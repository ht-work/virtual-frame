__default__:
	@echo "Please specify a target to make"

test:
	@py.test -v --html=test.html --self-contained-html

cov:
	@py.test -v --cov=../sysagent --cov-report=term --cov-report=xml --cov-report=html

pep8:
	@py.test -v --pep8

flakes:
	@py.test -v --flakes
