#!/usr/bin/env bash

cd $(dirname $0)

WORK_DIR=${PWD}
NAME=exporter

systemctl stop ${NAME} 2>/dev/null

[ -e /usr/local/bin/${NAME} ] && rm -f /usr/local/bin/${NAME}
[ -d /etc/${NAME}  ] && rm -rf /etc/${NAME}
[ -e /usr/lib/systemd/system/${NAME}.service  ] && rm -f /usr/lib/systemd/system/${NAME}.service

[ ! -d /usr/local/bin  ] && mkdir -p /usr/local/bin
[ ! -d /etc/${NAME}  ] && mkdir -p /etc/${NAME}
[ ! -d /usr/lib/systemd/system  ] && mkdir -p /usr/lib/systemd/system

cp -f ${NAME} /usr/local/bin/ && chmod +x /usr/local/bin/${NAME}
cp -f config.yaml /etc/${NAME}/
cp -f ${NAME}.service /usr/lib/systemd/system/

systemctl daemon-reload
systemctl start ${NAME}
systemctl enable ${NAME}

exit 0
