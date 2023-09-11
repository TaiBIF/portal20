# syntax=docker/dockerfile:1
FROM node:18-alpine as build
WORKDIR /code
COPY ./frontend-data/package*.json ./frontend-data/yarn.lock ./
COPY ./frontend-data/webpack.config.js ./frontend-data/.babelrc ./
RUN yarn install
COPY ./frontend-data/src ./src
RUN yarn build-dev

##
# stage 2
##
FROM python:3.10-slim-buster as final

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
COPY Pipfile Pipfile.lock ./
RUN pipenv install --system

COPY . .

COPY --from=build /code/dist /frondend