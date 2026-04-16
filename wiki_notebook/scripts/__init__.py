"""Idempotent database initialization script.

Run this manually outside the app to initialize the database:
    python -m wiki_notebook.scripts.init_db
"""

from __future__ import annotations

from wiki_notebook.db import init_db


def main() -> None:
    """Initialize the database."""
    db_path = "./data/notebook.db"
    init_db(db_path)
    print(f"Database initialized: {db_path}")


if __name__ == "__main__":
    main()
