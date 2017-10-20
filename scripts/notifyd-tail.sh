#!/bin/sh

# notifyd-tail: tail notification log

TAIL=""
if [ -r $HOME/.config/notifyd/log/current ]; then
    TAIL="tail -F $HOME/.config/notifyd/log/current"
fi

if command journalctl 2> /dev/null; then
    TAIL="journalctl --user --user-unit=notifyd -f"
fi

$TAIL | sed -En 's/.*: (\[[^IW].*)/\1/p' 
