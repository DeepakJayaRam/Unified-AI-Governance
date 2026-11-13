#!/bin/sh
set -eu
# psql literal quoting avoids interpolating a password into executable SQL.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --set=app_password="$APP_DB_PASSWORD" <<'SQL'
CREATE ROLE uag_app LOGIN PASSWORD :'app_password' NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
GRANT CONNECT ON DATABASE uag TO uag_app;
GRANT USAGE ON SCHEMA public TO uag_app;
ALTER DEFAULT PRIVILEGES FOR ROLE uag_owner IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO uag_app;
SQL
