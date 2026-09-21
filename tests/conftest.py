import pytest

from phi_guardrails.config import DatabaseConfig


@pytest.fixture
def cfg() -> DatabaseConfig:
    """Config with a fake DSN; never connects anywhere."""
    return DatabaseConfig(
        dsn="postgresql://human001:fake-human-password@localhost:5432/claims_db"
    )
