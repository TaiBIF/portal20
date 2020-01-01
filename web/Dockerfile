FROM python:3.7.2-slim

# set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# for Pillow to support jpeg/png
#ENV INCLUDE=/usr/include
#ENV LIBRARY_PATH=/lib:/usr/lib

# for debian
#RUN apt-get update && \
#    apt-get install -y postgresql-client && \
#    rm -rf /var/lib/apt/lists/*

# timezone to Asia/Taipei
RUN ln -sf /usr/share/zoneinfo/Asia/Taipei /etc/localtime
RUN echo "Asia/Taipei" > /etc/timezone
ENV TZ=Asia/Taipei

WORKDIR /code/

# install python package
RUN pip install --upgrade pip
RUN pip install --no-cache-dir pipenv
COPY Pipfile Pipfile.lock ./
RUN pipenv install --system


#COPY . /code/

# dev
#RUN apk --update add --no-cache postgresql-client

# remove compiling environment `build-dependencies`
#RUN apk del build-dependencies