import psycopg
import pytest

from phi_guardrails.config import DatabaseConfig
from phi_guardrails.db import connect

FAKE_DSN = "postgresql://human001:fake-human-password@localhost:5432/claims_db"

# Tests only ever talk to claims_test (created by scripts/init/03-create-test-db.sql
# or `just db-init-test`). Never claims_db.
TEST_DSN = "postgresql://human001:fake-human-password@localhost:5432/claims_test"


@pytest.fixture
def cfg() -> DatabaseConfig:
    """Config with a fake DSN; never connects anywhere."""
    return DatabaseConfig(dsn=FAKE_DSN)


@pytest.fixture
def db():
    """DB-API connection to claims_test; skipped when Postgres is unreachable.

    Everything a test does is rolled back at teardown. Keep usage to the
    DB-API surface (cursor/execute/fetchall, row["col"]) so this fixture could
    be pointed at sqlite3 if we ever want DB-free integration tests.
    """
    assert TEST_DSN.rsplit("/", 1)[1].endswith("_test"), "db fixture must target a *_test DB"
    try:
        conn = connect(DatabaseConfig(dsn=TEST_DSN))
    except psycopg.OperationalError as e:
        pytest.skip(f"claims_test not reachable ({e.__class__.__name__}); run `just db-up`")
    yield conn
    conn.rollback()
    conn.close()
