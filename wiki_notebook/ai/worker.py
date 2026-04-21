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
        """Background worker loop with enhanced error handling."""
        from ..ai.categorize import categorize
        from ..ai.ollama_client import OllamaClient
        from ..db import get_conn
        import logging

        logger = logging.getLogger(__name__)
        logger.info("Enrichment worker started")

        while not self._shutdown:
            try:
                note_id = self.q.get(timeout=1)
            except queue.Empty:
                continue

            conn = None
            try:
                # Get note from database
                conn = get_conn()
                note = self.repository.get_note(conn, note_id)

                if note is None:
                    logger.debug(f"Note {note_id} not found, skipping")
                else:
                    logger.debug(f"Enriching note {note_id}: {note.title[:50]}")

                    # Categorize the note
                    client = OllamaClient()
                    result = categorize(note.title, note.body, client)
                    logger.debug(f"Categorized {note_id} as '{result['category']}'")

                    # Update note with enrichment results
                    self.repository.update_enrichment(
                        conn,
                        note_id,
                        result["category"],
                        result["tags"],
                    )

                    logger.info(f"Enrichment succeeded for note {note_id}")

            except Exception as e:
                logger.exception(f"Enrichment failed for note {note_id}: {e}")
            finally:
                # Always clean up connection and mark task done
                if conn:
                    conn.close()
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
