FROM python:3.8.13-slim-bullseye

ENV PYTHONUNBUFFERED 1
ENV AM_I_IN_A_DOCKER_CONTAINER Yes

RUN mkdir -p /django/reputation
WORKDIR /django/reputation
COPY . /django/reputation
#.pyc 파일 생성 X
ENV PYTHONDONTWRITEBYTECODE 1 
ENV PYTHONUNBUFFERED 1

RUN apt-get update
RUN apt-get install -y gcc
RUN apt-get install -y default-libmysqlclient-dev
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install gunicorn
