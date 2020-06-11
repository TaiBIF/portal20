#!/bin/bash

cd /taibif-code

npm run build-dev

python manage.py migrate --no-input

python manage.py runserver 0.0.0.0:8000
