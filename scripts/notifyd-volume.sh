#!/bin/sh

usage="usage: $0  [-c up|down|mute] [-i increment] [-m mixer]"

command=
increment=
mixer=

while getopts "c:i:m:h" o
do case "$o" in
    c) command=$OPTARG;;
    i) increment=$OPTARG;;
    m) mixer=$OPTARG;;
    h) echo "$usage"; exit 0;;
    ?) echo "$usage"; exit 0;;
esac
done

if [[ -z $command ]] || [[ -z $increment ]] || [[ -z $mixer ]]
then
     echo $usage
     exit 1
fi

display_volume=0
if [ "$command" = "up" ]; then
    display_volume=$(amixer set $mixer $increment+ unmute | grep -m 1 "%]" | cut -d "[" -f2|cut -d "%" -f1)%
fi

if [ "$command" = "down" ]; then
    display_volume=$(amixer set $mixer $increment- unmute | grep -m 1 "%]" | cut -d "[" -f2|cut -d "%" -f1)%
fi

if [ "$command" = "mute" ]; then
    if amixer get Master | grep "\[on\]" > /dev/null 2>&1; then
        display_volume="Muted"
        amixer set $mixer mute > /dev/null 2>&1
    else
        display_volume=$(amixer set $mixer unmute | grep -m 1 "%]" | cut -d "[" -f2|cut -d "%" -f1)%
    fi
fi

notifyd-send "VOLUME" "${display_volume}"
