"""Rebuild FTS5 search index from notes table.

Run this if the FTS5 index ever drifts from the notes table:
    python scripts/rebuild_fts.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import sqlite3

from wiki_notebook.config import config


def rebuild_fts(db_path: str | None = None) -> None:
    """Drop and rebuild the FTS5 index.

    Args:
        db_path: Optional override for DB_PATH from config.
    """
    db_path = db_path or config.db_path

    conn = sqlite3.connect(db_path, timeout=10)
    try:
        cursor = conn.cursor()

        # Get current note count
        cursor.execute("SELECT COUNT(*) FROM notes")
        note_count = cursor.fetchone()[0]

        print(f"Notes in table: {note_count}")
        print(f"Rebuilding FTS5 index for: {db_path}")

        # Record FTS count before rebuild
        cursor.execute("SELECT COUNT(*) FROM notes_fts")
        fts_before = cursor.fetchone()[0]
        print(f"FTS5 rows before rebuild: {fts_before}")

        # Rebuild FTS5 index
        cursor.execute("INSERT INTO notes_fts(notes_fts) VALUES('rebuild')")
        conn.commit()

        # Get FTS row count after rebuild
        cursor.execute("SELECT COUNT(*) FROM notes_fts")
        fts_after = cursor.fetchone()[0]
        print(f"FTS5 rows after rebuild: {fts_after}")

        if note_count != fts_after:
            print(f"WARNING: Mismatch! notes={note_count}, notes_fts={fts_after}")
    finally:
        conn.close()


def main() -> None:
    """Main entry point."""
    rebuild_fts()


if __name__ == "__main__":
    main()
