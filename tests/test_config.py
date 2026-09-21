import pytest
from conftest import FAKE_DSN

from phi_guardrails.config import DatabaseConfig, load_config


def test_dsn_passthrough(cfg: DatabaseConfig):
    # Arrange
    dsn = cfg.dsn

    # Act
    # (property access is the act; nothing else to do)

    # Assert
    assert dsn == FAKE_DSN


@pytest.mark.parametrize(
    ("env_value", "expected"),
    [
        (
            "postgresql://agent001:fake-agent-password@localhost:5432/claims_db",
            "postgresql://agent001:fake-agent-password@localhost:5432/claims_db",
        ),
        (
            "postgres://human001:fake-human-password@localhost:5432/claims_db",
            "postgres://human001:fake-human-password@localhost:5432/claims_db",
        ),
    ],
)
def test_load_config_reads_env(monkeypatch, env_value, expected):
    # Arrange
    monkeypatch.setenv("DATABASE_URL", env_value)

    # Act
    cfg = load_config()

    # Assert
    assert cfg.dsn == expected


@pytest.mark.parametrize(
    "bad_value",
    ["mysql://user:pass@localhost/db", "sqlite:///local.db", "http://localhost"],
)
def test_load_config_rejects_bad_scheme(monkeypatch, bad_value):
    # Arrange
    monkeypatch.setenv("DATABASE_URL", bad_value)

    # Act / Assert
    with pytest.raises(ValueError, match="postgresql"):
        load_config()
