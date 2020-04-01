#!/bin/bash

get_volume() {
    pacmd list-sinks |
	awk '/^\s+name: /{indefault = $2 == "<'$SINK_NAME'>"}
	    /^\s+volume: / && indefault {print $5; exit}'
}

SINK_NAME=$(pacmd info | awk '/Default sink/ {print $4}')

case "$1" in
    up)	    pactl set-sink-volume $SINK_NAME +3%;;
    down)   pactl set-sink-volume $SINK_NAME -3%;;
    mute)   
	if pactl list sinks | grep -q 'Mute: yes'; then
	    pactl set-sink-mute $SINK_NAME 0
	else
	    pactl set-sink-mute $SINK_NAME 1
	    display_volume='Muted'
	fi
esac

if [ -z "$display_volume" ]; then
    display_volume=$(get_volume)
fi

notifyd-send "VOLUME" "$display_volume"
