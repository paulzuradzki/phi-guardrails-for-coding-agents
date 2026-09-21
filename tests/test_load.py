from contextlib import contextmanager
from decimal import Decimal

import pytest

from phi_guardrails import load


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


class FakeConn:
    """Records the COPY statement and rows written; no DB involved."""

    def __init__(self):
        self.statement = None
        self.rows = []

    @contextmanager
    def cursor(self):
        yield self

    @contextmanager
    def copy(self, statement):
        self.statement = statement.as_string()
        yield self

    def write_row(self, row):
        self.rows.append(tuple(row))


def test_load_table_streams_rows_over_given_connection(tmp_path):
    # Arrange
    csv_path = tmp_path / "beneficiary.csv"
    csv_path.write_text("DESYNPUF_ID,BENE_BIRTH_DT\nID1,19230501\nID2,\n")
    df = load.read_csv(csv_path)
    conn = FakeConn()

    # Act
    n = load.load_table("beneficiary", df, conn)

    # Assert
    assert n == 2
    assert conn.statement == 'COPY "beneficiary" ("desynpuf_id", "bene_birth_dt") FROM STDIN'
    assert conn.rows == [("ID1", "19230501"), ("ID2", None)]


def test_load_table_roundtrip(db, tmp_path):
    """Integration: real schema in claims_test; rolled back by the fixture."""
    # Arrange
    csv_path = tmp_path / "beneficiary.csv"
    csv_path.write_text("DESYNPUF_ID,BENE_BIRTH_DT,MEDREIMB_IP\nID1,19230501,12.50\nID2,19430101,\n")
    df = load.read_csv(csv_path)
    with db.cursor() as cur:
        cur.execute("TRUNCATE beneficiary")

    # Act
    n = load.load_table("beneficiary", df, db)

    # Assert
    assert n == 2
    with db.cursor() as cur:
        cur.execute("SELECT desynpuf_id, medreimb_ip FROM beneficiary ORDER BY desynpuf_id")
        rows = cur.fetchall()
    assert [r["desynpuf_id"] for r in rows] == ["ID1", "ID2"]
    assert [r["medreimb_ip"] for r in rows] == [Decimal("12.50"), None]
