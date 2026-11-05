#!/bin/bash
set -euo pipefail

cd /taibif-code

python manage.py migrate --no-input
python manage.py collectstatic --no-input \
    --ignore='search.dev.js*' --ignore='search.min.js*' \
    --ignore='dataset-table.dev.js*' --ignore='dataset-table.min.js*'

exec gunicorn --bind 0.0.0.0:8001 --workers=5 --timeout 120 conf.wsgi:application
