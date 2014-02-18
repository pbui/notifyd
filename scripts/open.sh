#!/bin/sh

set -e

TYPE=$1
SENDER=$2
shift 2
BODY=$*

case ${TYPE} in
    IMAGE|WWW)
        exec xdg-open "${BODY}" > /dev/null 2>&1
    ;;
esac

exit 0

# vim: sts=4 sw=4 ts=8 expandtab ft=sh
