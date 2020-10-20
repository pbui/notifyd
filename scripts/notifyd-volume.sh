#!/bin/bash

usage="usage: $0  [-c set|up|down|mute] [-i increment] [-m mixer]"

card=0
operation=
increment=
mixer=

while getopts "c:i:m:h" o
do case "$o" in
    c) operation=$OPTARG;;
    i) increment=$OPTARG;;
    m) mixer=$OPTARG;;
    h) echo "$usage"; exit 0;;
    ?) echo "$usage"; exit 0;;
esac
done

if aplay -l | grep -q 'Dock'; then
    card=2
    mixer='Headphone'
fi

if amixer -c $card | grep -q 'EB34'; then	# TODO: generalize this
    mixer="EB34 - A2DP"
elif amixer -c $card | grep -q 'Soundcore'; then
    mixer="Soundcore Life Q20 - A2DP"
fi

if [[ -z $operation ]] || [[ -z $increment ]] || [[ -z $mixer ]]
then
     echo $usage
     exit 1
fi

display_volume=0
case $operation in
up)
    display_volume=$(amixer -c $card set "$mixer" $increment+ unmute | grep -m 1 "%]" | cut -d "[" -f2|cut -d "%" -f1)%
    ;;

down)
    display_volume=$(amixer -c $card set "$mixer" $increment- unmute | grep -m 1 "%]" | cut -d "[" -f2|cut -d "%" -f1)%
    ;;
set)
    display_volume=$(amixer -c $card set "$mixer" $increment unmute | grep -m 1 "%]" | cut -d "[" -f2|cut -d "%" -f1)%
    ;;
mute)
    if amixer -c $card get "$mixer" | grep "\[on\]" > /dev/null 2>&1; then
        display_volume="Muted"
        amixer -c $card set "$mixer" mute > /dev/null 2>&1
    else
        display_volume=$(amixer -c $card set "$mixer" unmute | grep -m 1 "%]" | cut -d "[" -f2|cut -d "%" -f1)%
    fi
esac

notifyd-send "VOLUME" "${display_volume}"
