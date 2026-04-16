"""Database connection helper and schema bootstrap."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from .config import config


def get_conn() -> sqlite3.Connection:
    """Return a database connection with row_factory and foreign keys enabled."""
    conn = sqlite3.connect(config.db_path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str | None = None) -> None:
    """Initialize the database by running schema.sql idempotently.

    Args:
        db_path: Optional override for DB_PATH from config.
    """
    db_path = db_path or config.db_path
    schema_dir = Path(__file__).parent
    schema_path = schema_dir / "schema.sql"

    # Ensure data directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path, timeout=10)
    try:
        with open(schema_path, "r") as f:
            schema_sql = f.read()
        conn.executescript(schema_sql)
    finally:
        conn.close()


def check_schema(conn: sqlite3.Connection) -> None:
    """Verify that all required tables and triggers exist.

    Raises:
        RuntimeError: If any expected schema element is missing.
    """
    # Check main tables exist
    tables = {"notes", "notes_fts", "note_revisions"}
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    existing = {row[0] for row in cursor.fetchall()}
    missing = tables - existing
    if missing:
        raise RuntimeError(f"Missing tables: {missing}")

    # Check triggers exist
    triggers = {"notes_ai", "notes_au", "notes_ad"}
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='trigger' ORDER BY name"
    )
    existing_triggers = {row[0] for row in cursor.fetchall()}
    missing_triggers = triggers - existing_triggers
    if missing_triggers:
        raise RuntimeError(f"Missing triggers: {missing_triggers}")
