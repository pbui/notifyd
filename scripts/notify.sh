#!/bin/sh

PREFIX=$(dirname $0)

if [ -x ${PREFIX}/dzen2.sh ]; then
    ${PREFIX}/dzen2.sh "$@"
elif [ -x ${PREFIX}/notify-send.sh ]; then
    ${PREFIX}/notify-send.sh "$@"
fi

if [ -x ${PREFIX}/dispatch.sh ]; then
    ${PREFIX}/dispatch.sh "$@"
fi
