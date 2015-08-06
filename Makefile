.PHONY: help check-stage pipme setup require lint test

help:
	@echo "check-stage - check staged changes for lint errors"
	@echo "pipme - install requirements.txt"
	@echo "setup - setup database"
	@echo "require - create requirements.txt"
	@echo "lint - check style with flake8"
	@echo "test - run nose and script tests"

check-stage:
	bin/check-stage

pipme:
	pip install -r requirements.txt

setup:
  virtualenv venv
  source venv/bin/activate
  pipme
  manage -m Scraper setup

require:
	pip freeze -l | grep -vxFf dev-requirements.txt > requirements.txt

lint:
	flake8 app tests

test:
	nosetests -xv
