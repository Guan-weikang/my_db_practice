#!/usr/bin/env sh
set -eu

echo "Waiting for PostgreSQL to become available..."
until python - <<'PY'
import os
import psycopg

database_url = os.environ["DATABASE_URL"]
database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
database_url = database_url.replace("postgresql+psycopg://", "postgresql://", 1)

with psycopg.connect(database_url):
    pass
PY
do
  sleep 2
done

python /workspace/scripts/stage7/reimport_generated.py --input-dir /workspace/data/stage7/generated
