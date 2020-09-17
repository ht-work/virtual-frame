PYTHON ?= python

__default__:
	@echo "Please specify a target to make"

clean:
	@find ./ -name __pycache__ | xargs rm -rf

pep8:
	@pytest -v --pep8 src/netcp

flakes:
	@pytest -v --flakes src/netcp

check: pep8 flakes

test:
	@py.test -v --self-contained-html -n 4 src/test/*.py

cov:
	@py.test -v --cov=src/util_base --cov-report=term --cov-report=xml

dev: all
	$(PYTHON) setup.py develop

install: all
	$(PYTHON) setup.py install

all: clean

.PHONY: clean
