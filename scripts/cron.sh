#!/bin/sh

if ! ps ux | grep python2.7 | grep notifyd > /dev/null 2>&1; then
    nice $HOME/src/personal/notifyd/notifyd.py --port=9411 --logging=debug --log_file_prefix=$HOME/.config/notifyd/log &
fi
