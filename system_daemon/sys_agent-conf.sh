#!/bin/bash

cd $(dirname $0)

WORK_DIR=${PWD}
NAME=sys_agent
VERSION=$(grep -m1 __version__ sysagent/__init__.py | awk -F = '{print $2}' | sed "s/'//g;s/ //g")

release_tag="dirty, dirty, dirty"
if test -d .git && command -v git &>/dev/null; then
    git_version=$(git rev-parse --short HEAD)
    git_branch=$(git branch | grep "^*" | awk '{print $2}')
    remote=$(git config --get branch.${git_branch}.remote)
    url=$(git config --get remote.${remote}.url)
    ip=$(echo $url | grep -o -P "(\d+\.)(\d+\.)(\d+\.)\d+")
    source_path=$(echo ${url//$ip/IP})
    release_tag="$source_path, $git_branch, $git_version"
fi

[ -e rpmbuild ] && rm -rf rpmbuild
mkdir -p rpmbuild/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}

pushd $(dirname ${WORK_DIR})
[ -e ${NAME}-${VERSION} ] && rm -rf ${NAME}-${VERSION}
mkdir ${NAME}-${VERSION}
cp -rf ${WORK_DIR}/* ${NAME}-${VERSION}/
tar -zcvf ${WORK_DIR}/rpmbuild/SOURCES/${NAME}-${VERSION}.tar.gz ${NAME}-${VERSION}
rm -rf ${NAME}-${VERSION}
popd

rpmbuild --bb --define "_topdir ${dir:-${WORK_DIR}/rpmbuild}" --define "release_tag $release_tag" ${NAME}.spec

exit 0
