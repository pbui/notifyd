#!/bin/sh

PREFIX=$(dirname $0)

if [ -x ${PREFIX}/dzen2.sh ]; then
    ${PREFIX}/dzen2.sh "$@"
fi

if [ -x ${PREFIX}/open.sh ]; then
    ${PREFIX}/open.sh "$@"
fi
