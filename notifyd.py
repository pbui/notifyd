#!/usr/bin/env python3

import collections
import datetime
import json
import logging
import os
import signal
import socket
import subprocess
import sys
import time

import tornado.ioloop
import tornado.httpclient
import tornado.gen
import tornado.options
import tornado.web

# Defaults

NOTIFYD_QUEUE_LENGTH    = 100       # Hundred messages
NOTIFYD_PERIOD          = 1         # One second
NOTIFYD_PORT            = 9411
NOTIFYD_ADDRESS         = 'localhost'
NOTIFYD_CONFIG_DIR      = os.path.expanduser('~/.config/notifyd')
NOTIFYD_REQUEST_TIMEOUT = 10 * 60   # Ten Minutes

# Messages Handler

class MessagesHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self, identifier):
        timeout  = time.time() + NOTIFYD_REQUEST_TIMEOUT
        filtered = []

        while not filtered and time.time() < timeout:
            filtered = [m for m in self.application.messages if identifier not in m['delivered']]
            yield tornado.gen.sleep(1.0)

        try:
            self.write(json.dumps({'messages': filtered}))
            for message in filtered:
                message['delivered'].append(identifier)
            self.application.logger.debug('Sent json: {}'.format(filtered))
        except (RuntimeError, TypeError) as e:
            self.application.logger.error('Could not write json: {}'.format(e))

    @tornado.gen.coroutine
    def post(self):
        try:
            data     = self.request.body.decode('UTF-8')
            messages = json.loads(data)['messages']
            metadata = {'notified': False, 'delivered': []}

            for message in messages:
                message.update(metadata)

            self.application.add_messages(messages)
        except (AttributeError, ValueError, KeyError) as e:
            self.application.logger.error('could not read json: {}\n'.format(e))

# StaticFileHandler

class StaticFileHandler(tornado.web.StaticFileHandler):
    def set_extra_headers(self, path):
        # Disable cache
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')

# Notify Daemon

class NotifyDaemon(tornado.web.Application):

    def __init__(self, **settings):
        tornado.web.Application.__init__(self, **settings)

        self.messages   = collections.deque(maxlen=NOTIFYD_QUEUE_LENGTH)
        self.logger     = logging.getLogger()
        self.period     = settings.get('period', NOTIFYD_PERIOD)
        self.port       = settings.get('port') or NOTIFYD_PORT
        self.address    = settings.get('address') or NOTIFYD_ADDRESS
        self.peers      = settings.get('peers', [])
        self.config_dir = settings.get('config_dir') or NOTIFYD_CONFIG_DIR
        self.script     = os.path.join(self.config_dir, 'scripts', 'notify.sh')
        self.files_dir  = os.path.join(self.config_dir, 'files')
        self.ioloop     = tornado.ioloop.IOLoop.instance()
        self.identifier = '{}:{}'.format(os.uname()[1], self.port)
        self.notify_scheduled = False

        if not os.path.exists(self.files_dir):
            os.makedirs(self.files_dir)

        self.add_handlers(r'.*', [
            (r'/files/(.*)'       , StaticFileHandler, {'path': self.files_dir}),
            (r'/messages'         , MessagesHandler),
            (r'/messages/([\w:]+)', MessagesHandler),
        ])

    def notify(self):
        self.notify_scheduled = False

        if not os.path.exists(self.script):
            self.logger.warning('Unable to find notification script: {}'.format(self.script))
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

            sender = sender.encode('utf-8')
            for body in bodies:
                body = body.encode('utf-8')
                subprocess.run([self.script, type, sender, body], close_fds=True)

    def add_messages(self, messages):
        self.messages.extend(messages)

        formatted_messages = []
        for message in messages:
            message['type'] = message['type'].upper()

            type   = message['type']
            sender = message['sender']
            body   = message['body']
            if not body:
                formatted_messages.append('[{:^12}] {:>16}'.format(type, sender))
            else:
                formatted_messages.append('[{:^12}] {:>16} | {}'.format(type, sender, body))

        self.logger.info('Added {} message(s)...\n{}'.format(len(messages), '\n'.join(formatted_messages)))

        if not self.notify_scheduled:
            self.ioloop.add_timeout(datetime.timedelta(seconds=self.period), self.notify)
            self.notify_scheduled = True

    @tornado.gen.coroutine
    def pull(self, peer):
        while True:
            http_client = tornado.httpclient.AsyncHTTPClient()
            request     = tornado.httpclient.HTTPRequest(
                url             = '{}/messages/{}'.format(peer, self.identifier),
                request_timeout = NOTIFYD_REQUEST_TIMEOUT)

            try:
                self.logger.debug('Starting pull...')
                response = yield http_client.fetch(request)
                data     = response.body.decode('UTF-8')
                messages = json.loads(data)['messages']

                for message in messages:
                    message['notified'] = False
                self.add_messages(messages)
            except Exception as e:
                self.logger.warning('Could fetch from peer {}: {}'.format(peer, e))
                yield tornado.gen.sleep(1.0)
            except (AttributeError, TypeError, ValueError, KeyError) as e:
                if response.body:
                    self.logger.error('Could not read json: {}\n{}'.format(response.body, e))
                yield tornado.gen.sleep(1.0)

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

# Main Execution

if __name__ == '__main__':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8', buffering=True)
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf8', buffering=True)

    tornado.options.define('debug', default=False, help='Enable debugging mode.')
    tornado.options.define('address', default=NOTIFYD_ADDRESS, help='Address to listen on.')
    tornado.options.define('port', default=NOTIFYD_PORT, help='Port to listen on.')
    tornado.options.define('peers', default=None, multiple=True, help='List of peers to pull message from.')
    tornado.options.define('config_dir', default=None, help='Configuration directory.')
    tornado.options.parse_command_line()

    options = tornado.options.options.as_dict()
    notifyd = NotifyDaemon(**options)
    notifyd.run()

# vim: sts=4 sw=4 ts=8 expandtab ft=python
