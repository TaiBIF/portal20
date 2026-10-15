#!/bin/bash
set -euo pipefail

cd /taibif-code

bash ./scripts/prepare-static-assets.sh

python manage.py migrate --no-input
python manage.py collectstatic --no-input

exec gunicorn --bind 0.0.0.0:8001 --workers=5 --timeout 120 conf.wsgi:application
