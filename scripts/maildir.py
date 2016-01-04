#!/usr/bin/env python2.7

import email
import json
import os
import subprocess
import sys
import time
import requests

#------------------------------------------------------------------------------
# Configuration
#------------------------------------------------------------------------------

TIMEOUT          = 5 * 60
SENDER_BLACKLIST = []
LISTID_BLACKLIST = [
    'arch-announce',
    'arch-general',
    'arch-dev-public',
    'aur-dev',
    'aur-general',
    'current-users.netbsd.org',
    'netbsd-advocacy.netbsd.org',
    'netbsd-users.netbsd.org',
    'pkgsrc-users.netbsd.org',
    'port-amd64.netbsd.org',
    'port-i386.netbsd.org',
    'port-xen.netbsd.org',
    'source-changes-digest.netbsd.org',
    'tech-kern.netbsd.org',
    'tech-misc.netbsd.org',
    'tech-multimedia.netbsd.org',
    'tech-net.netbsd.org',
    'tech-pkg.netbsd.org',
    'tech-toolchain.netbsd.org',
    'tech-userlevel.netbsd.org',
    'tech-x11.netbsd.org',
    'python-announce',
    'python-dev',
    'python-list',
    'conferences.python.org',
    'advocacy.openbsd.org',
    'misc.openbsd.org',
    'ports.openbsd.org',
    'ports-changes.openbsd.org',
    'source-changes.openbsd.org',
    'tech.openbsd.org',
    'centos-announce.centos.org',
    'centos.centos.org',
]

#------------------------------------------------------------------------------
# Walk maildir and notify of new messages
#------------------------------------------------------------------------------

def filter_message(path):
    if ('Spam' in path or
        'Sent' in path or
        'Trash' in path or
        'new' not in path):
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
        for l in LISTID_BLACKLIST:
            if l in list_id:
                return None, None

    if time.time() - os.path.getmtime(path) >= TIMEOUT:
        return None, None

    return sender, subject

def notify_maildir(maildir):
    messages = []

    for root, dirs, files in os.walk(maildir):
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
