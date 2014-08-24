#!/bin/sh

if ! pgrep -f notifyd > /dev/null 2>&1; then
    nice $HOME/src/personal/notifyd/notifyd.py --port=9411 --log_file_prefix=$HOME/.config/notifyd/log &
fi
