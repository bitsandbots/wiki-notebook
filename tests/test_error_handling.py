"""Tests for error handling in categorization."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest


class TestCategorizeErrorHandling:
    """Tests for categorization error handling."""

    def test_categorize_empty_title(self, client, seed_note):
        """Cannot categorize note with empty title."""
        note_id = seed_note(title="", body="content")

        resp = client.post(f"/api/notes/{note_id}/categorize")

        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "invalid_state"
        assert "must have title and body" in data["error"]["message"]

    def test_categorize_empty_body(self, client, seed_note):
        """Cannot categorize note with empty body."""
        note_id = seed_note(title="Title", body="")

        resp = client.post(f"/api/notes/{note_id}/categorize")

        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "invalid_state"
        assert "must have title and body" in data["error"]["message"]

    def test_categorize_invalid_note_id(self, client):
        """Invalid note ID returns 404 (Flask converts it to positive int)."""
        resp = client.post("/api/notes/0/categorize")
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "invalid_input"
        assert "invalid note ID" in data["error"]["message"]

    def test_categorize_nonexistent_note(self, client):
        """Nonexistent note returns 404."""
        resp = client.post("/api/notes/9999/categorize")
        assert resp.status_code == 404
        data = resp.get_json()
        assert data["error"]["code"] == "not_found"
        assert "note not found" in data["error"]["message"]

    def test_categorize_handles_categorization_error(self, client, seed_note):
        """Gracefully handles categorization errors."""
        note_id = seed_note(title="Test", body="Content")

        with patch("wiki_notebook.ai.categorize.categorize") as mock_categorize:
            mock_categorize.side_effect = RuntimeError("Categorization failed")

            resp = client.post(f"/api/notes/{note_id}/categorize")

            assert resp.status_code == 500
            data = resp.get_json()
            assert data["error"]["code"] == "categorization_failed"
            assert "Failed to categorize note" in data["error"]["message"]

    def test_categorize_success(self, client, seed_note):
        """Successful categorization updates note."""
        note_id = seed_note(title="Project Update", body="We discussed the new feature")

        with patch("wiki_notebook.ai.categorize.categorize") as mock_categorize:
            mock_categorize.return_value = {
                "category": "meetings",
                "tags": ["feature", "discussion"],
            }

            resp = client.post(f"/api/notes/{note_id}/categorize")

            assert resp.status_code == 200
            data = resp.get_json()
            assert data["category"] == "meetings"
            assert data["tags"] == ["feature", "discussion"]


class TestWorkerErrorHandling:
    """Tests for worker error handling."""

    def test_worker_initializes_without_repository(self):
        """Worker initializes even with None repository."""
        from wiki_notebook.ai.worker import EnrichmentWorker
        from wiki_notebook.config import config

        worker = EnrichmentWorker(config, None)
        assert worker.get_queue_size() == 0
        assert worker.get_stats() == {"queue_size": 0}

    def test_worker_enqueue_no_crash(self):
        """Worker accepts enqueue without crashing."""
        from wiki_notebook.ai.worker import EnrichmentWorker
        from wiki_notebook.config import config

        worker = EnrichmentWorker(config, None)
        worker.enqueue(1)
        worker.enqueue(2)
        assert worker.get_queue_size() == 2
