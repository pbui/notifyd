#!/bin/sh

# notifyd-tail: tail notification log

TAIL=""
if [ -r $HOME/.config/notifyd/log/current ]; then
    tail -F $HOME/.config/notifyd/log/current | sed -En 's/.*\s+(\[[^IW].*)/\1/p'
elif command -v journalctl > /dev/null 2>&1; then
    journalctl -n 10 --user --user-unit=notifyd -f | sed -En 's/.*:\s+(\[[^IW].*)/\1/p' 
else
    echo "Unable to locate notification log"
    exit 1
fi

