storage
========

storeagentd is a gRPC server for VIK.

## To try:
Depends: python36-pip grpcio grpcio-tools setuptools
```sh
#setup 1
# yum install device-mapper-multipath
# install util_base agent
# pip3 install -r requirements.txt

#setup 2
# python3 setup.py bdist_wheel
# pip3 install dist/storeagentd-*.whl

#or

# python3 setup.py sdist
# pip3 install dist/storeagentd-*.tar.gz

#or only install *.pyc

# python3 setup.py bdist_egg --exclude-source-files
# easy_install dist/eggname.egg

# storeagentd
```
## Test:
Depends: pytest pytest-grpc
```sh
# make test
```
## Test Coverage:
Depends: coverage pytest-cov
```sh
# make cov
```
## Test pep8:
Depends: pep8 pytest-pep8
```sh
# make pep8
```
## Test flakes:
Depends: python-flakes
```sh
# make flakes
```
## Test check:
```sh
# make check
```
