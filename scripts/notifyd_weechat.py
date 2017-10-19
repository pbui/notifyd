# Copyright (C) 2014 Peter Bui <pnutzh4x0r@gmail.com>

import weechat, os, string, sys, logging, json, requests


weechat.register("notifyd", "pbui", "0.0.1", "ISC", "notifyd - A notifyd script for weechat", "", "")

# Set up here, go no further!
settings = {
    "show_highlight"    : "on",
    "show_priv_msg"     : "on",
    "show_channels"     : "",
    "ignore_nicks"      : "",
}

# Init everything
for option, default_value in settings.items():
    if weechat.config_get_plugin(option) == "":
        weechat.config_set_plugin(option, default_value)

# Hook privmsg/hilights
weechat.hook_print("", "irc_privmsg", "", 1, "get_notified", "")

# Functions

def write_notifyd_message(sender, message):
    message = message.replace('\n', ' ')
    sender  = sender.strip()
    if sender == '*':
        mlist   = message.split()
        sender  = mlist[0]
        message = ' '.join(mlist[1:])
    requests.post('http://localhost:9411/messages', data=json.dumps({
        'messages': [
            {
                'type'  : 'CHAT',
                'sender': sender,
                'body'  : message,
            }
        ],
    }))

def get_notified(data, bufferp, uber_empty, tagsn, isdisplayed, ishilight, prefix, message):
    buffer = weechat.buffer_get_string(bufferp, "short_name") or \
             weechat.buffer_get_string(bufferp, "name")

    prefix = prefix.replace('@', '')\
                   .replace('+', '')

    if weechat.buffer_get_string(bufferp, "localvar_type") == "private" and \
       weechat.config_get_plugin('show_priv_msg') == "on":
        if buffer == prefix:
            write_notifyd_message(prefix, message)
    elif ishilight == "1" and weechat.config_get_plugin('show_highlight') == "on":
        write_notifyd_message(prefix, message)
    elif buffer in weechat.config_get_plugin('show_channels').split(',') and \
        prefix not in weechat.config_get_plugin('ignore_nicks').split(','):
        write_notifyd_message(prefix, message)
    return weechat.WEECHAT_RC_OK

# vim: expandtab ft=python
