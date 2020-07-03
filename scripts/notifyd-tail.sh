#!/bin/sh

# notifyd-tail: tail notification log

_GRY='[0m'
_BLK='[0;30m'
_RED='[0;31m'
_GRN='[0;32m'
_YEL='[0;33m'
_BLU='[0;34m'
_CYN='[0;36m'
_WHI='[0;37m'

tail_log() {
    if [ -r $HOME/.config/notifyd/log/current ]; then
	tail -n 100 -F $HOME/.config/notifyd/log/current
    elif command -v journalctl > /dev/null 2>&1; then
	journalctl -n 10 --user --user-unit=notifyd -f
    else
	exit 1
    fi
}

format_log() {
    # 1. Strip Info and Warnings
    # 2. Highlight Parts of message
    sed -En \
	-e 's|^[-0-9_:\.]+\s+(\[[^IW].*)|\1|' \
	-e "s/^\[(\s*)([^ ]+)(\s*)\](\s+)([^|]+)/\[\1$_YEL\2$_GRY\3\]\4$_CYN\5$_GRY/p"
}

tail_log | format_log

# vim: set sts=4 sw=4 ts=8 ft=sh:
