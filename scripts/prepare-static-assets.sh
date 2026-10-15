#!/bin/bash
set -euo pipefail

# Assets are built in Docker's Node stage, not when the Python container starts.
assets_dir=/opt/taibif-assets/js
for filename in search.dev.js search.min.js dataset-table.dev.js dataset-table.min.js; do
  if [[ ! -s "$assets_dir/$filename" ]]; then
    echo "Missing Docker build asset: $filename. Rebuild the web image before starting it." >&2
    exit 1
  fi
done

mkdir -p /taibif-code/static/js
cp -R "$assets_dir/." /taibif-code/static/js/
