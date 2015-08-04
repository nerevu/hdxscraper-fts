.PHONY: help check-stage pipme require lint test

help:
	@echo "check-stage - check staged changes for lint errors"
	@echo "pipme - install requirements.txt"
	@echo "require - create requirements.txt"
	@echo "lint - check style with flake8"
	@echo "test - run nose and script tests"

check-stage:
	bin/check-stage

pipme:
	pip install -r requirements.txt

require:
	pip freeze -l | grep -vxFf dev-requirements.txt > requirements.txt

lint:
	flake8 app tests

test:
	nosetests -xv
