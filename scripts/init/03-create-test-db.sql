-- Separate database for the test suite so tests never touch claims_db.
-- Same schema, reused from 02-create-schema.sql (single source of truth).
-- Runs once on first container start; for an existing volume use
-- `just db-init-test`, which runs this same file. Safe to re-run.
SELECT 'CREATE DATABASE claims_test'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'claims_test') \gexec

\connect claims_test
\i /docker-entrypoint-initdb.d/02-create-schema.sql
