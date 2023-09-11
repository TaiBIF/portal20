#!/bin/bash

cd /taibif-code

cp /frontend/search.dev.js /taibif-code/static/js
cp /frontend/data-table.dev.js /taibif-code/static/js

python manage.py migrate --no-input

python manage.py runserver 0.0.0.0:8000
