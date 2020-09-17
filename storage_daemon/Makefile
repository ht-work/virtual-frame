SRC_PROTO=storeagent/adapters.proto \
        storeagent/store_util.proto \
	         storeagent/pools.proto \
	          storeagent/vols.proto

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
	@find ./ -name "*.pyc" | xargs rm -rfv
	@find ./ -name build | xargs rm -rfv
	@find ./ -name dist | xargs rm -rfv
	@find ./ -name storeagent.egg-info | xargs rm -rfv

all-proto:
	python3 -m grpc_tools.protoc --python_out=. --grpc_python_out=. -I./proto ${SRC_PROTO}

all: clean all-proto

test:
	@make test -C test

cov:
	@make  test-cov -C test

pep8:
	@make  test-pep8 -C test || true
	@py.test --pep8 -v storeagent

flakes:
	@pytest -v --flakes storeagent

check: pep8 flakes

.PHONY: test proto
