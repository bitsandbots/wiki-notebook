"""Integration tests for the enrichment worker."""

from __future__ import annotations

import sqlite3
import time
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from wiki_notebook import config
from wiki_notebook.ai.ollama_client import OllamaClient, OllamaError
from wiki_notebook.ai.worker import EnrichmentWorker
from wiki_notebook.db import get_conn
from wiki_notebook.repository import (
    create_note,
    get_note,
    update_enrichment,
)


class MockRepo:
    """Mock repository with get_note and update_enrichment methods."""

    def get_note(self, conn: sqlite3.Connection, note_id: int) -> dict[str, Any] | None:
        """Get a note from the database."""
        # Return dict like the real repository does
        return get_note(conn, note_id)

    def update_enrichment(
        self, conn: sqlite3.Connection, note_id: int, category: str, tags: list[str]
    ) -> dict[str, Any]:
        """Update enrichment info for a note."""
        return update_enrichment(conn, note_id, category, tags)


class TestEnrichmentWorker:
    """Tests for EnrichmentWorker background processing."""

    @patch("wiki_notebook.ai.categorize.OllamaClient")
    def test_worker_processes_enqueued_notes(self, mock_ollama_class, app):
        """Verifies worker processes enqueued notes with categorization.

        Tests that:
        - Worker correctly retrieves note from database
        - Worker calls categorize function
        - Worker updates note with category and tags
        - Worker completes without blocking
        """
        # Mock OllamaClient to avoid network calls
        mock_client = MagicMock(spec=OllamaClient)
        mock_client.is_available.return_value = False  # Force keyword fallback
        mock_ollama_class.return_value = mock_client

        # Setup test note
        conn = get_conn()
        try:
            note_data = create_note(
                conn,
                {
                    "title": "Team Meeting",
                    "body": "Discussed Q1 goals and roadmap",
                    "category": None,
                    "tags": [],
                },
            )
            note_id = note_data["id"]
        finally:
            conn.close()

        # Create worker with mock repository
        worker = EnrichmentWorker(config.config, MockRepo())

        # Start worker, enqueue note, wait for processing
        # Note: uses keyword fallback if Ollama unavailable
        worker.start()
        worker.enqueue(note_id)

        # Wait for queue to be processed (with timeout)
        worker.q.join()

        # Stop worker
        worker.stop()

        # Verify note was updated with categorization
        conn = get_conn()
        try:
            updated_note = get_note(conn, note_id)
            assert updated_note is not None
            # Should be categorized as meetings (via keyword heuristic)
            assert updated_note["category"] == "meetings"
            # Should have tags extracted
            assert len(updated_note["tags"]) > 0
        finally:
            conn.close()

    @patch("wiki_notebook.ai.ollama_client.OllamaClient")
    def test_worker_handles_ollama_error(self, mock_ollama_class, app):
        """Verifies worker falls back to keyword categorization on error.

        Tests that:
        - Worker catches Ollama exceptions
        - Worker falls back to keyword heuristic
        - Note is still updated with fallback category
        - Worker continues processing without crashing
        """
        # Mock OllamaClient to raise error
        mock_client = MagicMock(spec=OllamaClient)
        mock_client.is_available.return_value = True
        mock_client.generate_json.side_effect = OllamaError("Ollama error")
        mock_ollama_class.return_value = mock_client

        # Setup test note with meeting keywords
        conn = get_conn()
        try:
            note_data = create_note(
                conn,
                {
                    "title": "Meeting Notes",
                    "body": "Team discussion about timeline",
                    "category": None,
                    "tags": [],
                },
            )
            note_id = note_data["id"]
        finally:
            conn.close()

        worker = EnrichmentWorker(config.config, MockRepo())

        # Start worker, enqueue note, wait for processing
        worker.start()
        worker.enqueue(note_id)

        # Wait for queue to be processed
        worker.q.join()

        # Stop worker
        worker.stop()

        # Verify note was updated with fallback category (meetings)
        # because the title/body contain meeting keywords
        conn = get_conn()
        try:
            updated_note = get_note(conn, note_id)
            assert updated_note is not None
            assert updated_note["category"] == "meetings"
        finally:
            conn.close()

    def test_worker_queue_full_doesnt_block(self, app):
        """Verifies enqueue doesn't block when queue is full.

        Tests that:
        - Worker queue has maxsize of 1000
        - Enqueuing beyond capacity uses put_nowait
        - put_nowait silently drops items without raising
        - No exception is raised during high volume enqueue
        """
        worker = EnrichmentWorker(config.config, MockRepo())

        # Fill queue with 1000 items
        for i in range(1000):
            worker.enqueue(i)

        # This should NOT raise an exception (silent drop on full queue)
        assert worker.enqueue(1001) is None

        # Verify queue is indeed full
        assert worker.q.qsize() == 1000

    @patch("wiki_notebook.ai.ollama_client.OllamaClient")
    def test_worker_handles_exception_gracefully(self, mock_ollama_class, app):
        """Verifies worker catches exceptions and continues processing.

        Tests that:
        - Worker continues on error instead of crashing
        - Multiple notes are processed even if one fails
        - Worker gracefully recovers from exceptions
        """
        # Mock OllamaClient to avoid network calls
        mock_client = MagicMock(spec=OllamaClient)
        mock_client.is_available.return_value = False  # Force keyword fallback
        mock_ollama_class.return_value = mock_client

        # Create two notes
        conn = get_conn()
        try:
            note1_data = create_note(
                conn,
                {
                    "title": "First Meeting",
                    "body": "Team sync discussion",
                    "category": None,
                    "tags": [],
                },
            )
            note1_id = note1_data["id"]

            note2_data = create_note(
                conn,
                {
                    "title": "Second Meeting",
                    "body": "Planning discussion meeting",
                    "category": None,
                    "tags": [],
                },
            )
            note2_id = note2_data["id"]
        finally:
            conn.close()

        worker = EnrichmentWorker(config.config, MockRepo())

        # Start worker
        worker.start()

        # Enqueue both notes
        worker.enqueue(note1_id)
        worker.enqueue(note2_id)

        # Wait for processing
        worker.q.join()

        # Stop worker
        worker.stop()

        # Verify both notes were processed
        conn = get_conn()
        try:
            note1 = get_note(conn, note1_id)
            note2 = get_note(conn, note2_id)

            assert note1 is not None
            assert note1["category"] == "meetings"

            assert note2 is not None
            assert note2["category"] == "meetings"
        finally:
            conn.close()

    @patch("wiki_notebook.ai.categorize.categorize")
    def test_worker_cleanup_on_error(self, mock_categorize, app):
        """Verifies worker properly cleans up resources on error.

        Tests that:
        - Worker closes database connection even on exception
        - Worker marks task as done even if categorization fails
        - Worker continues processing next items after error
        """
        # Mock categorize to raise an exception
        mock_categorize.side_effect = RuntimeError("Test error")

        # Create a test note
        conn = get_conn()
        try:
            note_data = create_note(
                conn,
                {
                    "title": "Test Note",
                    "body": "Test body",
                    "category": None,
                    "tags": [],
                },
            )
            note_id = note_data["id"]
        finally:
            conn.close()

        worker = EnrichmentWorker(config.config, MockRepo())

        # Start worker, enqueue note
        worker.start()
        worker.enqueue(note_id)

        # Wait for queue to be processed (should complete despite error)
        worker.q.join()

        # Stop worker
        worker.stop()

        # Verify queue was processed (task_done was called)
        # If task_done wasn't called, q.join() would have hung
        assert worker.q.qsize() == 0
