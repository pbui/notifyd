#!/bin/sh

if [ $# -lt 3 -o -z "$3" ]; then
    icon=$1
    title=$1 ; shift
    body=$@
else
    icon=$1  ; shift
    title=$1 ; shift
    body=$@
fi

case $icon in
    \#*)	icon=irc-chat;;
    \&*)	icon=android-messages-desktop;;
    CHAT)	icon=internet-chat;;
    MAIL)	icon=internet-mail;;
    PASSWORD)	icon=password-manager; title=Password;;
    SCREENSHOT) icon=applets-screenshooter; title=Screenshot;;
    PIANOBAR)	icon=google-music-manager-panel;;
    TOUCHPAD)	icon=mouse; title=Touchpad;;
    WWW)	icon=web-browser; title=Link;;
    *)		icon=dialog-information;;
esac

notify-send --icon="$icon" "$title" "$body"
