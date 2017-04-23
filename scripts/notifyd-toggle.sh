#!/bin/sh

DZEN2_SCRIPT=${HOME}/.config/notifyd/scripts/dzen2.sh

if [ -x ${DZEN2_SCRIPT} ]; then
    notifyd-send "NOTFIFYD" "Disable notifications" && sleep 2
    chmod -x ${DZEN2_SCRIPT}
else
    chmod +x ${DZEN2_SCRIPT}
    notifyd-send "NOTFIFYD" "Enable notifications"
fi
