"""Background enrichment worker for async categorization."""

from __future__ import annotations

import queue
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..config import Config
    from ..repository import Repository


class EnrichmentWorker:
    """Background worker for async note enrichment.

    Uses a thread-backed queue to process enrichment requests without
    blocking the API responses.
    """

    def __init__(self, config: "Config", repository: "Repository"):
        """Initialize the enrichment worker.

        Args:
            config: Application configuration
            repository: Repository instance for database operations
        """
        self.config = config
        self.repository = repository
        self.q: queue.Queue[int] = queue.Queue(maxsize=1000)
        self._shutdown = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Start the background worker thread."""
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Signal the worker to stop and wait for it to finish."""
        self._shutdown = True
        if self._thread is not None:
            self._thread.join(timeout=5)

    def get_queue_size(self) -> int:
        """Get current queue size (number of pending items)."""
        return self.q.qsize()

    def get_stats(self) -> dict[str, int]:
        """Get worker statistics."""
        return {
            "queue_size": self.q.qsize(),
        }

    def enqueue(self, note_id: int) -> None:
        """Enqueue a note for enrichment.

        Args:
            note_id: ID of the note to enrich
        """
        try:
            self.q.put_nowait(note_id)
        except queue.Full:
            # Queue full - note will be enriched on next request
            pass

    def _run(self) -> None:
        """Background worker loop."""
        from ..ai.categorize import categorize
        from ..ai.ollama_client import OllamaClient

        while not self._shutdown:
            try:
                note_id = self.q.get(timeout=1)
            except queue.Empty:
                continue

            # Process the item - task_done() will be called once after completion
            # The queue tracks how many items are being processed
            processed = False
            try:
                # Get note from database
                conn = None
                try:
                    import sqlite3
                    from ..db import get_conn

                    conn = get_conn()
                    note = self.repository.get_note(conn, note_id)
                    if note is None:
                        continue

                    # Create client for this operation
                    client = OllamaClient()

                    # Categorize the note
                    result = categorize(note.title, note.body, client)

                    # Update enrichment info
                    conn = get_conn()
                    try:
                        # Update only category and tags, keep updated_at unchanged
                        self.repository.update_enrichment(
                            conn,
                            note_id,
                            result["category"],
                            result["tags"],
                        )
                    finally:
                        conn.close()
                finally:
                    if conn:
                        conn.close()
                processed = True
            except Exception:
                # Log the error but continue processing
                import logging

                logger = logging.getLogger(__name__)
                logger.exception("Enrichment failed for note %s", note_id)
            finally:
                if processed:
                    self.q.task_done()


# Helper to create enrichment info update function
def enrich_note(note_id: int, category: str, tags: list[str]) -> dict[str, Any]:
    """Create a note dict with enrichment info for testing.

    Args:
        note_id: Note ID
        category: Assigned category
        tags: Assigned tags

    Returns:
        Note dict with enrichment fields
    """
    return {
        "id": note_id,
        "category": category,
        "tags": tags,
    }
