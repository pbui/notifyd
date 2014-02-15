#!/usr/bin/env python2.7

import collections
import datetime
import json
import logging
import os
import subprocess

import tornado.ioloop
import tornado.httpclient
import tornado.options
import tornado.web

#------------------------------------------------------------------------------
# Defaults 
#------------------------------------------------------------------------------

NOTIFYD_QUEUE_LENGTH = 100
NOTIFYD_TIMEOUT      = 10
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
        filtered = (m for m in self.daemon.messages if m.timestamp >= timestamp)
        if not filtered:
            tornado.ioloop.IOLoop.instance().add_timeout(
                    datetime.timedelta(seconds=self.daemon.timeout),
                    lambda: self.get(timestamp))
        else:
            try:
                self.write(json.dumps({'messages': filtered}))
            except TypeError as e:
                self.daemon.logger.error('could not write json: {}'.format(e))
            self.finish()

    @tornado.web.asynchronous
    def post(self, timestamp=None):
        try:
            data = json.loads(self.request.body)
            self.daemon.messages.extend(data['messages'])
            self.daemon.notify(data['messages'])
        except (ValueError, KeyError) as e:
            self.daemon.logger.error('could not read json: {}\n{}'.format(self.request.body, e))

        self.finish()

#------------------------------------------------------------------------------
# Notify Daemon
#------------------------------------------------------------------------------

class NotifyDaemon(tornado.web.Application):

    def __init__(self, **settings):
        tornado.options.parse_command_line()
        tornado.web.Application.__init__(self, **settings)

        self.messages = collections.deque(maxlen=NOTIFYD_QUEUE_LENGTH)
        self.logger   = logging.getLogger()
        self.timeout  = settings.get('timeout', NOTIFYD_TIMEOUT)
        self.port     = settings.get('port', NOTIFYD_PORT)
        self.script   = settings.get('script', NOTIFYD_SCRIPT)
        self.peers    = settings.get('peers', [])
        self.ioloop   = tornado.ioloop.IOLoop.instance()

        for peer in self.peers:
            self.pull(peer)

        self.add_handlers('', [
            (r'.*/',        NotifydHandler, {'daemon': self}),
            (r'.*/(\d+)' ,  NotifydHandler, {'daemon': self}),
        ])

        self.listen(self.port)

    def notify(self, messages):
        if not os.path.exists(self.script):
            return

        groups = collections.defaultdict(list)
        for message in messages:
            groups[(message['type'], message['sender'])].append(message['body'])

        for (type, sender), bodies in groups.items():
            command = '{} "{}" "{}" "{}"'.format(self.script, type, sender, '; '.join(bodies))
            subprocess.call(command, shell=True)

    def pull(self, peer):
        http_client = tornado.httpclient.AsyncHTTPClient()
        http_client.fetch('{}/{:d}'.format(peer, time.time()), lambda response: self.pull_finish(peer, response))

    def pull_finish(self, peer, response):
        try:
            self.messages.extend(json.loads(response.body)['messages'])
        except (ValueError, KeyError) as e:
            self.logger.error('could not read json: {}\n{}'.format(response.body, e))

        self.ioloop.add_timeout(datetime.timedelta(seconds=self.timeout), lambda: self.pull(peer))

    def run(self):
        self.ioloop.start()

#------------------------------------------------------------------------------
# Main Execution
#------------------------------------------------------------------------------

if __name__ == '__main__':
    notifyd = NotifyDaemon(debug=True)
    notifyd.run()

# vim: sts=4 sw=4 ts=8 expandtab ft=python
