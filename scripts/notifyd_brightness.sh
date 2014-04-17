#!/bin/sh

case "$1" in 
    up)
    xbacklight -inc 3%
    ;;
    down)
    xbacklight -dec 3%
    ;;
esac

notifyd_send BRIGHTNESS $(xbacklight -get)%
