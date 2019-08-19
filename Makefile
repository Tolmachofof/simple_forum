all: run

isort:
	isort -rc simple_forum
	isort -rc tests

build: isort
	mkdir -p ./report/coverage
	docker build . --tag simple-forum

# Запуск тестов
test: build
	docker-compose -f docker-compose-testing.yaml up \
	    --force-recreate --abort-on-container-exit --exit-code-from test-app

# Запуск приложения
run: build
	docker-compose -f docker-compose-dev.yaml up