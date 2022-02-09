DUMMY: lint test

lint:
	flake8 pygt3x tests
	mypy pygt3x tests

test:
	pytest
