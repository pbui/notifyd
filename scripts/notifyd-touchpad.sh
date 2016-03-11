#!/bin/sh

if [ "$(synclient | grep TouchpadOff | awk '{print $3}')" == "0" ]; then
    synclient TouchpadOff=1
    notifyd-send TOUCHPAD off
else
    synclient TouchpadOff=0
    notifyd-send TOUCHPAD on
fi
