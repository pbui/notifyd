#!/bin/sh

FILES_PATH=$HOME/.config/notifyd/files

for file in "$@"; do
    TYPE=WWW
    SENDER=file
    NAME=$(basename "$file")
    EXTENSION="${NAME##*.}"

    BODY="http://$(ip -br addr show wg0 | grep -Po '\d+.\d+.\d+.\d+'):9411/files/$NAME"
    if ! cp "$file" "$FILES_PATH/$NAME"; then
	continue
    fi

    case ${EXTENSION} in
	doc|docx|xls|xlsx)
	    UPLOAD="$(google-drive-upload $file)"
	    if [ ! -z "${UPLOAD}" ]; then
		BODY="${UPLOAD}"
	    fi
	;;
    esac

    cat <<EOF | curl -X POST -d @- http://localhost:9411/messages
    {
	"messages" : [
	    {
		"type"	    : "${TYPE}",
		"sender"    : "${SENDER}",
		"body"	    : "${BODY}"
	    }
	]
    }
EOF
done
