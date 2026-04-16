"""Tests for multi-select and combine functionality."""

from __future__ import annotations

import pytest


class TestCombineNotes:
    """Tests for POST /api/notes/combine."""

    def test_combine_two_notes_concatenate(self, client, seed_note):
        """Should concatenate two notes into a new combined note."""
        id1 = seed_note("Note A", "Content A")
        id2 = seed_note("Note B", "Content B")

        response = client.post(
            "/api/notes/combine",
            json={"note_ids": [id1, id2], "mode": "concatenate"},
        )
        assert response.status_code == 201
        data = response.get_json()
        assert "id" in data
        assert "Combined" in data["title"]
        assert "Note A" in data["title"]
        assert "Note B" in data["title"]
        assert "Content A" in data["body"]
        assert "Content B" in data["body"]
        assert "source_ids" in data

    def test_combine_three_notes_concatenate(self, client, seed_note):
        """Should concatenate three notes with ellipsis for longer lists."""
        id1 = seed_note("Note Alpha", "Content Alpha")
        id2 = seed_note("Note Beta", "Content Beta")
        id3 = seed_note("Note Gamma", "Content Gamma")
        id4 = seed_note("Note Delta", "Content Delta")

        response = client.post(
            "/api/notes/combine",
            json={"note_ids": [id1, id2, id3, id4], "mode": "concatenate"},
        )
        assert response.status_code == 201
        data = response.get_json()
        assert "Note Alpha" in data["title"]
        assert "Note Beta" in data["title"]
        assert "Note Gamma" in data["title"]
        assert "+1 more" in data["title"]
        assert "Content Alpha" in data["body"]

    def test_combine_with_custom_title(self, client, seed_note):
        """Should use custom title when provided."""
        id1 = seed_note("Note A", "Content A")
        id2 = seed_note("Note B", "Content B")

        response = client.post(
            "/api/notes/combine",
            json={
                "note_ids": [id1, id2],
                "mode": "concatenate",
                "title": "My Combined Note",
            },
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["title"] == "My Combined Note"

    def test_combine_mode_ai(self, client, seed_note):
        """Should combine notes with AI mode."""
        id1 = seed_note("Meeting Notes", "Discussed project timeline")
        id2 = seed_note("Action Items", "Follow up on requirements")

        response = client.post(
            "/api/notes/combine",
            json={"note_ids": [id1, id2], "mode": "ai"},
        )
        assert response.status_code == 201
        data = response.get_json()
        assert "Combined Notes (ai)" in data["body"]
        assert "Meeting Notes" in data["body"]
        assert "Action Items" in data["body"]

    def test_combine_source_ids_tracking(self, client, seed_note):
        """Should track source IDs in combined note."""
        id1 = seed_note("Source 1", "Content 1")
        id2 = seed_note("Source 2", "Content 2")

        response = client.post(
            "/api/notes/combine",
            json={"note_ids": [id1, id2], "mode": "concatenate"},
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["source_ids"] == [id1, id2]

    def test_combine_validation_missing_note_ids(self, client):
        """Should return 422 when note_ids is missing."""
        response = client.post(
            "/api/notes/combine",
            json={"mode": "concatenate"},
        )
        assert response.status_code == 422
        data = response.get_json()
        assert "note_ids" in data["error"]["message"].lower()

    def test_combine_validation_empty_note_ids(self, client):
        """Should return 422 when note_ids is empty."""
        response = client.post(
            "/api/notes/combine",
            json={"note_ids": [], "mode": "concatenate"},
        )
        assert response.status_code == 422

    def test_combine_validation_single_note(self, client):
        """Should return 422 when note_ids has only one note."""
        response = client.post(
            "/api/notes/combine",
            json={"note_ids": [1], "mode": "concatenate"},
        )
        assert response.status_code == 422

    def test_combine_validation_invalid_mode(self, client, seed_note):
        """Should return 422 for invalid mode."""
        id1 = seed_note("Note A", "Content A")
        id2 = seed_note("Note B", "Content B")

        response = client.post(
            "/api/notes/combine",
            json={"note_ids": [id1, id2], "mode": "invalid"},
        )
        assert response.status_code == 422
        data = response.get_json()
        assert "mode" in data["error"]["message"].lower()

    def test_combine_validation_title_too_long(self, client, seed_note):
        """Should return 422 when title exceeds 200 chars."""
        id1 = seed_note("Note A", "Content A")
        id2 = seed_note("Note B", "Content B")

        long_title = "A" * 201

        response = client.post(
            "/api/notes/combine",
            json={"note_ids": [id1, id2], "mode": "concatenate", "title": long_title},
        )
        assert response.status_code == 422

    def test_combine_notes_not_found(self, client):
        """Should return 404 when notes don't exist."""
        response = client.post(
            "/api/notes/combine",
            json={"note_ids": [99999, 99998], "mode": "concatenate"},
        )
        assert response.status_code == 404
