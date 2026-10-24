#!/bin/sh
set -e

: "${DB_PG_DJANGO_USER:?DB_PG_DJANGO_USER is required}"
: "${DB_PG_DJANGO_PASSWORD:?DB_PG_DJANGO_PASSWORD is required}"
: "${DB_PG_CINEMA_USER:?DB_PG_CINEMA_USER is required}"
: "${DB_PG_CINEMA_PASSWORD:?DB_PG_CINEMA_PASSWORD is required}"
: "${DB_PG_PARSER_USER:?DB_PG_PARSER_USER is required}"
: "${DB_PG_PARSER_PASSWORD:?DB_PG_PARSER_PASSWORD is required}"

psql -v ON_ERROR_STOP=1 \
    --username "$POSTGRES_USER" \
    --dbname "$POSTGRES_DB" \
    --set=django_user="$DB_PG_DJANGO_USER" \
    --set=django_password="$DB_PG_DJANGO_PASSWORD" \
    --set=cinema_user="$DB_PG_CINEMA_USER" \
    --set=cinema_password="$DB_PG_CINEMA_PASSWORD" \
    --set=parser_user="$DB_PG_PARSER_USER" \
    --set=parser_password="$DB_PG_PARSER_PASSWORD" <<'SQL'
SELECT format('CREATE ROLE %I LOGIN', :'django_user')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'django_user')
\gexec

SELECT format('CREATE ROLE %I LOGIN', :'cinema_user')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'cinema_user')
\gexec

SELECT format('CREATE ROLE %I LOGIN', :'parser_user')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'parser_user')
\gexec

ALTER ROLE :"django_user"
    WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT
    PASSWORD :'django_password';
ALTER ROLE :"cinema_user"
    WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT
    PASSWORD :'cinema_password';
ALTER ROLE :"parser_user"
    WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT
    PASSWORD :'parser_password';

ALTER ROLE :"django_user" SET default_transaction_read_only = on;
ALTER ROLE :"cinema_user" SET default_transaction_read_only = on;
ALTER ROLE :"cinema_user" SET statement_timeout = '30s';
SQL
