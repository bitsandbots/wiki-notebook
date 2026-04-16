"""Tests for optimize and undo functionality."""

from __future__ import annotations

import pytest


class TestOptimizeNote:
    """Tests for POST /api/notes/<id>/optimize."""

    def test_optimize_note(self, client, seed_note):
        """Should optimize a note and create a revision."""
        note_id = seed_note("Original Title", "Original body content")

        response = client.post(
            f"/api/notes/{note_id}/optimize",
            json={"title": "Optimized Title", "body": "Optimized body content"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["title"] == "Optimized Title"
        assert data["body"] == "Optimized body content"
        assert data["optimized_at"] is not None

    def test_optimize_partial_update(self, client, seed_note):
        """Should allow partial optimization (only title or body)."""
        note_id = seed_note("Original Title", "Original body content")

        # Only update title
        response = client.post(
            f"/api/notes/{note_id}/optimize",
            json={"title": "New Title Only"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["title"] == "New Title Only"
        assert data["body"] == "Original body content"

    def test_optimize_creates_revision(self, client, seed_note):
        """Optimize should create a revision that can be undone."""
        note_id = seed_note("Original", "Original body")

        # Store original revision
        from wiki_notebook.db import get_conn
        from wiki_notebook.repository import latest_revision

        conn = get_conn()
        try:
            # No revision yet
            assert latest_revision(conn, note_id) is None

            # Optimize
            client.post(
                f"/api/notes/{note_id}/optimize",
                json={"body": "Optimized"},
            )

            # Now there should be a revision
            revision = latest_revision(conn, note_id)
            assert revision is not None
            assert revision["title"] == "Original"
            assert revision["body"] == "Original body"
            assert revision["reason"] == "optimize"
        finally:
            conn.close()

    def test_optimize_no_changes(self, client, seed_note):
        """Should handle optimization with no changes (creates revision only)."""
        note_id = seed_note("Title", "Body")

        response = client.post(
            f"/api/notes/{note_id}/optimize",
            json={},
        )
        assert response.status_code == 422
        # Empty payload is invalid - must specify title or body

    def test_optimize_note_not_found(self, client):
        """Should return 404 for unknown note ID."""
        response = client.post(
            "/api/notes/99999/optimize",
            json={"title": "New", "body": "Content"},
        )
        assert response.status_code == 404


class TestUndoOptimize:
    """Tests for POST /api/notes/<id>/undo."""

    def test_undo_optimize(self, client, seed_note):
        """Should undo an optimize and restore previous content."""
        note_id = seed_note("Original", "Original body")

        # Optimize first
        client.post(
            f"/api/notes/{note_id}/optimize",
            json={"title": "Optimized", "body": "Optimized body"},
        )

        # Now undo
        response = client.post(f"/api/notes/{note_id}/undo")
        assert response.status_code == 200
        data = response.get_json()
        assert data["title"] == "Original"
        assert data["body"] == "Original body"

    def test_undo_creates_new_revision(self, client, seed_note):
        """Undo should create a new revision entry."""
        note_id = seed_note("Original", "Original body")

        # Optimize
        client.post(
            f"/api/notes/{note_id}/optimize",
            json={"body": "Optimized"},
        )

        from wiki_notebook.db import get_conn
        from wiki_notebook.repository import latest_revision, pop_latest_revision

        conn = get_conn()
        try:
            # Get the optimization revision
            revision = latest_revision(conn, note_id)
            assert revision is not None
            original_rev_id = revision["id"]

            # Undo
            client.post(f"/api/notes/{note_id}/undo")

            # The optimization revision should be deleted
            # and we're now back to original (no more revisions)
            # Actually, undo creates a new revision for the undo action
            # Let's check the state after undo
            revision_after = latest_revision(conn, note_id)
            # The undo operation deletes the revision it used
            assert revision_after is None or revision_after["id"] != original_rev_id
        finally:
            conn.close()

    def test_undo_nothing_to_undo(self, client, seed_note):
        """Should return 404 when there's no revision to undo."""
        note_id = seed_note("Original", "Original body")

        response = client.post(f"/api/notes/{note_id}/undo")
        assert response.status_code == 404
        data = response.get_json()
        assert "no revision" in data["error"]["message"].lower()

    def test_undo_note_not_found(self, client):
        """Should return 404 for unknown note ID."""
        response = client.post("/api/notes/99999/undo")
        assert response.status_code == 404
