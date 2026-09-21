DO $$
DECLARE
    agent_user    TEXT := current_setting('agent_db_user', true);
    agent_password TEXT := current_setting('agent_db_password', true);
BEGIN
    IF agent_user IS NULL OR agent_password IS NULL THEN
        RAISE NOTICE 'agent_db_user / agent_db_password not set; skipping agent role';
        RETURN;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = agent_user) THEN
        EXECUTE format('CREATE ROLE %I LOGIN PASSWORD %L', agent_user, agent_password);
    END IF;
END
$$;
