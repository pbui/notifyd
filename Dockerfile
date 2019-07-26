FROM	    alpine:latest
MAINTAINER  Peter Bui <pbui@yld.bx612.space>

RUN	    apk update && \
	    apk add python3 py3-tornado

RUN	    wget -O - https://gitlab.com/pbui/notifyd/-/archive/master/notifyd-master.tar.gz | tar xzvf -

EXPOSE	    9411
ENTRYPOINT  ["/notifyd-master/notifyd.py", "--config-dir=/var/lib/notifyd", "--address=0.0.0.0"]
