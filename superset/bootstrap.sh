#!/bin/bash
# Bootstrap Superset: migrate DB, create admin, init
set -e

echo "=== Superset: DB upgrade ==="
superset db upgrade

echo "=== Superset: Create admin user ==="
superset fab create-admin \
  --username admin \
  --firstname Admin \
  --lastname User \
  --email admin@superset.com \
  --password admin || true

echo "=== Superset: Init ==="
superset init

echo "=== Superset: Bootstrap complete ==="
