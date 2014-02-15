#!/bin/sh

cat <<EOF | curl -X POST -d @- localhost:9411
{
    "messages" : [
	{
	    "type"	: "$1",
	    "sender"	: "$2",
	    "body"	: "$3"
	}
    ]
}
EOF
