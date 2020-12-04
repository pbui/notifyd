#!/bin/bash

get_volume() {
    pactl list sinks |
    	awk -v SINK_NAME=$SINK_NAME '
	    /Name:/		    { is_default = $2 == SINK_NAME }
	    /Volume:/ && is_default { print $5; exit }
    	'
}

get_muted() {
    pactl list sinks |
    	awk -v SINK_NAME=$SINK_NAME '
	    /Name:/		  { is_default = $2 == SINK_NAME }
	    /Mute:/ && is_default { print $2; exit }
    	'
}

SINK_NAME=$(pactl info | awk '/Default Sink/ {print $3}')

case "$1" in
    up)	    pactl set-sink-volume $SINK_NAME +3%;;
    down)   pactl set-sink-volume $SINK_NAME -3%;;
    mute)
	if [ "$(get_muted)" = 'yes' ]; then
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
