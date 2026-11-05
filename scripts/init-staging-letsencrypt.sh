#!/bin/bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 || ( $# -eq 2 && "$2" != '--dry-run' ) ]]; then
  echo "Usage: bash $0 EMAIL [--dry-run]" >&2
  exit 1
fi
email=$1
if [[ "$email" != *@* || "$email" == -* ]]; then
  echo 'Please provide a valid certificate contact email.' >&2
  exit 1
fi
project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$project_dir"
compose=(docker compose -f docker-compose.yml -f docker-compose-staging.yml)
"${compose[@]}" version >/dev/null

# Start HTTP first. No existing certificate is removed or replaced with a dummy.
"${compose[@]}" up -d nginx
extra_args=()
if [[ "${2:-}" == '--dry-run' ]]; then
  extra_args+=(--dry-run)
fi
"${compose[@]}" run --rm --no-deps --entrypoint certbot certbot certonly \
  --non-interactive --webroot -w /var/www/certbot \
  --cert-name staging.taibif.tw -d staging.taibif.tw \
  --email "$email" --agree-tos --keep-until-expiring "${extra_args[@]}"

if [[ "${2:-}" == '--dry-run' ]]; then
  echo 'Validation succeeded. No certificate was saved; run again without --dry-run to enable HTTPS.'
else
  "${compose[@]}" up -d certbot
  echo 'Certificate ready. Nginx will switch to HTTPS within 60 seconds; renewal is checked every 12 hours.'
fi
