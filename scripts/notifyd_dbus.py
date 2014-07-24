#!/usr/bin/env python3

import collections
import itertools
import json
import logging
import requests

import dbus
import dbus.mainloop.glib
import dbus.service

try:
    import gobject
except ImportError:
    from gi.repository import GObject as gobject

import lxml.html

# Default configuration --------------------------------------------------------

DEFAULT_EXPIRE_TIMEOUT  = 5
DEFAULT_APP_ICON        = 'notifyd'
DEFAULT_LOGGER          = 'notifyd'

# Renaming ---------------------------------------------------------------------

ICON_TABLE = {
    'drive-removable-media': 'udiskie',
}

# DBUS configuration -----------------------------------------------------------

DBUS_SERVICE = 'org.freedesktop.Notifications'
DBUS_PATH    = '/org/freedesktop/Notifications'

# Strip HTML function ----------------------------------------------------------

def strip_html(s):
    # http://stackoverflow.com/questions/753052/strip-html-from-strings-in-python
    return lxml.html.fromstring(s).text_content()

# Notification service class ---------------------------------------------------

class NotificationService(dbus.service.Object):

    def __init__(self):

        dbus.service.Object.__init__(self, dbus.service.BusName(DBUS_SERVICE, bus=dbus.SessionBus()), DBUS_PATH)

        self.logger          = logging.getLogger(DEFAULT_LOGGER)
        self.counter         = itertools.count(0)
        self.notifications   = collections.deque()
        self.timeout         = None

    @dbus.service.method(dbus_interface=DBUS_SERVICE, in_signature='', out_signature='ssss')
    def GetServerInformation(self):
        self.logger.debug('GetServerInformation')
        return ('notifyd', 'pnutzh4x0r', '0.0.1', '1.0')

    @dbus.service.method(dbus_interface=DBUS_SERVICE, in_signature='susssasa{sv}i', out_signature='u')
    def Notify(self, app_name, replaces_id, app_icon, summary, body, actions, hints, expire_timeout):
        self.logger.debug('Notify')
        app_icon = app_icon or 'NOTIFYD'
        requests.post('http://127.0.0.1:9412/messages', data=json.dumps({
            'messages': [
                {
                    'type'  : ICON_TABLE.get(app_icon, app_icon),
                    'sender': summary.strip(),
                    'body'  : strip_html(body.strip()),
                }
            ],
        }))
        return next(self.counter)


def notifyd_dbus():
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    NotificationService()
    gobject.MainLoop().run()

# Main execution ---------------------------------------------------------------

if __name__ == '__main__':
    notifyd_dbus()

# vim: set sts=4 sw=4 ts=8 expandtab ft=python:
