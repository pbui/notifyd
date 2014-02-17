#!/usr/bin/env python2.7

import collections
import datetime
import json
import logging
import os
import socket
import subprocess
import sys
import time

import tornado.ioloop
import tornado.httpclient
import tornado.gen
import tornado.options
import tornado.web

#------------------------------------------------------------------------------
# Defaults
#------------------------------------------------------------------------------

NOTIFYD_QUEUE_LENGTH    = 100       # Hundred messages
NOTIFYD_PERIOD          = 1         # One second
NOTIFYD_SLEEP           = 5         # Five seconds
NOTIFYD_PORT            = 9411
NOTIFYD_SCRIPT          = os.path.expanduser('~/.config/notifyd/scripts/notify.sh')
NOTIFYD_REQUEST_TIMEOUT = 10 * 60   # Ten Minutes

#------------------------------------------------------------------------------
# Notifyd Handler
#------------------------------------------------------------------------------

class NotifydHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self, timestamp):
        timestamp = float(timestamp)
        filtered  = [m for m in self.application.messages if m['timestamp'] >= timestamp]
        if filtered:
            try:
                self.write(json.dumps({'messages': filtered}))
                self.application.logger.info('sent json: {}'.format(filtered))
            except TypeError as e:
                self.application.logger.error('could not write json: {}'.format(e))
            self.finish()
        else:
            tornado.ioloop.IOLoop.instance().add_timeout(
                    datetime.timedelta(seconds=self.application.sleep),
                    lambda: self.get(timestamp))

    @tornado.web.asynchronous
    def post(self, timestamp=None):
        try:
            messages = json.loads(self.request.body)['messages']
            metadata = {'timestamp': time.time(), 'notified': False}

            for message in messages:
                message.update(metadata)

            self.application.add_messages(messages)
        except (ValueError, KeyError) as e:
            self.application.logger.error('could not read json: {}\n{}'.format(self.request.body, e))

        self.finish()

#------------------------------------------------------------------------------
# Notify Daemon
#------------------------------------------------------------------------------

class NotifyDaemon(tornado.web.Application):

    def __init__(self, **settings):
        tornado.web.Application.__init__(self, **settings)

        self.messages = collections.deque(maxlen=NOTIFYD_QUEUE_LENGTH)
        self.logger   = logging.getLogger()
        self.sleep    = settings.get('sleep', NOTIFYD_SLEEP)
        self.period   = settings.get('period', NOTIFYD_PERIOD)
        self.port     = settings.get('port', NOTIFYD_PORT)
        self.script   = settings.get('script', NOTIFYD_SCRIPT)
        self.peers    = settings.get('peers', [])
        self.ioloop   = tornado.ioloop.IOLoop.instance()
        self.notify_scheduled = False

        self.add_handlers('', [
            (r'.*/',        NotifydHandler),
            (r'.*/(\d+)' ,  NotifydHandler),
        ])

        self.peers_timestamp = {}
        for peer in self.peers:
            self.peers_timestamp[peer] = time.time()

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

            for body in bodies:
                command = u'{} "{}" "{}" "{}"'.format(self.script, type, sender, body)
                subprocess.call(command, shell=True)

    def add_messages(self, messages):
        self.messages.extend(messages)

        formatted_messages = []
        for message in messages:
            type   = message['type']
            sender = message['sender']
            body   = message['body']
            if not body:
                formatted_messages.append('[{:>8}] {:>16}'.format(type, sender))
            else:
                formatted_messages.append('[{:>8}] {:>16} | {}'.format(type, sender, body))

        self.logger.info('Added {} message(s)...\n{}'.format(len(messages), '\n'.join(formatted_messages)))

        if not self.notify_scheduled:
            self.ioloop.add_timeout(datetime.timedelta(seconds=self.period), self.notify)
            self.notify_scheduled = True

    @tornado.gen.engine
    def pull(self, peer):
        http_client = tornado.httpclient.AsyncHTTPClient()
        request     = tornado.httpclient.HTTPRequest(
            url             = '{}/{}'.format(peer, int(self.peers_timestamp[peer])),
            request_timeout = NOTIFYD_REQUEST_TIMEOUT)
        response    = yield tornado.gen.Task(http_client.fetch, request)

        self.peers_timestamp[peer] = time.time()

        try:
            messages = json.loads(response.body)['messages']
            for message in messages:
                message['notified'] = False

            self.add_messages(messages)
        except (TypeError, ValueError, KeyError) as e:
            self.logger.debug('could not read json: {}\n{}'.format(response.body, e))

        self.ioloop.add_timeout(datetime.timedelta(seconds=self.sleep), lambda: self.pull(peer))

    def run(self):
        try:
            self.listen(self.port)
        except socket.error:
            sys.exit(1)

        for peer in self.peers:
            self.logger.debug('Pulling from {}'.format(peer))
            self.pull(peer)

        self.ioloop.start()

#------------------------------------------------------------------------------
# Main Execution
#------------------------------------------------------------------------------

if __name__ == '__main__':
    tornado.options.define('debug', default=False, help='Debugging mode.')
    tornado.options.define('port', default=NOTIFYD_PORT, help='Port to listen on.')
    tornado.options.define('peers', default=None, multiple=True, help='List of peers to pull message from.')
    tornado.options.parse_command_line()
    options = tornado.options.options.as_dict()

    notifyd = NotifyDaemon(**options)
    notifyd.run()

# vim: sts=4 sw=4 ts=8 expandtab ft=python
