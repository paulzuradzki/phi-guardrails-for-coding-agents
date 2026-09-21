"""Load the downloaded CSVs into local Postgres via Polars.

Usage:
    uv run python -m phi_guardrails.load            # load both tables
    uv run python -m phi_guardrails.load --table beneficiary
    uv run python -m phi_guardrails.load --truncate  # wipe tables first
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import polars as pl
import sqlalchemy
from psycopg import sql

from .config import load_config
from .db import connect
from .fetch import DATA_DIR

# table name -> CSV filename
TABLES: dict[str, str] = {
    "beneficiary": "beneficiary.csv",
    "inpatient_claims": "inpatient_claims.csv",
}


def read_csv(csv_path: Path) -> pl.DataFrame:
    """Read a CSV with lowercase column names (table columns are lowercase)."""
    if not csv_path.exists():
        raise FileNotFoundError(
            f"{csv_path} not found. Run `uv run python -m phi_guardrails.fetch` first."
        )
    df = pl.read_csv(csv_path, infer_schema_length=0)
    return df.rename({c: c.lower() for c in df.columns})


def load_table(table: str, df: pl.DataFrame, conn, dsn: str) -> int:
    """Write a Polars DataFrame into a table. Returns total rows in table."""
    # polars' sqlalchemy engine needs a SQLAlchemy engine. Swap the scheme in
    # the DSN so SQLAlchemy uses psycopg2 as its driver.
    sa_url = dsn.replace("postgresql://", "postgresql+psycopg2://", 1)
    sa_conn = sqlalchemy.create_engine(sa_url, pool_pre_ping=True)
    df.write_database(
        table,
        sa_conn,
        if_table_exists="append",
        engine="sqlalchemy",
        engine_options={"method": "multi", "chunksize": 5000},
    )
    with conn.cursor() as cur:
        cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table)))
        return cur.fetchone()["count"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--table", choices=list(TABLES), help="load a single table instead of both"
    )
    parser.add_argument(
        "--truncate", action="store_true", help="TRUNCATE tables before loading"
    )
    args = parser.parse_args()

    cfg = load_config()
    tables = [args.table] if args.table else list(TABLES)

    with connect(cfg) as conn:
        for table in tables:
            csv_path = DATA_DIR / TABLES[table]
            if args.truncate:
                with conn.cursor() as cur:
                    cur.execute(sql.SQL("TRUNCATE {}").format(sql.Identifier(table)))
                # load_table writes over a *separate* connection; an uncommitted
                # TRUNCATE holds an ACCESS EXCLUSIVE lock and that write would
                # block forever.
                conn.commit()
            df = read_csv(csv_path)
            n = load_table(table, df, conn, cfg.dsn)
            print(f"{table}: {n} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
