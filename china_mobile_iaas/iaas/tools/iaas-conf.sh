#!/usr/bin/env bash

cd $(dirname $0)

WORK_DIR=${PWD}
NAME=iaas
TARBALL=${NAME}.tar

[ -d $NAME ] && rm -rf $NAME
[ -e ../${TARBALL} ] && rm -rf ../${TARBALL}

mkdir -p $NAME

mv -f ../${NAME} ${NAME}/
cp -rf config ${NAME}/
cp -f ${NAME}.service.in ${NAME}/${NAME}.service
cp -f install.sh ${NAME}/

chmod +x ${NAME}/install.sh

tar -cf ${TARBALL} ${NAME}
rm -rf ${NAME}
mv -f ${TARBALL} ../

exit 0
