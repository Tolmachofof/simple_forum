FROM python:3.7.3

RUN mkdir /opt/simple_forum

WORKDIR /opt/simple_forum


COPY ./simple_forum /opt/simple_forum/simple_forum/
COPY ./tests/ /opt/simple_forum/tests/
COPY ./conf/ /opt/simple_forum/conf/
COPY ./requirements.txt /opt/simple_forum/requirements.txt
COPY ./main.py /opt/simple_forum/main.py

# После копирования в образ может попасть мусор в виде __pycache__ файлов,
# который может помешать нормальной работе
# Чистим WORKDIR от мксора
RUN find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf

RUN pip install -r ./requirements.txt


