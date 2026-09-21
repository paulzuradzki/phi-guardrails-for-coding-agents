import pytest

from phi_guardrails import load

FAKE_DSN = "postgresql://human001:fake-human-password@localhost:5432/claims_db"


@pytest.fixture
def live_db():
    """Real Postgres via docker compose. Skipped when the DB is unreachable."""
    import psycopg

    try:
        conn = psycopg.connect(FAKE_DSN)
    except psycopg.OperationalError:
        pytest.skip("Postgres not reachable; run `just db-up`")
    yield conn
    conn.close()


def test_read_csv_missing(tmp_path):
    # Arrange
    missing = tmp_path / "nope.csv"

    # Act / Assert
    with pytest.raises(FileNotFoundError, match="fetch"):
        load.read_csv(missing)


def test_read_csv_lowercases_columns(tmp_path):
    # Arrange
    csv_path = tmp_path / "beneficiary.csv"
    csv_path.write_text("DESYNPUF_ID,BENE_BIRTH_DT\nID1,19230501\n")

    # Act
    df = load.read_csv(csv_path)

    # Assert
    assert df.columns == ["desynpuf_id", "bene_birth_dt"]
    assert df.shape == (1, 2)


def test_load_table_roundtrip(live_db, tmp_path):
    # Arrange
    csv_path = tmp_path / "beneficiary.csv"
    csv_path.write_text("DESYNPUF_ID,BENE_BIRTH_DT\nID1,19230501\nID2,19430101\n")
    df = load.read_csv(csv_path)
    with live_db.cursor() as cur:
        cur.execute("TRUNCATE beneficiary")
    # Release the TRUNCATE lock: load_table inserts over a second connection.
    live_db.commit()

    # Act
    n = load.load_table("beneficiary", df, live_db, FAKE_DSN)

    # Assert
    assert n == 2
    with live_db.cursor() as cur:
        cur.execute("SELECT desynpuf_id FROM beneficiary ORDER BY desynpuf_id")
        assert [r["desynpuf_id"] for r in cur.fetchall()] == ["ID1", "ID2"]
