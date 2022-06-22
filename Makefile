DUMMY: lint test format

format:
	black .

lint:
	flake8 pygt3x tests
	mypy pygt3x tests
	pydocstyle pygt3x

test:
	pytest
