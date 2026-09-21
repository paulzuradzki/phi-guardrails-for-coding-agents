"""Load the downloaded CSVs into local Postgres via Polars.

Usage:
    uv run python -m phi_guardrails.load            # load both tables
    uv run python -m phi_guardrails.load --table beneficiary
    uv run python -m phi_guardrails.load --truncate  # wipe tables first
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import polars as pl
from psycopg import sql

from .config import load_config
from .db import connect
from .fetch import DATA_DIR

log = logging.getLogger(__name__)

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


def load_table(table: str, df: pl.DataFrame, conn) -> int:
    """Stream a DataFrame into a table with COPY on *this* connection.

    Returns the number of rows written. Using the caller's connection keeps
    a TRUNCATE + load in one transaction and avoids a second connection
    blocking on locks the first one holds.
    """
    columns = sql.SQL(", ").join(sql.Identifier(c) for c in df.columns)
    stmt = sql.SQL("COPY {} ({}) FROM STDIN").format(sql.Identifier(table), columns)
    with conn.cursor() as cur, cur.copy(stmt) as copy:
        for row in df.iter_rows():
            copy.write_row(row)
    return df.height


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--table", choices=list(TABLES), help="load a single table instead of both"
    )
    parser.add_argument(
        "--truncate", action="store_true", help="TRUNCATE tables before loading"
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    cfg = load_config()
    tables = [args.table] if args.table else list(TABLES)

    with connect(cfg) as conn:
        for table in tables:
            csv_path = DATA_DIR / TABLES[table]
            if args.truncate:
                with conn.cursor() as cur:
                    cur.execute(sql.SQL("TRUNCATE {}").format(sql.Identifier(table)))
            df = read_csv(csv_path)
            n = load_table(table, df, conn)
            conn.commit()  # each table is its own transaction
            log.info("%s: loaded %d rows", table, n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
