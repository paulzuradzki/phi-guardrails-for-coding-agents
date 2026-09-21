"""Schema column names must match the (lowercased) CSV headers, or COPY fails."""

import re
from pathlib import Path

import pytest

from phi_guardrails.fetch import DATA_DIR
from phi_guardrails.load import TABLES

SCHEMA_SQL = Path(__file__).parent.parent / "scripts" / "init" / "02-create-schema.sql"


def schema_columns(table: str) -> list[str]:
    """Column names of one CREATE TABLE block, in order."""
    body = re.search(
        rf"CREATE TABLE IF NOT EXISTS {table} \((.*?)\n\);", SCHEMA_SQL.read_text(), re.S
    ).group(1)
    return [m.group(1) for m in re.finditer(r"^\s+([a-z0-9_]+)\s", body, re.M)]


def csv_header(csv_path: Path) -> list[str]:
    """Only the header line is read; never a data row."""
    if not csv_path.exists():
        pytest.skip(f"{csv_path.name} not fetched; run `just fetch`")
    with csv_path.open() as f:
        return [c.strip().strip('"').lower() for c in f.readline().rstrip("\n").split(",")]


@pytest.mark.parametrize("table", list(TABLES))
def test_schema_columns_match_csv_header(table):
    # Arrange
    expected = csv_header(DATA_DIR / TABLES[table])

    # Act
    actual = schema_columns(table)

    # Assert
    assert actual == expected
