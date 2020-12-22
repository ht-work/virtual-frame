#!/usr/bin/env bash

cd $(dirname $0)

WORK_DIR=${PWD}
NAME=iaas
POOL_LIST="hachi huchi xxg"

if [ ! -d dist ]; then
    echo -e "\033[31m err:\033[0m dist directorynot exist."
    exit 1
fi

systemctl stop ${NAME} 2>/dev/null
for _pool in ${POOL_LIST}; do
    systemctl stop ${NAME}-${_pool} 2>/dev/null
done

[ -e /usr/local/bin/${NAME} ] && rm -f /usr/local/bin/${NAME}
[ -d /etc/${NAME}  ] && rm -rf /etc/${NAME}
for _pool in ${POOL_LIST}; do
    [ -e /usr/lib/systemd/system/${NAME}-${_pool}.service  ] && rm -f /usr/lib/systemd/system/${NAME}-${_pool}.service
done
[ -e /usr/lib/systemd/system/${NAME}.service  ] && rm -f /usr/lib/systemd/system/${NAME}.service


[ ! -d /usr/local/bin  ] && mkdir -p /usr/local/bin
[ ! -d /etc/${NAME}  ] && mkdir -p /etc/${NAME}
[ ! -d /usr/lib/systemd/system  ] && mkdir -p /usr/lib/systemd/system
cp -rf dist /etc/${NAME}/

cp -f ${NAME} /usr/local/bin/ && chmod +x /usr/local/bin/${NAME}
cp -rf config /etc/${NAME}/
for _pool in ${POOL_LIST}; do
    cp -f ${NAME}.service /usr/lib/systemd/system/${NAME}-${_pool}.service
    sed -i \
        -e "s/xxx_pool_xxx/${_pool}/g" \
        -e "s/xxx_service_xxx/${NAME}-${_pool}/g"  \
        /usr/lib/systemd/system/${NAME}-${_pool}.service
done
cp -f ${NAME}.service /usr/lib/systemd/system/${NAME}.service
sed -i \
    -e "s/xxx_pool_xxx/${NAME}/g" \
    -e "s/xxx_service_xxx/${NAME}/g"  \
    /usr/lib/systemd/system/${NAME}.service


systemctl daemon-reload

systemctl start ${NAME}
systemctl enable ${NAME}
for _pool in ${POOL_LIST}; do
    systemctl start ${NAME}-${_pool}
    systemctl enable ${NAME}-${_pool}
done

exit 0
