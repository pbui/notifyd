#!/bin/sh

if [ "$(synclient | grep TouchpadOff | awk '{print $3}')" == "0" ]; then
    synclient TouchpadOff=1
    notifyd_send TOUCHPAD off
else
    synclient TouchpadOff=0
    notifyd_send TOUCHPAD on
fi
