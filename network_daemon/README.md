net_agentd
========

net_agentd is a gRPC server for VIK.

## To try:
Depends: python36-pip grpcio grpcio-tools setuptools psutil
```sh
# python3 setup.py bdist_wheel
# pip3 install dist/net_agentd-*.whl

#or

# python3 setup.py sdist
# pip3 install dist/net_agentd-*.tar.gz

#or only install  *.pcy

# python setup.py bdist_egg --exclude-source-files
# easy_install dist/eggname.egg

# net_agentd
```
## Test:
Depends: pytest pytest-grpc
```sh
# make test
```
## Test Coverage:
Depends: coverage pytest-cov
```sh
# make test-cov
```
## Test pep8:
Depends: pep8 pytest-pep8
```sh
# make test-pep8
```