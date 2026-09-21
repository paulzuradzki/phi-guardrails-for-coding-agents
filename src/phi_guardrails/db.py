"""Thin psycopg connection helpers."""

from __future__ import annotations

import psycopg
from psycopg.rows import dict_row

from .config import DatabaseConfig


def connect(cfg: DatabaseConfig) -> psycopg.Connection:
    """Connect with the role configured in .env (DB_USER / DB_PASSWORD)."""
    return psycopg.connect(cfg.dsn, row_factory=dict_row)
