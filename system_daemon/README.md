# sysagent

A gRPC server for system.

## To try:
Depends: python36-pip grpcio grpcio-tools setuptools wheel
```sh
# python3 setup.py bdist_egg --exclude-source-files
# easy_install --always-unzip dist/sysagent-*.egg
# sys-agentd
```

## Test:
Depends: pytest pytest-grpc pytest-html
```sh
# make test
```

## Coverage:
Depends: coverage pytest-cov
```sh
# make cov
```

## pep8:
Depends: pep8 pytest-pep8
```sh
# make pep8
```

## flakes:
Depends: pyflakes pytest-flakes
```sh
# make flakes
```
