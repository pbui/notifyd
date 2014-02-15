#!/usr/bin/env python2.7

import collections
import datetime
import json
import logging
import os
import subprocess
import time

import tornado.ioloop
import tornado.httpclient
import tornado.options
import tornado.web

#------------------------------------------------------------------------------
# Defaults 
#------------------------------------------------------------------------------

NOTIFYD_QUEUE_LENGTH = 100
NOTIFYD_PERIOD       = 5 * 1000
NOTIFYD_SLEEP        = 10
NOTIFYD_PORT         = 9412
NOTIFYD_SCRIPT       = 'scripts/notify.sh'

#------------------------------------------------------------------------------
# Notifyd Handler
#------------------------------------------------------------------------------

class NotifydHandler(tornado.web.RequestHandler):
    def initialize(self, daemon):
        self.daemon = daemon

    @tornado.web.asynchronous
    def get(self, timestamp):
        timestamp = float(timestamp)
        filtered  = [m for m in self.daemon.messages if m['timestamp'] >= timestamp]
        if not filtered:
            tornado.ioloop.IOLoop.instance().add_timeout(
                    datetime.timedelta(seconds=self.daemon.sleep),
                    lambda: self.get(timestamp))
        else:
            try:
                self.write(json.dumps({'messages': filtered}))
                self.daemon.logger.debug('sent json: {}'.format(filtered))
            except TypeError as e:
                self.daemon.logger.error('could not write json: {}'.format(e))
            self.finish()

    @tornado.web.asynchronous
    def post(self, timestamp=None):
        try:
            messages  = json.loads(self.request.body)['messages']
            metadata  = {'timestamp': time.time(), 'notified': False}

            for message in messages:
                message.update(metadata)

            self.daemon.messages.extend(messages)
        except (ValueError, KeyError) as e:
            self.daemon.logger.error('could not read json: {}\n{}'.format(self.request.body, e))

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
        self.notifier = tornado.ioloop.PeriodicCallback(self.notify, self.period)

        for peer in self.peers:
            self.pull(peer)

        self.add_handlers('', [
            (r'.*/',        NotifydHandler, {'daemon': self}),
            (r'.*/(\d+)' ,  NotifydHandler, {'daemon': self}),
        ])

    def notify(self):
        if not os.path.exists(self.script):
            return

        groups    = collections.defaultdict(list)
        filtered  = (m for m in self.messages if not m['notified'])
        for message in filtered:
            groups[(message['type'], message['sender'])].append(message['body'])
            message['notified'] = True

        for (type, sender), bodies in groups.items():
            command = '{} "{}" "{}" "{}"'.format(self.script, type, sender, '; '.join(bodies))
            subprocess.call(command, shell=True)

    def pull(self, peer):
        http_client = tornado.httpclient.AsyncHTTPClient()
        http_client.fetch('{}/{:}'.format(peer, int(time.time())), lambda response: self.pull_finish(peer, response))

    def pull_finish(self, peer, response):
        try:
            messages = json.loads(response.body)['messages']
            for message in messages:
                message['notified'] = False

            self.messages.extend(messages)
            self.logger.debug('read json: {}'.format(response.body))
        except (TypeError, ValueError, KeyError) as e:
            self.logger.debug('could not read json: {}\n{}'.format(response.body, e))

        self.ioloop.add_timeout(datetime.timedelta(seconds=self.sleep), lambda: self.pull(peer))

    def run(self):
        self.listen(self.port)
        self.notifier.start()
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
