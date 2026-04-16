"""Pytest fixtures for wiki-notebook tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from wiki_notebook.app import create_app
from wiki_notebook.db import init_db
from wiki_notebook import config


@pytest.fixture
def app():
    """Create a Flask app with a temporary database."""
    # Create a temporary database file
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        # Initialize the temp database
        init_db(db_path)

        # Store original and override db_path
        original_db_path = config.config.db_path
        config.config.db_path = db_path

        app = create_app()
        app.config["TESTING"] = True

        yield app

        # Cleanup: restore original config
        config.config.db_path = original_db_path
    finally:
        # Clean up temp file
        Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


@pytest.fixture
def seed_note(app):
    """Create a helper to insert a note for testing."""
    from wiki_notebook.db import get_conn

    def _seed_note(
        title: str = "Test Note",
        body: str = "Test body content",
        category: str | None = None,
    ) -> int:
        conn = get_conn()
        try:
            from datetime import datetime

            from datetime import timezone

            now = datetime.now(timezone.utc).isoformat().replace("+00:00", "")
            cursor = conn.cursor()
            tags_json = "[]" if category is None else "[]"

            cursor.execute(
                """INSERT INTO notes (title, body, category, tags,
                                     created_at, updated_at)
                 VALUES (?, ?, ?, ?, ?, ?)""",
                (title, body, category, tags_json, now, now),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    return _seed_note
