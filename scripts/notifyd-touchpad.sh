#!/bin/sh

disable() {
    xinput disable $ID
    notifyd-send TOUCHPAD Disabled
}

enable() {
    xinput enable $ID
    xinput set-prop $ID "libinput Scroll Method Enabled" 0, 1, 0
    notifyd-send TOUCHPAD Enabled
}

toggle() {
    if [ $(xinput list-props $ID | grep 'Device Enabled' | awk '{print $4}') -eq 1 ]; then
	disable
    else
	enable
    fi
}

ID=$(xinput | grep TouchPad | cut -d = -f 2 | awk '{print $1}')

case $1 in
enable)	    enable;;
disable)    disable;;
*)	    toggle;;
esac
