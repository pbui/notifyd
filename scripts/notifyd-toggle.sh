#!/bin/sh

DZEN2_SCRIPT=${HOME}/.config/notifyd/scripts/dzen2.sh

if [ -x ${DZEN2_SCRIPT} ]; then
    chmod -x ${DZEN2_SCRIPT}
else
    chmod +x ${DZEN2_SCRIPT}
fi
