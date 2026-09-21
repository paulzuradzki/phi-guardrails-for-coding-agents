from phi_guardrails.config import DatabaseConfig, load_config


def test_dsn_passthrough(cfg: DatabaseConfig):
    assert (
        cfg.dsn == "postgresql://human001:fake-human-password@localhost:5432/claims_db"
    )


def test_load_config_reads_env(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql://agent001:fake-agent-password@localhost:5432/claims_db"
    )
    assert (
        load_config().dsn
        == "postgresql://agent001:fake-agent-password@localhost:5432/claims_db"
    )


def test_load_config_rejects_bad_scheme(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "mysql://user:pass@localhost/db")
    try:
        load_config()
        raise AssertionError("expected ValueError")
    except ValueError as e:
        assert "postgresql" in str(e)
