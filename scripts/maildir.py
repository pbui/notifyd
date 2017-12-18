#!/usr/bin/env python3

import email
import json
import os
import subprocess
import sys
import time
import requests
import re

#------------------------------------------------------------------------------
# Configuration
#------------------------------------------------------------------------------

TIMEOUT          = 5 * 60
SENDER_BLACKLIST = []
LISTID_BLACKLIST = [
    'arch-.*',
    'aur-.*',
    '.*\.netbsd\.org',
    'python-.*',
    '.*\.openbsd\.org',
    '.*\.centos\.org',
]
MAILDIRS        = ('cur', 'new', 'tmp')

#------------------------------------------------------------------------------
# Walk maildir and notify of new messages
#------------------------------------------------------------------------------

def filter_message(path):
    if ('Spam' in path or
        'Sent' in path or
        'Trash' in path or
        'new' not in path):
        return None, None

    if time.time() - os.path.getmtime(path) >= TIMEOUT:
        return None, None

    message = email.message_from_file(open(path, 'r'))
    sender  = message['From'].split('<')[0]\
                .replace('&','&amp;')\
                .replace('"','')
    subject = message['Subject'].replace('&', '&amp;')\
                .replace('$', '')\
                .replace('!', '')

    for s in SENDER_BLACKLIST:
        if s in sender:
            return None, None

    if 'list-id' in message:
        list_id = message['list-id'].lower()
        for rx in LISTID_BLACKLIST:
            if re.search(rx, list_id, re.IGNORECASE):
                return None, None

    return sender, subject

def notify_maildir(maildir):
    messages = []

    for root, dirs, files in os.walk(maildir):
        if os.path.basename(root) in ('cur', 'tmp'):
            continue

        if len(dirs) > 3:
            for maildir in MAILDIRS:
                try:
                    os.rmdir(os.path.join(root, maildir))
                except OSError:
                    pass

        for file in files:
            sender, subject = filter_message(os.path.join(root, file))
            if sender and subject:
                messages.append({
                    'type'      : 'MAIL',
                    'sender'    : sender.strip(),
                    'body'      : subject.strip(),
                })

    if messages:
        requests.post('http://localhost:9411/messages', data=json.dumps({'messages': messages}))

#------------------------------------------------------------------------------
# Main execution
#------------------------------------------------------------------------------

if __name__ == '__main__':
    try:
        for maildir in sys.argv[1:]:
            notify_maildir(maildir)
    except KeyboardInterrupt:
        sys.exit(0)

# vim: sts=4 sw=4 ts=8 expandtab ft=python
