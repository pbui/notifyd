#!/bin/sh

set -e

TYPE=$1
SENDER=$2
shift 2
BODY=$*

case ${TYPE} in
    IMAGE|WWW)
        xdg-open "${BODY}"
    ;;
esac

# vim: sts=4 sw=4 ts=8 expandtab ft=sh
