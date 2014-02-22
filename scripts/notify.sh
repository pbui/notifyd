#!/bin/sh

PREFIX=$(dirname $0)

if [ -x ${PREFIX}/dzen2.sh ]; then
    ${PREFIX}/dzen2.sh "$@"
fi

if [ -x ${PREFIX}/dispatch.sh ]; then
    ${PREFIX}/dispatch.sh "$@"
fi
