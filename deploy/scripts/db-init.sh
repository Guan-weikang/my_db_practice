#!/usr/bin/env bash
set -Eeuo pipefail

export PGPASSWORD="${POSTGRES_PASSWORD}"

psql_base=(
  psql
  --host "${POSTGRES_HOST:-postgres}"
  --port "${POSTGRES_PORT:-5432}"
  --username "${POSTGRES_USER}"
  --dbname "${POSTGRES_DB}"
  --set ON_ERROR_STOP=1
)

database_has_schema() {
  "${psql_base[@]}" --tuples-only --no-align --command \
    "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'user_account');" \
    | tr -d '[:space:]'
}

database_has_data() {
  local table_exists
  table_exists="$(database_has_schema)"
  if [[ "${table_exists}" != "t" ]]; then
    echo "f"
    return
  fi

  "${psql_base[@]}" --tuples-only --no-align --command \
    "SELECT EXISTS (SELECT 1 FROM public.user_account LIMIT 1);" \
    | tr -d '[:space:]'
}

has_alembic_version() {
  "${psql_base[@]}" --tuples-only --no-align --command \
    "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'alembic_version');" \
    | tr -d '[:space:]'
}

trigger_exists() {
  "${psql_base[@]}" --tuples-only --no-align --command \
    "SELECT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = '${SLOW_TRIGGER_NAME}' AND NOT tgisinternal);" \
    | tr -d '[:space:]'
}

disable_slow_trigger() {
  if [[ "${DISABLE_SLOW_TRIGGER_DURING_IMPORT:-1}" != "1" ]]; then
    return
  fi

  if [[ "$(trigger_exists)" == "t" ]]; then
    echo "Disabling ${SLOW_TRIGGER_NAME} on ${SLOW_TRIGGER_TABLE} before data import"
    "${psql_base[@]}" --command "ALTER TABLE ${SLOW_TRIGGER_TABLE} DISABLE TRIGGER ${SLOW_TRIGGER_NAME};"
  fi
}

enable_slow_trigger() {
  if [[ "${DISABLE_SLOW_TRIGGER_DURING_IMPORT:-1}" != "1" ]]; then
    return
  fi

  if [[ "$(trigger_exists)" == "t" ]]; then
    echo "Enabling ${SLOW_TRIGGER_NAME} on ${SLOW_TRIGGER_TABLE} after data import"
    "${psql_base[@]}" --command "ALTER TABLE ${SLOW_TRIGGER_TABLE} ENABLE TRIGGER ${SLOW_TRIGGER_NAME};"
  fi
}

grant_app_user_permissions() {
  "${psql_base[@]}" --command "GRANT USAGE, CREATE ON SCHEMA public TO ${POSTGRES_USER};"
  "${psql_base[@]}" --command "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ${POSTGRES_USER};"
  "${psql_base[@]}" --command "GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO ${POSTGRES_USER};"
  "${psql_base[@]}" --command "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ${POSTGRES_USER};"
  "${psql_base[@]}" --command "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO ${POSTGRES_USER};"
}

imported_dump=0

if [[ "${IMPORT_DUMP_ON_EMPTY_DB:-1}" == "1" && "$(database_has_schema)" != "t" && -f "${IMPORT_DUMP_PATH:-}" ]]; then
  echo "Importing ${IMPORT_DUMP_PATH}"
  "${psql_base[@]}" --dbname postgres --command "DO \$\$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'root') THEN CREATE ROLE root; END IF; END \$\$;"
  trap enable_slow_trigger EXIT
  disable_slow_trigger
  "${psql_base[@]}" --file "${IMPORT_DUMP_PATH}"
  enable_slow_trigger
  trap - EXIT
  imported_dump=1
  grant_app_user_permissions
elif [[ "$(database_has_schema)" == "t" ]]; then
  echo "Database schema already exists; skipping dump import"
else
  echo "No dump import requested; running migrations on an empty database"
fi

cd /app/backend

if [[ "${imported_dump}" == "1" ]]; then
  echo "Stamping Alembic head for imported dump"
  alembic stamp head
elif [[ "$(has_alembic_version)" == "t" || "$(database_has_schema)" != "t" ]]; then
  echo "Running Alembic migrations"
  alembic upgrade head
  enable_slow_trigger
else
  echo "Database has existing data but no Alembic version; stamping head"
  alembic stamp head
  enable_slow_trigger
fi

grant_app_user_permissions
