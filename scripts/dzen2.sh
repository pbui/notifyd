#!/bin/sh

set -e
set -f

#------------------------------------------------------------------------------
# Constant Defaults
#------------------------------------------------------------------------------

DZEN2_BACKGROUND='#2e3440'
DZEN2_FOREGROUND='#eceff4'
DZEN2_HIGHLIGHT='#88c0d0'
DZEN2_FONTNAME='Source Code Pro:pixelsize=13'
DZEN2_TIMEOUT=5

SCREEN_CACHE_TIMEOUT="60"
SCREEN_CACHE_FILE="${XDG_RUNTIME_DIR:-$HOME/.cache}/xrandr.screens"

if [ -z "$DISPLAY" ]; then
    export DISPLAY=:0.0
fi

if [ "$(uname)" = "Linux" ]; then
    STAT_MTIME="stat -c %s"
else
    STAT_MTIME="stat -f %m"
fi

#------------------------------------------------------------------------------
# Detect Screens using XRandR
#------------------------------------------------------------------------------

detect_screens() {
    if [ -r "${SCREEN_CACHE_FILE}" ] && [ $(( $(date +%s) - $(${STAT_MTIME} "${SCREEN_CACHE_FILE}" 2> /dev/null) )) -le ${SCREEN_CACHE_TIMEOUT} ]; then
    	cat "${SCREEN_CACHE_FILE}"
    	return 0
    fi

    xrandr -q | grep ' connected' | awk 'match($0, /connected.*[0-9]+x[0-9]+\+[0-9]+\+[0-9]+/) {
	print substr($0, RSTART, RLENGTH)
    }' | while read screen; do
	width=$(echo ${screen} | cut -d x -f 1 | awk '{print $NF}')
	x=$(echo ${screen} | cut -d + -f 2)
	y=$(echo ${screen} | cut -d + -f 3)
	if echo ${screen} | grep -q primary; then
	    primary=1
	else
	    primary=0
        fi

	echo ${width} ${x} ${y} ${primary}
    done | tee ${SCREEN_CACHE_FILE}
}

#------------------------------------------------------------------------------
# Display notification using dzen2
#------------------------------------------------------------------------------

dzen2_notify() {
    type=$1
    sender=$2
    body=$(echo $3 | sed 's/\^/\^\^/g')

    detect_screens | while read screen; do
        width=$(($(echo $screen | awk '{print $1}') * 2 / 3))
	x=$(echo $screen | awk '{print $2}')
	y=$(echo $screen | awk '{print $3}')
	primary=$(echo $screen | awk '{print $4}')

	if [ $primary -eq 0 ]; then
	    continue
	fi

        message="^bg(${DZEN2_HIGHLIGHT})^fg(${DZEN2_BACKGROUND}) ${type} ^bg()^fg() ${sender}"
	if [ -n "${body}" ]; then
	    message="${message}^fg(${DZEN2_HIGHLIGHT}) | ^fg()${body}"
	fi

	echo ${message} | dzen2 \
	    -e 'button1=exit:1;key_Escape=ungrabkeys,exit;leavetitle=exit;' \
	    -w  ${width}		\
	    -ta l			\
	    -bg "${DZEN2_BACKGROUND}"	\
	    -fg "${DZEN2_FOREGROUND}"	\
	    -fn "${DZEN2_FONTNAME}"	\
	    -p  ${DZEN2_TIMEOUT}	\
	    -x  ${x}			\
	    -y  ${y} &
    done
}

#------------------------------------------------------------------------------
# Main Execution
#------------------------------------------------------------------------------

dzen2_notify "$@"

# vim: sts=4 sw=4 ts=8 expandtab ft=sh
