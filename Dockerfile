# syntax=docker/dockerfile:1
FROM python:3.10-slim-bookworm

# set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# update & install system package
RUN apt-get update && apt-get install -y \
    gettext

# timezone to Asia/Taipei
RUN ln -sf /usr/share/zoneinfo/Asia/Taipei /etc/localtime
RUN echo "Asia/Taipei" > /etc/timezone
ENV TZ=Asia/Taipei

WORKDIR /taibif-code/

# install python package
RUN pip install --upgrade pip
RUN pip install --no-cache-dir pipenv

# Copy only the requirements file
COPY requirements.txt ./

# Install dependencies from requirements.txt
RUN pip install -r requirements.txt


##### install with Pipefile (deprecated version) ######
# COPY Pipfile Pipfile.lock ./
# RUN pipenv install --system


COPY . .
