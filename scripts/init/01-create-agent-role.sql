-- Runs once on first container start (docker-entrypoint-initdb.d).
-- Creates the restricted agent role. AGENT_DB_USER / AGENT_DB_PASSWORD are
-- injected as container environment variables from .env.
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = current_setting('agent_db_user')) THEN
      EXECUTE format('CREATE ROLE %I LOGIN PASSWORD %L',
                     current_setting('agent_db_user'),
                     current_setting('agent_db_password'));
   END IF;
END
$$;
