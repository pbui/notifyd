#!/usr/bin/env python2.7

import collections
import datetime
import json
import logging
import os
import signal
import socket
import sys
import time

import tornado.ioloop
import tornado.httpclient
import tornado.gen
import tornado.options
import tornado.web

# Defaults ---------------------------------------------------------------------

NOTIFYD_QUEUE_LENGTH    = 100       # Hundred messages
NOTIFYD_PERIOD          = 1         # One second
NOTIFYD_SLEEP           = 5         # Five seconds
NOTIFYD_PORT            = 9411
NOTIFYD_ADDRESS         = 'localhost'
NOTIFYD_SCRIPT          = os.path.expanduser('~/.config/notifyd/scripts/notify.sh')
NOTIFYD_FILES_PATH      = os.path.expanduser('~/.config/notifyd/files')
NOTIFYD_REQUEST_TIMEOUT = 10 * 60   # Ten Minutes

# Messages Handler -------------------------------------------------------------

class MessagesHandler(tornado.web.RequestHandler):
    finished = False

    @tornado.web.asynchronous
    def get(self, identifier, timeout=None):
        if self.finished:
            return

        timeout  = timeout or (time.time() + NOTIFYD_REQUEST_TIMEOUT)
        filtered = [m for m in self.application.messages if identifier not in m['delivered']]

        if filtered or time.time() >= timeout:
            try:
                self.write(json.dumps({u'messages': filtered}))
                for message in filtered:
                    message['delivered'].append(identifier)
                self.application.logger.debug('sent json: {}'.format(filtered))
            except (RuntimeError, TypeError) as e:
                self.application.logger.error('could not write json: {}'.format(e))
            self.finish()
        else:
            self.application.logger.debug('GET timeout...')
            tornado.ioloop.IOLoop.instance().add_timeout(
                datetime.timedelta(seconds=self.application.sleep),
                lambda: self.get(identifier, timeout))

    def on_connection_close(self):
        self.finished = True
        self.application.logger.debug('Connection closed')
        self.finish()

    @tornado.web.asynchronous
    def post(self, timeout=None):
        try:
            data     = self.request.body.decode('UTF-8')
            messages = json.loads(data)['messages']
            metadata = {u'notified': False, u'delivered': []}

            for message in messages:
                message.update(metadata)

            self.application.add_messages(messages)
        except (AttributeError, ValueError, KeyError) as e:
            self.application.logger.error('could not read json: {}\n'.format(e))

        self.finish()

# StaticFileHandler ------------------------------------------------------------

class StaticFileHandler(tornado.web.StaticFileHandler):
    def set_extra_headers(self, path):
        # Disable cache
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')

# Notify Daemon ----------------------------------------------------------------

class NotifyDaemon(tornado.web.Application):

    def __init__(self, **settings):
        tornado.web.Application.__init__(self, **settings)

        self.messages   = collections.deque(maxlen=NOTIFYD_QUEUE_LENGTH)
        self.logger     = logging.getLogger()
        self.sleep      = settings.get('sleep', NOTIFYD_SLEEP)
        self.period     = settings.get('period', NOTIFYD_PERIOD)
        self.port       = settings.get('port', NOTIFYD_PORT)
        self.address    = settings.get('address', NOTIFYD_ADDRESS)
        self.script     = settings.get('script', NOTIFYD_SCRIPT)
        self.peers      = settings.get('peers', [])
        self.files_path = settings.get('files_path', NOTIFYD_FILES_PATH)
        self.ioloop     = tornado.ioloop.IOLoop.instance()
        self.identifier = '{}:{}'.format(os.uname()[1], self.port)
        self.notify_scheduled = False

        if not os.path.exists(self.files_path):
            os.makedirs(self.files_path)

        self.add_handlers(r'.*', [
            (r'/files/(.*)'       , StaticFileHandler, {'path': self.files_path}),
            (r'/messages'         , MessagesHandler),
            (r'/messages/([\w:]+)', MessagesHandler),
        ])

    def _execute_daemon(self, argv):
        try:
            pid = os.fork()         # Fork 1
            if pid > 0:             # Parent returns
                return
        except OSError as e:
            self.logger.error('Unable to fork: {}'.format(e))
            return

        os.setsid()                 # New session group

        try:
            pid = os.fork()         # Fork 2
            if pid > 0:             # Parent exits
                sys.exit(0)
        except OSError as e:
            self.logger.error('Unable to fork: {}'.format(e))
            sys.exit(1)

        os.execvp(argv[0], argv)    # Child execs
        sys.exit(1)

    def notify(self):
        self.notify_scheduled = False

        if not os.path.exists(self.script):
            return

        groups    = collections.defaultdict(list)
        filtered  = (m for m in self.messages if not m['notified'])
        for message in filtered:
            groups[(message['type'], message['sender'])].append(message['body'])
            message['notified'] = True

        for (type, sender), bodies in groups.items():
            if type in ('CHAT', 'MAIL'):
                bodies = ['; '.join(bodies)]
            elif type in ('VOLUME'):
                bodies = [bodies[-1]]

            sender = sender.encode('UTF-8')

            for body in bodies:
                body = body.encode('UTF-8')
                self._execute_daemon([self.script, type, sender, body])

    def add_messages(self, messages):
        self.messages.extend(messages)

        formatted_messages = []
        for message in messages:
            message['type'] = message['type'].upper()

            type   = message['type']
            sender = message['sender']
            body   = message['body']
            if not body:
                formatted_messages.append(u'[{:^12}] {:>12}'.format(type, sender))
            else:
                formatted_messages.append(u'[{:^12}] {:>12} | {}'.format(type, sender, body))

        self.logger.info(u'Added {} message(s)...\n{}'.format(len(messages), '\n'.join(formatted_messages)))

        if not self.notify_scheduled:
            self.ioloop.add_timeout(datetime.timedelta(seconds=self.period), self.notify)
            self.notify_scheduled = True

    @tornado.gen.engine
    def pull(self, peer):
        self.logger.debug('Starting pull...')
        http_client = tornado.httpclient.AsyncHTTPClient()
        request     = tornado.httpclient.HTTPRequest(
            url             = '{}/messages/{}'.format(peer, self.identifier),
            request_timeout = NOTIFYD_REQUEST_TIMEOUT)
        response    = yield tornado.gen.Task(http_client.fetch, request)

        self.logger.debug('Finishing pull...')

        try:
            data     = response.body.decode('UTF-8')
            messages = json.loads(data)['messages']
            for message in messages:
                message['notified'] = False

            self.add_messages(messages)
        except (AttributeError, TypeError, ValueError, KeyError) as e:
            if response.body is not None:
                self.logger.error('could not read json: {}\n{}'.format(response.body, e))

        self.ioloop.add_timeout(datetime.timedelta(seconds=self.sleep), lambda: self.pull(peer))

    def run(self):
        try:
            self.listen(self.port, self.address)
        except socket.error:
            sys.exit(1)

        signal.signal(signal.SIGCHLD, signal.SIG_IGN)

        for peer in self.peers:
            self.logger.debug('Pulling from {}'.format(peer))
            self.pull(peer)

        self.ioloop.start()

# Main Execution ---------------------------------------------------------------

if __name__ == '__main__':
    tornado.options.define('debug', default=False, help='Enable debugging mode.')
    tornado.options.define('port', default=NOTIFYD_PORT, help='Port to listen on.')
    tornado.options.define('peers', default=None, multiple=True, help='List of peers to pull message from.')
    tornado.options.define('files_path', default=NOTIFYD_FILES_PATH, help='Path to files directory.')
    tornado.options.parse_command_line()

    options = tornado.options.options.as_dict()
    notifyd = NotifyDaemon(**options)
    notifyd.run()

# vim: sts=4 sw=4 ts=8 expandtab ft=python
