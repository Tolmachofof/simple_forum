# SIMPLE FORUM - пример API простого форума.
### Requirements
python >= 3.7
### Установка зависимостей
```
pip install -r requerements.txt
```
### Поднятие тестовой БД
```
docker-compose -f docker-compose-testing.yaml
alembic upgrade head
```
### Локальный запуск тестов
```
python -m pytest
```
или
```
make tests
```
### Запуск прокта
```
python main.py run-app
```
