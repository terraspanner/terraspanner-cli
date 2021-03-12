help:
	@echo "clean - remove all test, coverage and Python artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "clean-test - remove test and coverage artifacts"
	@echo "lint - check style"
	@echo "test - run tests quickly with the default Python"

all: .venv clean clean-pyc clean-test default dist

default: deps

.venv:
	if [ ! -e ".venv/bin/activate_this.py" ] ; then python -m venv .venv ; fi

clean: clean-dist clean-pyc clean-test

clean-dist:
	rm -rf build
	rm -rf dist

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	rm -f .coverage
	rm -fr htmlcov/

deps: .venv
	. .venv/bin/activate && pip install -U -r requirements.txt

dist: .venv
	. .venv/bin/activate && pyinstaller --onefile cli.py

run: .venv
	. .venv/bin/activate && python cli.py