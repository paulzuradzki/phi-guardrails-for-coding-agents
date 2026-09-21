"""Configuration loaded from environment / .env file."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class DatabaseConfig:
    dsn: str


def load_config() -> DatabaseConfig:
    dsn = os.environ["DATABASE_URL"]
    if not dsn.startswith("postgresql://") and not dsn.startswith("postgres://"):
        raise ValueError(f"DATABASE_URL must start with postgresql://, got: {dsn[:20]}...")
    return DatabaseConfig(dsn=dsn)
