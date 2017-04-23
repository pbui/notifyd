#!/bin/sh

if [ $(synclient | grep TouchpadOff | awk '{print $3}') -eq 0 ]; then
    synclient TouchpadOff=1
    notifyd-send TOUCHPAD Off
else
    synclient TouchpadOff=0 VertEdgeScroll=1
    notifyd-send TOUCHPAD On
fi
