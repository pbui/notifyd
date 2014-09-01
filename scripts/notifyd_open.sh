#!/bin/sh

FILES_PATH=$HOME/.config/notifyd/files

for file in "$@"; do
    TYPE=WWW
    SENDER=file
    NAME=$(basename $file)
    BODY=http://localhost:9412/files/$NAME

    if ! cp "$file" $FILES_PATH/$NAME; then
    	continue
    fi

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
