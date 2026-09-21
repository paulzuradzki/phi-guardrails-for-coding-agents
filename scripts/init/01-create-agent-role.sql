-- Compose passes AGENT_DB_USER / AGENT_DB_PASSWORD as container env vars.
-- current_setting() only sees Postgres GUCs, so copy them in via psql first.
\getenv agent_user AGENT_DB_USER
\getenv agent_password AGENT_DB_PASSWORD
\o /dev/null
SELECT set_config('app.agent_db_user', :'agent_user', false);
SELECT set_config('app.agent_db_password', :'agent_password', false);
\o

DO $$
DECLARE
    agent_user    TEXT := current_setting('app.agent_db_user', true);
    agent_password TEXT := current_setting('app.agent_db_password', true);
BEGIN
    IF agent_user IS NULL OR agent_password IS NULL THEN
        RAISE NOTICE 'app.agent_db_user / app.agent_db_password not set; skipping agent role';
        RETURN;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = agent_user) THEN
        EXECUTE format('CREATE ROLE %I LOGIN PASSWORD %L', agent_user, agent_password);
    END IF;
END
$$;
