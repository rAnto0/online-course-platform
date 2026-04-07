#!/bin/sh
set -eu

if [ -n "${POSTGRES_AUTH_DB:-}" ]; then
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE "${POSTGRES_AUTH_DB}";
EOSQL
fi

if [ -n "${POSTGRES_COURSE_DB:-}" ]; then
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE "${POSTGRES_COURSE_DB}";
EOSQL
fi

if [ -n "${POSTGRES_PROGRESS_DB:-}" ]; then
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE "${POSTGRES_PROGRESS_DB}";
EOSQL
fi
