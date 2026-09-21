import polars as pl

from phi_guardrails import load


def test_tables_map_is_consistent():
    assert set(load.TABLES) == {"beneficiary", "inpatient_claims"}
    for _table, csv_name in load.TABLES.items():
        assert csv_name.endswith(".csv")


def test_read_csv_missing(tmp_path):
    try:
        load.read_csv(tmp_path / "nope.csv")
        raise AssertionError("expected FileNotFoundError")
    except FileNotFoundError as e:
        assert "fetch" in str(e)


def test_read_csv_lowercases_columns(tmp_path):
    csv_path = tmp_path / "beneficiary.csv"
    csv_path.write_text("DESYNPUF_ID,BENE_BIRTH_DT\nID1,19230501\n")
    df = load.read_csv(csv_path)
    assert df.columns == ["desynpuf_id", "bene_birth_dt"]
    assert df.shape == (1, 2)


def test_load_table_writes_dataframe(monkeypatch):
    df = pl.DataFrame({"desynpuf_id": ["ID1"], "bene_birth_dt": ["19230501"]})
    calls: list[tuple] = []

    monkeypatch.setattr(
        pl.DataFrame,
        "write_database",
        lambda self, table, conn, **kw: calls.append((table, conn, kw)),
    )
    monkeypatch.setattr(
        load.sqlalchemy,
        "create_engine",
        lambda url, **kw: calls.append(("engine", url)) or object(),
    )

    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def execute(self, q):
            pass

        def fetchone(self):
            return {"count": 1}

    class FakeConn:
        dsn = "postgresql://human001:fake-human-password@localhost:5432/claims_db"

        def cursor(self):
            return FakeCursor()

    n = load.load_table("beneficiary", df, FakeConn(), FakeConn.dsn)
    assert n == 1
    assert (
        "engine",
        FakeConn.dsn.replace("postgresql://", "postgresql+psycopg2://", 1),
    ) in calls
    table, _conn, kw = calls[-1]
    assert table == "beneficiary"
    assert kw["if_table_exists"] == "append"
