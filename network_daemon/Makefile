SRC_PROTO=net_agent/AclManager.proto \
          net_agent/ErrNo.proto \
          net_agent/NicManager.proto \
          net_agent/OvsManager.proto \
          net_agent/QosManager.proto \
          net_agent/UpLinkManager.proto

__default__:
	@echo "Please specify a target to make"

clean:
	@rm build -rfv
	@rm dist -rfv
	@rm *.egg-info -rfv
	@find ./ -name __pycache__ | xargs rm -rfv
	@find ./ -name "*pb2*.py" | xargs rm -rfv
	@find ./ -name .coverage | xargs rm -rfv
	@find ./ -name .pytest_cache | xargs rm -rfv
	@find ./ -name htmlcov -or -name *.xml -or -name *.html| xargs rm -rfv

all-proto:
	python3 -m grpc_tools.protoc --python_out=. --grpc_python_out=. -I./protos ${SRC_PROTO}

all: clean all-proto

test:
	@make test -C test

cov:
	@make  cov -C test

pep8:
	@make  pep8 -C test || true
	@py.test --pep8 -v net_agent

flakes:
	@make flakes -C test || true
	@py.test -v --flakes net_agent

.PHONY: test proto

