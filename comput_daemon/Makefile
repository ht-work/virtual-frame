PYTHON ?= python

__default__:
	@echo "Please specify a target to make"

clean:
	@find ./ -name __pycache__ | xargs rm -rf
	@find ./ -name "*pb2*.py" -delete

proto:
	$(PYTHON) -m grpc_tools.protoc -I src/virt_agent/proto/ --python_out=./src/ --grpc_python_out=./src/ src/virt_agent/proto/virt_agent/*.proto

pep8:
	@pytest -v --pep8 src/virt_agent

flakes:
	@pytest -v --flakes src/virt_agent

check: pep8 flakes

test:
	@py.test -v -n 4 --self-contained-html src/tests/*.py

dev: all
	$(PYTHON) setup.py develop

install: all
	$(PYTHON) setup.py install

all: clean proto

.PHONY: clean proto
