"""Idempotent database initialization script.

Run this manually outside the app to initialize the database:
    python scripts/init_db.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from wiki_notebook.db import init_db


def main() -> None:
    """Initialize the database."""
    db_path = "./data/notebook.db"
    init_db(db_path)
    print(f"Database initialized: {db_path}")


if __name__ == "__main__":
    main()
