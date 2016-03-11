#!/bin/sh

FILES_PATH=$HOME/.config/notifyd/files

for file in "$@"; do
    TYPE=WWW
    SENDER=file
    NAME=$(basename "$file")
    EXTENSION="${NAME##*.}"

    BODY="http://localhost:9412/files/$NAME"
    if ! cp "$file" "$FILES_PATH/$NAME"; then
	continue
    fi

    case ${EXTENSION} in
	doc|docx|xls|xlsx)
	    BODY="$(google-drive-upload $file)"
	    if [ -z ${BODY} ]; then
		BODY="http://localhost:9412/files/$NAME"
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
