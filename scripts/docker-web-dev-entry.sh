#!/bin/bash
set -euo pipefail

cd /taibif-code

bash ./scripts/prepare-static-assets.sh

python manage.py migrate --no-input

exec python manage.py runserver 0.0.0.0:8001
