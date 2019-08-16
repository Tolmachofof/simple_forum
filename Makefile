all: test

.install-requirements:
	pip install --upgrade pip
	pip install -r ./requirements.txt

isort:
	isort -rc simple_forum
	isort -rc tests

test: .install-requirements
	mkdir -p ./report/coverage
	mkdir -p ./report/junit
	python -m pytest -vvv
