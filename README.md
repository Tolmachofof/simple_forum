# Пример API простого форума.
### Requirements
* Python >= 3.7
* Docker

### Запуск проекта в Docker
```
make run
```

### Запуск тестов в Docker
```
make test
```

### Настройки проекта
Базовые настройки приложения хранятся в файле /conf/conf.yaml

Некоторые настройки могут быть переопределены через переменные окружения:
* DATABASE_HOST
* DATABASE_PORT
* DATABASE_NAME
* DATABASE_USER
* DATABASE_PASSWORD

```
./conf/.test_env - Окружение для запуска тестов

./cont/.dev_env - Окружение для запуска прокта
```
