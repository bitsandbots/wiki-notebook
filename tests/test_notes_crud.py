"""Tests for notes CRUD API."""

from __future__ import annotations

import pytest


class TestNotesList:
    """Tests for GET /api/notes."""

    def test_empty_list(self, client):
        """Should return empty list when no notes exist."""
        response = client.get("/api/notes")
        assert response.status_code == 200
        data = response.get_json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["limit"] == 50
        assert data["offset"] == 0

    def test_list_with_notes(self, client, seed_note):
        """Should return notes when they exist."""
        seed_note("Note 1", "Body 1")
        seed_note("Note 2", "Body 2")

        response = client.get("/api/notes")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["items"]) == 2
        assert data["total"] == 2
        assert data["items"][0]["title"] == "Note 2"  # new first
        assert data["items"][1]["title"] == "Note 1"

    def test_pagination(self, client, seed_note):
        """Should handle pagination."""
        for i in range(5):
            seed_note(f"Note {i}", f"Body {i}")

        # First page, limit=2
        response = client.get("/api/notes?limit=2&offset=0")
        data = response.get_json()
        assert len(data["items"]) == 2
        assert data["limit"] == 2
        assert data["offset"] == 0

        # Second page
        response = client.get("/api/notes?limit=2&offset=2")
        data = response.get_json()
        assert len(data["items"]) == 2
        assert data["offset"] == 2


class TestNotesCreate:
    """Tests for POST /api/notes."""

    def test_create_note(self, client):
        """Should create a note and return it."""
        payload = {
            "title": "New Note",
            "body": "Note body content",
            "category": "meetings",
            "tags": ["tag1", "tag2"],
        }

        response = client.post(
            "/api/notes",
            json=payload,
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["title"] == "New Note"
        assert data["body"] == "Note body content"
        assert data["category"] == "meetings"
        assert data["tags"] == ["tag1", "tag2"]
        assert data["id"] is not None

    def test_create_validation_error(self, client):
        """Should return 422 for invalid payload."""
        payload = {"title": "", "body": "body"}

        response = client.post(
            "/api/notes",
            json=payload,
            content_type="application/json",
        )
        assert response.status_code == 422
        data = response.get_json()
        assert "error" in data
        assert "title" in data["error"]["message"].lower()


class TestNotesRead:
    """Tests for GET /api/notes/<id>."""

    def test_get_note(self, client, seed_note):
        """Should return a specific note."""
        note_id = seed_note("Read Note", "Read body")

        response = client.get(f"/api/notes/{note_id}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["title"] == "Read Note"
        assert data["body"] == "Read body"

    def test_get_note_not_found(self, client):
        """Should return 404 for unknown note ID."""
        response = client.get("/api/notes/99999")
        assert response.status_code == 404


class TestNotesUpdate:
    """Tests for PUT /api/notes/<id>."""

    def test_update_note(self, client, seed_note):
        """Should update a note and return it."""
        note_id = seed_note("Original", "Original body")

        response = client.put(
            f"/api/notes/{note_id}",
            json={"title": "Updated", "body": "Updated body"},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["title"] == "Updated"
        assert data["body"] == "Updated body"

    def test_update_partial(self, client, seed_note):
        """Should allow partial updates."""
        note_id = seed_note("Title", "Body")

        response = client.put(
            f"/api/notes/{note_id}",
            json={"title": "New Title"},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["title"] == "New Title"
        assert data["body"] == "Body"  # unchanged

    def test_update_not_found(self, client):
        """Should return 404 for unknown note ID."""
        response = client.put(
            "/api/notes/99999",
            json={"title": "New"},
            content_type="application/json",
        )
        assert response.status_code == 404


class TestNotesDelete:
    """Tests for DELETE /api/notes/<id>."""

    def test_delete_note(self, client, seed_note):
        """Should delete a note and return 204."""
        note_id = seed_note("ToDelete", "Will be deleted")

        response = client.delete(f"/api/notes/{note_id}")
        assert response.status_code == 204

        # Verify it's gone
        response = client.get(f"/api/notes/{note_id}")
        assert response.status_code == 404

    def test_delete_not_found(self, client):
        """Should return 404 for unknown note ID."""
        response = client.delete("/api/notes/99999")
        assert response.status_code == 404


class TestFTS5Sync:
    """Tests for FTS5 trigger synchronization."""

    def test_insert_syncs_to_fts(self, client, seed_note):
        """Creating a note should sync to FTS5."""
        note_id = seed_note("Search Me", "Find this note")

        # Query FTS5 directly
        from wiki_notebook.db import get_conn

        conn = get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM notes_fts WHERE notes_fts MATCH 'Search'")
            results = cursor.fetchall()
            assert len(results) >= 1
        finally:
            conn.close()

    def test_delete_syncs_to_fts(self, client, seed_note):
        """Deleting a note should sync to FTS5."""
        note_id = seed_note("Delete Me", "Removed content")

        # Delete the note
        client.delete(f"/api/notes/{note_id}")

        # Verify FTS5 is updated
        from wiki_notebook.db import get_conn

        conn = get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM notes_fts WHERE notes_fts MATCH 'Delete'")
            results = cursor.fetchall()
            # Should be empty since note was deleted
            assert len(results) == 0
        finally:
            conn.close()
