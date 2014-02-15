#!/bin/sh

TYPE=$1
SENDER=$2
shift 2
BODY=$@

cat <<EOF | curl -X POST -d @- localhost:9411
{
    "messages" : [
	{
	    "type"	: "${TYPE}",
	    "sender"	: "${SENDER}",
	    "body"	: "${BODY}"
	}
    ]
}
EOF
