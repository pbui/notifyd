#!/bin/sh

current_volume() {
    mixerctl outputs.master | cut -d = -f 2 | cut -d , -f 1
}

current_mute() {
    mixerctl outputs.master.mute | cut -d = -f 2
}

if [ "$(current_mute)" = "on" ]; then
    notifyd_send VOLUME MUTED
else
    notifyd_send VOLUME $((($(current_volume) + 1) * 100 / 255))%
fi
