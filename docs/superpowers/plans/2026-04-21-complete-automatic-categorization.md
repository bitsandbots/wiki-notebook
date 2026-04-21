# Complete Automatic Categorization Feature Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the automatic categorization feature by adding frontend UI, manual trigger endpoint, integration tests, and queue monitoring.

**Architecture:** The feature uses a background worker thread that processes notes asynchronously via a queue. When notes are created/updated without explicit category/tags, they're enqueued for enrichment. This plan adds: (1) frontend UI to display categories/tags and manually trigger categorization, (2) `/api/notes/<id>/categorize` endpoint for manual triggers, (3) integration tests for the worker, (4) queue monitoring and stats, (5) improved error handling and resilience.

**Tech Stack:** Flask (backend), Vanilla JavaScript (frontend), SQLite (persistence), Ollama HTTP API (AI), pytest (testing)

---

## Task 1: Add Manual Categorization API Endpoint

**Files:**
- Modify: `wiki_notebook/routes/notes.py:351-400` (add new route)
- Test: `tests/test_notes_crud.py` (add test cases)

- [ ] **Step 1: Write failing test for manual categorization endpoint**

```python
# In tests/test_notes_crud.py, add to the test class:

def test_categorize_note_with_ollama(self, mock_ollama):
    """Manually trigger categorization via API."""
    # Create a note without category
    resp = self.client.post(
        "/api/notes",
        json={"title": "Team Meeting", "body": "Discussed Q1 goals"},
    )
    note_id = resp.get_json()["id"]
    
    # Mock Ollama response
    mock_ollama.return_value.is_available.return_value = True
    mock_ollama.return_value.generate_json.return_value = {
        "category": "meetings",
        "tags": ["q1", "goals"],
    }
    
    # Trigger categorization
    resp = self.client.post(f"/api/notes/{note_id}/categorize")
    
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["category"] == "meetings"
    assert "q1" in data["tags"]

def test_categorize_nonexistent_note(self):
    """Returns 404 for nonexistent note."""
    resp = self.client.post("/api/notes/99999/categorize")
    assert resp.status_code == 404
    assert "not found" in resp.get_json()["error"]["message"]
```

Run: `pytest tests/test_notes_crud.py::TestNotesCRUD::test_categorize_note_with_ollama -v`
Expected: FAIL with "404 Client Error" (endpoint doesn't exist yet)

- [ ] **Step 2: Implement the categorize endpoint**

In `wiki_notebook/routes/notes.py`, add after the `combine_notes_route()` function (around line 350):

```python
@notes_bp.route("/<int:id>/categorize", methods=["POST"])
def categorize_note_route(id):
    """Manually trigger categorization for a note.
    
    Re-categorizes the note using Ollama if available, or keyword fallback.
    Updates category and tags, preserving other note fields.
    """
    from ..ai.categorize import categorize as categorize_note
    
    conn = get_conn()
    try:
        note = get_note(conn, id)
        if not note:
            return (
                jsonify({"error": {"code": "not_found", "message": "note not found"}}),
                404,
            )
        
        # Run categorization
        result = categorize_note(note["title"], note["body"])
        
        # Update the note with new category and tags
        update_payload = {
            "category": result["category"],
            "tags": result["tags"],
        }
        updated_note = update_note(conn, id, update_payload)
        
        return jsonify(updated_note), 200
    finally:
        conn.close()
```

- [ ] **Step 3: Run tests to verify implementation**

Run: `pytest tests/test_notes_crud.py::TestNotesCRUD::test_categorize_note_with_ollama -v`
Expected: PASS

Also run: `pytest tests/test_notes_crud.py::TestNotesCRUD::test_categorize_nonexistent_note -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add wiki_notebook/routes/notes.py tests/test_notes_crud.py
git commit -m "feat(api): add POST /api/notes/<id>/categorize endpoint"
```

---

## Task 2: Add Integration Tests for Enrichment Worker

**Files:**
- Create: `tests/test_enrichment_worker.py`
- Modify: `tests/conftest.py` (add fixtures if needed)
- Test: Integration of worker thread + database updates

- [ ] **Step 1: Write integration test for worker**

Create `tests/test_enrichment_worker.py`:

```python
"""Integration tests for the enrichment worker."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch
import pytest
import sqlite3

from wiki_notebook.ai.worker import EnrichmentWorker
from wiki_notebook.ai.ollama_client import OllamaClient
from wiki_notebook.config import config
from wiki_notebook.repository import create_note, get_note


class TestEnrichmentWorker:
    """Tests for EnrichmentWorker background processing."""

    def test_worker_processes_enqueued_notes(self, db_conn):
        """Worker processes notes from the queue."""
        # Create a mock repository
        class MockRepo:
            def get_note(self, conn, note_id):
                return get_note(conn, note_id)
            
            def update_enrichment(self, conn, note_id, category, tags):
                from wiki_notebook.repository import update_enrichment
                return update_enrichment(conn, note_id, category, tags)
        
        # Create worker
        worker = EnrichmentWorker(config, MockRepo())
        
        # Create a test note
        note = create_note(
            db_conn,
            {"title": "Team Meeting", "body": "Discussed Q1 goals", "tags": []}
        )
        note_id = note["id"]
        
        # Mock Ollama response
        with patch("wiki_notebook.ai.categorize.OllamaClient") as mock_client_class:
            mock_client = MagicMock(spec=OllamaClient)
            mock_client.is_available.return_value = True
            mock_client.generate_json.return_value = {
                "category": "meetings",
                "tags": ["q1", "goals"],
            }
            mock_client_class.return_value = mock_client
            
            # Start worker
            worker.start()
            
            # Enqueue the note
            worker.enqueue(note_id)
            
            # Wait for processing (with timeout)
            worker.q.join()
            
            # Stop worker
            worker.stop()
        
        # Verify note was updated
        updated_note = get_note(db_conn, note_id)
        assert updated_note["category"] == "meetings"
        assert "q1" in updated_note["tags"]

    def test_worker_handles_ollama_error(self, db_conn):
        """Worker falls back to keyword heuristic on Ollama error."""
        class MockRepo:
            def get_note(self, conn, note_id):
                return get_note(conn, note_id)
            
            def update_enrichment(self, conn, note_id, category, tags):
                from wiki_notebook.repository import update_enrichment
                return update_enrichment(conn, note_id, category, tags)
        
        worker = EnrichmentWorker(config, MockRepo())
        
        # Create a test note with obvious keyword
        note = create_note(
            db_conn,
            {"title": "Meeting Notes", "body": "Team discussion about timeline", "tags": []}
        )
        note_id = note["id"]
        
        # Mock Ollama to fail
        with patch("wiki_notebook.ai.categorize.OllamaClient") as mock_client_class:
            mock_client = MagicMock(spec=OllamaClient)
            mock_client.is_available.return_value = True
            mock_client.generate_json.side_effect = Exception("Ollama error")
            mock_client_class.return_value = mock_client
            
            worker.start()
            worker.enqueue(note_id)
            worker.q.join()
            worker.stop()
        
        # Should fall back to keyword matching
        updated_note = get_note(db_conn, note_id)
        assert updated_note["category"] == "meetings"  # Keyword fallback

    def test_worker_queue_full_doesnt_block(self, db_conn):
        """Enqueue doesn't block when queue is full."""
        class MockRepo:
            def get_note(self, conn, note_id):
                return get_note(conn, note_id)
            
            def update_enrichment(self, conn, note_id, category, tags):
                from wiki_notebook.repository import update_enrichment
                return update_enrichment(conn, note_id, category, tags)
        
        worker = EnrichmentWorker(config, MockRepo())
        
        # Fill the queue
        for i in range(1000):
            worker.enqueue(i)
        
        # This should not block, just silently drop the item
        worker.enqueue(1001)  # Should not raise
        
        assert True  # Test passes if no exception

    def test_worker_skips_nonexistent_note(self, db_conn):
        """Worker gracefully handles nonexistent notes."""
        class MockRepo:
            def get_note(self, conn, note_id):
                return get_note(conn, note_id)
            
            def update_enrichment(self, conn, note_id, category, tags):
                from wiki_notebook.repository import update_enrichment
                return update_enrichment(conn, note_id, category, tags)
        
        worker = EnrichmentWorker(config, MockRepo())
        worker.start()
        
        # Enqueue a note that doesn't exist
        worker.enqueue(99999)
        worker.q.join()
        worker.stop()
        
        # Should not crash, just skip it
        assert True
```

- [ ] **Step 2: Run tests to verify they work**

Run: `pytest tests/test_enrichment_worker.py -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_enrichment_worker.py
git commit -m "test: add integration tests for enrichment worker"
```

---

## Task 3: Add Queue Monitoring API Endpoint

**Files:**
- Modify: `wiki_notebook/routes/health.py` (add queue metrics)
- Modify: `wiki_notebook/ai/worker.py` (expose queue size)
- Test: `tests/test_health.py` (add test for metrics)

- [ ] **Step 1: Add queue size tracking to EnrichmentWorker**

In `wiki_notebook/ai/worker.py`, modify the `EnrichmentWorker` class:

```python
def get_queue_size(self) -> int:
    """Get current queue size (number of pending items)."""
    return self.q.qsize()

def get_stats(self) -> dict[str, int]:
    """Get worker statistics."""
    return {
        "queue_size": self.q.qsize(),
    }
```

- [ ] **Step 2: Modify health endpoint to include enrichment stats**

In `wiki_notebook/routes/health.py`, update the health check:

```python
@health_bp.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint with system status."""
    from flask import current_app
    
    # ... existing health check code ...
    
    # Add enrichment worker stats
    enrichment = None
    if "enrichment" in current_app.extensions:
        enrichment = current_app.extensions["enrichment"]
        health_data["enrichment_queue_size"] = enrichment.get_queue_size()
    
    return jsonify(health_data)
```

- [ ] **Step 3: Write test for health endpoint with enrichment stats**

In `tests/test_health.py`, add:

```python
def test_health_includes_enrichment_stats(self, client):
    """Health endpoint includes enrichment queue metrics."""
    resp = client.get("/api/health")
    
    assert resp.status_code == 200
    data = resp.get_json()
    assert "enrichment_queue_size" in data
    assert isinstance(data["enrichment_queue_size"], int)
    assert data["enrichment_queue_size"] >= 0
```

Run: `pytest tests/test_health.py::test_health_includes_enrichment_stats -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add wiki_notebook/ai/worker.py wiki_notebook/routes/health.py tests/test_health.py
git commit -m "feat: add enrichment queue metrics to health endpoint"
```

---

## Task 4: Implement Frontend UI for Category Display and Manual Categorization

**Files:**
- Modify: `static/index.html` (add category display and UI)
- Modify: `static/app.js` (add categorization logic)
- Modify: `static/styles.css` (style category badge)

- [ ] **Step 1: Update HTML to display category and tags**

In `static/index.html`, find the note display template and add category/tags section:

```html
<!-- Add this inside the note-item div, after the body content -->
<div class="note-metadata">
    <div class="category-section" id="category-section-{{id}}" style="display: none;">
        <span class="category-badge" id="category-badge-{{id}}"></span>
        <div class="tags-list" id="tags-list-{{id}}"></div>
    </div>
    <div class="enrichment-pending" id="enrichment-pending-{{id}}" style="display: none;">
        <span class="pending-indicator">Categorizing...</span>
    </div>
    <button class="btn-categorize" data-note-id="{{id}}">Re-categorize</button>
</div>
```

- [ ] **Step 2: Add JavaScript function to display categories**

In `static/app.js`, add (use safe DOM methods to prevent XSS):

```javascript
function escapeHtml(unsafe) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return unsafe.replace(/[&<>"']/g, m => map[m]);
}

function displayNoteCategory(note) {
    const categorySection = document.getElementById(`category-section-${note.id}`);
    const categoryBadge = document.getElementById(`category-badge-${note.id}`);
    const tagsList = document.getElementById(`tags-list-${note.id}`);
    const pendingIndicator = document.getElementById(`enrichment-pending-${note.id}`);
    
    if (note.category) {
        categorySection.style.display = 'block';
        categoryBadge.textContent = note.category;
        categoryBadge.className = `category-badge category-${note.category.replace(/\s+/g, '-')}`;
        
        // Display tags using safe DOM methods
        if (note.tags && note.tags.length > 0) {
            tagsList.innerHTML = '';  // Clear first
            note.tags.forEach(tag => {
                const tagEl = document.createElement('span');
                tagEl.className = 'tag';
                tagEl.textContent = tag;  // textContent is safe, prevents XSS
                tagsList.appendChild(tagEl);
            });
        }
    } else if (note.enrichment_pending) {
        pendingIndicator.style.display = 'block';
    }
}

async function recategorizeNote(noteId) {
    try {
        const resp = await fetch(`/api/notes/${noteId}/categorize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        });
        
        if (!resp.ok) {
            showError('Failed to recategorize note');
            return;
        }
        
        const note = await resp.json();
        displayNoteCategory(note);
        showSuccess('Note recategorized');
    } catch (err) {
        showError('Error recategorizing: ' + err.message);
    }
}

// Attach event listeners
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('btn-categorize')) {
        const noteId = e.target.dataset.noteId;
        recategorizeNote(noteId);
    }
});
```

- [ ] **Step 3: Add CSS styling for category display**

In `static/styles.css`, add:

```css
.note-metadata {
    margin-top: 1rem;
    padding-top: 0.75rem;
    border-top: 1px solid #ccc;
}

.category-section {
    margin-bottom: 0.5rem;
}

.category-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    background: linear-gradient(135deg, #2b7de9, #e07018);
    color: white;
    border-radius: 20px;
    font-size: 0.875rem;
    font-weight: 500;
    margin-right: 0.5rem;
}

.tags-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 0.5rem;
}

.tag {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    background: #f0f0f0;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 0.8rem;
    color: #666;
}

.enrichment-pending {
    padding: 0.5rem;
    background: #fffacd;
    border-left: 3px solid #e07018;
    font-size: 0.875rem;
    color: #666;
}

.pending-indicator::before {
    content: "⏳ ";
}

.btn-categorize {
    padding: 0.5rem 1rem;
    background: #2b7de9;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 0.875rem;
    cursor: pointer;
    margin-top: 0.5rem;
}

.btn-categorize:hover {
    background: #1e5fa3;
}
```

- [ ] **Step 4: Update note display function to show categories**

Find the function that renders notes in `app.js` and add category display:

```javascript
// In the note rendering function, after displaying note content:
displayNoteCategory(note);
```

- [ ] **Step 5: Run the app and test category display**

Run: `python -m wiki_notebook`
Expected: Server starts on http://localhost:5000

Test:
1. Create a note with title "Team Meeting" and body mentioning goals
2. Verify category badge appears or "Categorizing..." indicator shows
3. Click "Re-categorize" button
4. Verify category updates in real-time

- [ ] **Step 6: Commit**

```bash
git add static/index.html static/app.js static/styles.css
git commit -m "feat(ui): add category display and manual recategorization"
```

---

## Task 5: Improve Error Handling and Resilience

**Files:**
- Modify: `wiki_notebook/ai/worker.py` (better error logging)
- Modify: `wiki_notebook/routes/notes.py` (categorize endpoint error handling)
- Create: `tests/test_error_handling.py` (edge cases)

- [ ] **Step 1: Enhance error logging in worker**

In `wiki_notebook/ai/worker.py`, update `_run()` method:

```python
def _run(self) -> None:
    """Background worker loop with enhanced error handling."""
    from ..ai.categorize import categorize
    from ..ai.ollama_client import OllamaClient
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info("Enrichment worker started")
    
    while not self._shutdown:
        try:
            note_id = self.q.get(timeout=1)
        except queue.Empty:
            continue
        
        processed = False
        conn = None
        try:
            try:
                from ..db import get_conn
                conn = get_conn()
                note = self.repository.get_note(conn, note_id)
                
                if note is None:
                    logger.debug(f"Note {note_id} not found, skipping")
                    processed = True
                    continue
                
                logger.debug(f"Enriching note {note_id}: {note['title'][:50]}")
                
                client = OllamaClient()
                result = categorize(note['title'], note['body'], client)
                
                logger.debug(f"Categorized {note_id} as '{result['category']}'")
                
                conn = get_conn()
                try:
                    self.repository.update_enrichment(
                        conn,
                        note_id,
                        result["category"],
                        result["tags"],
                    )
                finally:
                    conn.close()
                    conn = None
                
                processed = True
                logger.info(f"Enrichment succeeded for note {note_id}")
                
            except Exception as e:
                logger.exception(f"Enrichment failed for note {note_id}: {e}")
        finally:
            if conn:
                conn.close()
            if processed:
                self.q.task_done()
```

- [ ] **Step 2: Add validation to categorize endpoint**

In `wiki_notebook/routes/notes.py`, improve the `categorize_note_route()` function:

```python
@notes_bp.route("/<int:id>/categorize", methods=["POST"])
def categorize_note_route(id):
    """Manually trigger categorization for a note."""
    from ..ai.categorize import categorize as categorize_note
    
    # Validate note ID
    if not isinstance(id, int) or id < 1:
        return (
            jsonify({"error": {"code": "invalid_input", "message": "invalid note ID"}}),
            400,
        )
    
    conn = get_conn()
    try:
        note = get_note(conn, id)
        if not note:
            return (
                jsonify({"error": {"code": "not_found", "message": "note not found"}}),
                404,
            )
        
        # Validate note has content
        if not note["title"] or not note["body"]:
            return (
                jsonify({
                    "error": {
                        "code": "invalid_state",
                        "message": "note must have title and body to categorize"
                    }
                }),
                400,
            )
        
        try:
            # Run categorization
            result = categorize_note(note["title"], note["body"])
            
            # Update the note
            update_payload = {
                "category": result["category"],
                "tags": result["tags"],
            }
            updated_note = update_note(conn, id, update_payload)
            
            return jsonify(updated_note), 200
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"Categorization failed for note {id}")
            
            return (
                jsonify({
                    "error": {
                        "code": "categorization_failed",
                        "message": "Failed to categorize note: " + str(e)
                    }
                }),
                500,
            )
    finally:
        conn.close()
```

- [ ] **Step 3: Write tests for error cases**

Create `tests/test_error_handling.py`:

```python
"""Tests for error handling in categorization."""

from __future__ import annotations
from unittest.mock import patch, MagicMock
import pytest


class TestCategorizeErrorHandling:
    """Tests for categorization error handling."""

    def test_categorize_empty_note(self, client, db_conn):
        """Cannot categorize note with empty title or body."""
        from wiki_notebook.repository import create_note
        
        # Create a note with minimal content
        note = create_note(db_conn, {"title": "", "body": "content"})
        
        resp = client.post(f"/api/notes/{note['id']}/categorize")
        
        assert resp.status_code == 400
        assert "must have title and body" in resp.get_json()["error"]["message"]

    def test_categorize_invalid_note_id(self, client):
        """Invalid note ID returns 400."""
        resp = client.post("/api/notes/-1/categorize")
        assert resp.status_code == 400

    def test_categorize_handles_ollama_timeout(self, client, db_conn):
        """Gracefully handles Ollama timeout."""
        from wiki_notebook.repository import create_note
        
        note = create_note(db_conn, {"title": "Test", "body": "Content"})
        
        with patch("wiki_notebook.ai.categorize.OllamaClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.is_available.return_value = True
            mock_client.generate_json.side_effect = TimeoutError("Ollama timeout")
            mock_client_class.return_value = mock_client
            
            resp = client.post(f"/api/notes/{note['id']}/categorize")
            
            # Should succeed with fallback
            assert resp.status_code == 200
            data = resp.get_json()
            assert "category" in data
```

Run: `pytest tests/test_error_handling.py -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add wiki_notebook/ai/worker.py wiki_notebook/routes/notes.py tests/test_error_handling.py
git commit -m "feat: improve error handling and logging in categorization"
```

---

## Task 6: Run Full Test Suite and Verify Integration

**Files:**
- Test: All modified test files
- Verify: No regressions in existing tests

- [ ] **Step 1: Run full test suite**

Run: `pytest tests/ -v --tb=short`
Expected: All tests PASS (103+ tests)

- [ ] **Step 2: Run tests with coverage**

Run: `pytest tests/ --cov=wiki_notebook --cov-report=html`
Expected: Coverage remains >80%

Check HTML report: `open htmlcov/index.html` (or use your browser)
Expected: New code is covered by tests

- [ ] **Step 3: Run the app and test end-to-end**

Run: `python -m wiki_notebook`

Manual test:
1. Create a note: "Weekly Standup" with body "Discussed sprint progress"
2. Verify "enrichment_pending" indicator or category appears
3. Query `/api/health` and verify `enrichment_queue_size`
4. Click "Re-categorize" button
5. Verify category updates to "meetings"
6. Update note title to "Project Planning" and click "Re-categorize"
7. Verify category changes to "project ideas"

- [ ] **Step 4: Commit**

```bash
git add .
git commit -m "test: verify full test suite passes with categorization enhancements"
```

---

## Task 7: Documentation and User Guide

**Files:**
- Create: `docs/CATEGORIZATION.md` (feature guide)
- Modify: `README.md` (add link to categorization guide)

- [ ] **Step 1: Write categorization feature documentation**

Create `docs/CATEGORIZATION.md`:

```markdown
# Automatic Categorization

Wiki Notebook automatically categorizes notes using AI (Ollama) or keyword heuristics.

## How It Works

### Automatic Categorization (On Create/Update)

When you create a note **without** specifying category and tags, the app automatically:
1. Enqueues the note for background enrichment
2. Calls Ollama (if available) or falls back to keyword analysis
3. Updates the note with category and tags

The frontend shows a "Categorizing..." indicator until enrichment completes.

### Manual Categorization

Click the **"Re-categorize"** button on any note to manually trigger categorization, even if the note already has a category.

This is useful if you've updated the note content and want to refresh the categorization.

### Categories

The system recognizes these categories (via keyword matching or AI):

- **meetings** - Team discussions, sync meetings, calls
- **project ideas** - Features, concepts, proposals
- **journal** - Personal reflections, daily entries
- **recipes** - Cooking, meal prep, food
- **notes** - General notes, reminders, tasks
- **learning** - Study materials, tutorials, courses
- **uncategorized** - Notes that don't fit other categories

### API Endpoints

#### POST /api/notes

Create a note. If you don't provide `category` and `tags`, enrichment is enqueued:

```json
{
  "title": "Team Meeting Notes",
  "body": "Discussed Q1 roadmap and timelines"
}
```

Response: Note with `enrichment_pending: true` if enrichment is in progress.

#### POST /api/notes/<id>/categorize

Manually trigger categorization for a note:

```bash
curl -X POST http://localhost:5000/api/notes/42/categorize
```

Response: Updated note with new category and tags.

#### GET /api/notes?category=meetings

Filter notes by category. Example:

```bash
curl http://localhost:5000/api/notes?category=meetings
```

Returns all notes in the "meetings" category.

#### GET /api/health

Check enrichment queue metrics:

```bash
curl http://localhost:5000/api/health
```

Response includes `enrichment_queue_size` - number of notes pending categorization.

## Configuration

### Enabling/Disabling AI Enrichment

Ensure Ollama is running on `localhost:11434`:

```bash
ollama pull qwen2.5-coder  # or any model
ollama serve
```

If Ollama is unavailable, the app automatically falls back to keyword-based categorization.

### Customizing Categories

Edit the category keywords in `wiki_notebook/ai/categorize.py`:

```python
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "meetings": ["meeting", "call", "zoom", ...],
    "project ideas": ["project", "feature", ...],
    # ... add or modify as needed
}
```

Then restart the app for changes to take effect.

## Troubleshooting

### "Categorizing..." indicator never disappears

**Check enrichment queue status:**
```bash
curl http://localhost:5000/api/health | jq .enrichment_queue_size
```

If the queue is > 0, the worker may be overloaded. Restart the app.

### Notes always categorized as "uncategorized"

**Ollama is likely unavailable.** Verify:
```bash
curl http://localhost:11434/api/tags
```

If Ollama isn't running, switch to keyword-based categorization or start Ollama.

### Want to disable auto-categorization

Set `category` and `tags` explicitly when creating notes. The worker only processes notes without explicit categorization.
```json
{
  "title": "My Note",
  "body": "Content",
  "category": "meetings",
  "tags": ["important"]
}
```
```

- [ ] **Step 2: Update README**

In `README.md`, add a link to categorization docs in the features section:

```markdown
## Features

- 📝 Auto-categorization with AI (Ollama) or keyword fallback — [Learn more](docs/CATEGORIZATION.md)
- 🔍 Full-text search with BM25 ranking
- 🏷️ Tags and categories
- ...
```

- [ ] **Step 3: Commit documentation**

```bash
git add docs/CATEGORIZATION.md README.md
git commit -m "docs: add categorization feature guide"
```

---

## Summary

This plan completes the automatic categorization feature by:

1. ✅ Adding a manual `/api/notes/<id>/categorize` endpoint for explicit re-categorization
2. ✅ Implementing comprehensive integration tests for the background worker
3. ✅ Adding queue monitoring to the health endpoint
4. ✅ Building frontend UI to display categories and trigger manual categorization
5. ✅ Improving error handling with better logging and validation
6. ✅ Writing user-facing documentation

**Total tasks: 7 | Total commits: 7 | Estimated test count: 20+ new tests**

All code follows the project's conventions (Black formatting, type hints, pytest test structure, conventional commits).
