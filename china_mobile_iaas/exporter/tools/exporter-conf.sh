#!/usr/bin/env bash

cd $(dirname $0)

WORK_DIR=${PWD}
NAME=exporter
TARBALL=${NAME}.tar


[ -d $NAME ] && rm -rf $NAME
[ -e ../${TARBALL} ] && rm -rf ../${TARBALL}

mkdir -p $NAME

mv -f ../exporter ${NAME}/
cp -f ../config/config.yaml ${NAME}/
cp -f exporter.service ${NAME}/
cp -f install.sh ${NAME}/

chmod +x ${NAME}/install.sh

tar -cf ${TARBALL} ${NAME}
rm -rf ${NAME}
mv -f ${TARBALL} ../

exit 0
