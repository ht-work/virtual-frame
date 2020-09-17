SRC_PROTO=sysagent/sysagent.proto \
                 sysagent/util.proto

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

proto:
	python3 -m grpc_tools.protoc --python_out=. --grpc_python_out=. -I./proto ${SRC_PROTO}

all: clean proto

test:
	@make test -C test

cov:
	@make cov -C test

pep8:
	@make pep8 -C test || true
	@py.test -v --pep8 sysagent

flakes:
	@make flakes -C test || true
	@py.test -v --flakes sysagent

.PHONY: test proto
