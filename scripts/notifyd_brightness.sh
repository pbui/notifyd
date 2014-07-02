#!/bin/sh

case "$1" in 
    up)
    xbacklight -inc 2%
    ;;
    down)
    xbacklight -dec 2%
    ;;
esac

notifyd_send BRIGHTNESS $(xbacklight -get)%
