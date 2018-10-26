#!/bin/sh

set -e
set -f

#------------------------------------------------------------------------------
# Constant Defaults
#------------------------------------------------------------------------------

DZEN2_BACKGROUND="${DZEN2_BACKGROUND:=#252525}"
DZEN2_FOREGROUND="${DZEN2_FOREGROUND:=#00bcd4}"
DZEN2_HIGHLIGHT_FG="${DZEN2_HIGHLIGHT_FG:=${DZEN2_FOREGROUND}}"
DZEN2_HIGHLIGHT_BG="${DZEN2_HIGHLIGHT_BG:=#353535}"
DZEN2_FONTNAME="${DZEN2_FONTNAME:='Tamzen:pixelsize=15'}"
DZEN2_TIMEOUT="${DZEN2_TIMEOUT:=5}"

WIDTH_OFFSET="${DZEN2_WIDTH_OFFSET:=0}"
HEIGHT="${DZEN2_HEIGHT:=25}"
X_OFFSET="${DZEN2_X_OFFSET:=0}"
Y_OFFSET="${DZEN2_Y_OFFSET:=0}"

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

    xrandr -q | grep ' connected' | awk 'match($0, /[0-9]+x[0-9]+\+[0-9]+\+[0-9]+/) {
	print substr($0, RSTART, RLENGTH)
    }' | while read screen; do
	width=$(echo ${screen} | cut -d x -f 1)
	x=$(echo ${screen} | cut -d + -f 2)
	y=$(echo ${screen} | cut -d + -f 3)

	echo ${width} ${x} ${y}
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
        width=$(expr `echo $screen | awk '{print $1}'` - ${WIDTH_OFFSET})
        height=${HEIGHT:=}
	x=${X_OFFSET:=$(echo $screen | awk '{print $2}')}
	y=${Y_OFFSET:=$(echo $screen | awk '{print $3}')}

        message="^bg(${DZEN2_HIGHLIGHT_BG})^fg(${DZEN2_HIGHLIGHT_FG}) ${type} ^bg()^fg() ${sender}"
	if [ -n "${body}" ]; then
            message="${message}^fg(${DZEN2_FOREGROUND})^bg(${DZEN_BACKGROUND}) | ^fg()${body}"
	fi

	echo ${message} | dzen2 \
	    -e 'button1=exit:1;key_Escape=ungrabkeys,exit;leavetitle=exit;' \
	    -w  ${width}		\
	    -h  ${height}		\
	    -ta l			\
	    -bg "${DZEN2_BACKGROUND}"	\
	    -fg "${DZEN2_FOREGROUND}"	\
	    -fn "${DZEN2_FONTNAME}"	\
	    -p  "${DZEN2_TIMEOUT}"	\
	    -x  ${x}			\
	    -y  ${y} &
    done
}

#------------------------------------------------------------------------------
# Main Execution
#------------------------------------------------------------------------------

dzen2_notify "$@"

# vim: sts=4 sw=4 ts=8 expandtab ft=sh
