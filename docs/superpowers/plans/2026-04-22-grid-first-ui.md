# Grid-First UI with Card Detail View and File Import — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure the Wiki Notebook UI so the notes grid is the primary home view, with a full-page detail view for reading/editing notes, a "+ New Note" button with import dropdown, and hybrid-chunked `.txt`/`.md` file import with a chunk-preview step before note creation.

**Architecture:** A `state.view` property (`"grid"` | `"detail"` | `"import-preview"`) drives a `renderView()` function that shows/hides the three top-level sections. All transitions are explicit via `navigateTo()`. The backend gains a `POST /api/notes/import` endpoint backed by a new `wiki_notebook/chunking.py` module.

**Tech Stack:** Python 3.13, Flask, SQLite, Vanilla JS (ES2021), Playwright UI tests, pytest

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `wiki_notebook/chunking.py` | **Create** | Hybrid chunking algorithm |
| `tests/test_chunking.py` | **Create** | Chunking unit tests |
| `tests/test_import.py` | **Create** | Import endpoint integration tests |
| `wiki_notebook/routes/notes.py` | **Modify** | Add `POST /api/notes/import` route |
| `static/index.html` | **Modify** | New Note button+dropdown, detail top bar, import-preview section, hide editor by default |
| `static/styles.css` | **Modify** | Detail top bar, dropdown, import preview card styles |
| `static/app.js` | **Modify** | `state.view`, `renderView()`, `navigateTo()`, import flow, unsaved-changes guard |
| `tests/ui/test_ui.py` | **Modify** | Update broken assertions + add view-switching and import UI tests |

---

## Task 1: Chunking Algorithm (TDD)

**Files:**
- Create: `tests/test_chunking.py`
- Create: `wiki_notebook/chunking.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_chunking.py`:

```python
"""Unit tests for the hybrid chunking algorithm."""
from __future__ import annotations

import pytest
from wiki_notebook.chunking import Chunk, chunk_file


# ── Fixtures ──────────────────────────────────────────────────────────────

SIMPLE_MD = """\
# Section One
Content for section one.

More content here.

# Section Two
Content for section two.
"""

MD_NO_HEADINGS = """\
First paragraph here with some text.

Second paragraph here with more text.

Third paragraph here to finish.
"""

TXT_PARAGRAPHS = """\
First paragraph of a plain text file.

Second paragraph of a plain text file.

Third paragraph of a plain text file.
"""

MD_DEEP_HEADINGS = """\
# Top Level
Intro content.

## Sub Section
Sub content.

### Deep Section
Deep content.
"""

MD_PREAMBLE = """\
This is preamble content before any heading.

# Section One
Content for section one.
"""

MD_ONLY_HEADINGS = """\
# Empty One

# Empty Two
"""

WINDOWS_ENDINGS = "# Title\r\nContent here.\r\n\r\n# Title Two\r\nMore content.\r\n"

UNICODE_MD = "# Unïcode Heading\nContent with special chars."


# ── Heading-based splitting ────────────────────────────────────────────────

class TestMarkdownHeadingSplit:
    def test_splits_on_h1_headings(self):
        chunks = chunk_file(SIMPLE_MD, "test.md")
        assert len(chunks) == 2
        assert chunks[0].title == "Section One"
        assert chunks[1].title == "Section Two"

    def test_body_contains_correct_content(self):
        chunks = chunk_file(SIMPLE_MD, "test.md")
        assert "Content for section one." in chunks[0].body
        assert "Content for section two." in chunks[1].body

    def test_splits_on_all_heading_levels(self):
        chunks = chunk_file(MD_DEEP_HEADINGS, "test.md")
        titles = [c.title for c in chunks]
        assert "Top Level" in titles
        assert "Sub Section" in titles
        assert "Deep Section" in titles

    def test_preamble_becomes_first_chunk(self):
        chunks = chunk_file(MD_PREAMBLE, "test.md")
        assert chunks[0].body.strip() == "This is preamble content before any heading."
        assert any(c.title == "Section One" for c in chunks)

    def test_source_file_set_on_each_chunk(self):
        chunks = chunk_file(SIMPLE_MD, "test.md")
        assert all(c.source_file == "test.md" for c in chunks)

    def test_index_is_sequential(self):
        chunks = chunk_file(SIMPLE_MD, "test.md")
        assert [c.index for c in chunks] == list(range(len(chunks)))

    def test_returns_chunk_namedtuple(self):
        chunks = chunk_file(SIMPLE_MD, "test.md")
        assert isinstance(chunks[0], Chunk)
        assert hasattr(chunks[0], "title")
        assert hasattr(chunks[0], "body")
        assert hasattr(chunks[0], "source_file")
        assert hasattr(chunks[0], "index")

    def test_windows_line_endings(self):
        chunks = chunk_file(WINDOWS_ENDINGS, "test.md")
        assert len(chunks) == 2
        assert chunks[0].title == "Title"

    def test_unicode_headings(self):
        chunks = chunk_file(UNICODE_MD, "test.md")
        assert chunks[0].title == "Unïcode Heading"


# ── Paragraph fallback ─────────────────────────────────────────────────────

class TestParagraphFallback:
    def test_md_no_headings_splits_on_paragraphs(self):
        chunks = chunk_file(MD_NO_HEADINGS, "test.md")
        assert len(chunks) >= 1
        combined = " ".join(c.body for c in chunks)
        assert "First paragraph" in combined
        assert "Second paragraph" in combined
        assert "Third paragraph" in combined

    def test_txt_splits_on_paragraphs(self):
        chunks = chunk_file(TXT_PARAGRAPHS, "test.txt")
        combined = " ".join(c.body for c in chunks)
        assert "First paragraph" in combined
        assert "Third paragraph" in combined

    def test_txt_titles_use_filename(self):
        chunks = chunk_file(TXT_PARAGRAPHS, "notes.txt")
        assert all("notes.txt" in c.title for c in chunks)

    def test_no_newlines_falls_back_to_word_split(self):
        content = "word " * 600  # ~3000 chars, no newlines
        chunks = chunk_file(content, "test.txt")
        assert len(chunks) >= 2
        assert all(c.body for c in chunks)


# ── Oversized chunks ───────────────────────────────────────────────────────

class TestOversizedChunks:
    def test_oversized_section_is_sub_split(self):
        big_body = "word " * 500  # ~2500 chars
        big_md = f"# Big Section\n{big_body}"
        chunks = chunk_file(big_md, "test.md")
        assert all(len(c.body) <= 2200 for c in chunks)

    def test_sub_split_titles_include_part_number(self):
        big_body = "word " * 500
        big_md = f"# Big Section\n{big_body}"
        chunks = chunk_file(big_md, "test.md")
        assert len(chunks) > 1
        assert any("Part" in c.title for c in chunks)


# ── Tiny chunk merging ─────────────────────────────────────────────────────

class TestTinyChunkMerging:
    def test_tiny_chunk_merged_into_previous(self):
        md = "# Real Section\nThis section has real content.\n\n# Tiny\nHi\n"
        chunks = chunk_file(md, "test.md")
        tiny_standalone = any(c.body.strip() == "Hi" for c in chunks)
        assert not tiny_standalone

    def test_only_headings_no_body_returns_non_empty_chunks(self):
        chunks = chunk_file(MD_ONLY_HEADINGS, "test.md")
        assert all(c.body.strip() for c in chunks)


# ── Empty / edge cases ─────────────────────────────────────────────────────

class TestEdgeCases:
    def test_empty_file_returns_empty_list(self):
        chunks = chunk_file("", "test.md")
        assert chunks == []

    def test_whitespace_only_returns_empty_list(self):
        chunks = chunk_file("   \n\n   ", "test.txt")
        assert chunks == []

    def test_single_line_no_newline(self):
        chunks = chunk_file("Just one line.", "test.txt")
        assert len(chunks) == 1
        assert "Just one line." in chunks[0].body
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd /home/coreconduit/wiki-notebook
pytest tests/test_chunking.py -q 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'wiki_notebook.chunking'`

- [ ] **Step 3: Create `wiki_notebook/chunking.py`**

```python
"""Hybrid file chunking algorithm for .txt and .md import."""
from __future__ import annotations

import re
from typing import NamedTuple

MAX_CHUNK_SIZE = 2000
MIN_CHUNK_SIZE = 50


class Chunk(NamedTuple):
    title: str
    body: str
    source_file: str
    index: int


def chunk_file(content: str, filename: str) -> list[Chunk]:
    """Dispatch to the right chunker based on file extension.

    Args:
        content: Raw file text.
        filename: Original filename (used for titles and extension detection).

    Returns:
        List of Chunk namedtuples ordered by appearance.
    """
    if not content or not content.strip():
        return []

    content = content.replace("\r\n", "\n").replace("\r", "\n")

    if filename.lower().endswith(".md"):
        return _chunk_markdown(content, filename)
    return _chunk_by_paragraphs(content, filename)


def _chunk_markdown(content: str, filename: str) -> list[Chunk]:
    """Split on ATX headings (#...######). Falls back to paragraphs if none found."""
    heading_re = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)
    matches = list(heading_re.finditer(content))

    if not matches:
        return _chunk_by_paragraphs(content, filename)

    pairs: list[tuple[str, str]] = []

    if matches[0].start() > 0:
        preamble = content[: matches[0].start()].strip()
        if preamble:
            pairs.append((f"{filename} - Preamble", preamble))

    for i, match in enumerate(matches):
        title = match.group(1).strip()
        body_start = match.end() + 1
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body = content[body_start:body_end].strip()
        pairs.append((title, body))

    return _finalize_chunks(pairs, filename)


def _chunk_by_paragraphs(content: str, filename: str) -> list[Chunk]:
    """Split on double newlines (blank lines). Falls back to word-boundary split."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", content) if p.strip()]

    if not paragraphs:
        return []

    groups: list[str] = []
    current: list[str] = []
    current_len = 0

    for para in paragraphs:
        if current and current_len + len(para) > MAX_CHUNK_SIZE:
            groups.append("\n\n".join(current))
            current = [para]
            current_len = len(para)
        else:
            current.append(para)
            current_len += len(para)

    if current:
        groups.append("\n\n".join(current))

    pairs = [(f"{filename} - Part {i + 1}", g) for i, g in enumerate(groups)]
    return _finalize_chunks(pairs, filename)


def _finalize_chunks(pairs: list[tuple[str, str]], filename: str) -> list[Chunk]:
    """Sub-split oversized chunks, merge tiny ones, assign sequential indices."""
    expanded: list[tuple[str, str]] = []
    for title, body in pairs:
        if len(body) > MAX_CHUNK_SIZE:
            sub_bodies = _sub_split(body)
            for j, sub in enumerate(sub_bodies):
                expanded.append((f"{title} - Part {j + 1}", sub))
        else:
            expanded.append((title, body))

    merged: list[tuple[str, str]] = []
    for title, body in expanded:
        if body and len(body) < MIN_CHUNK_SIZE and merged:
            prev_title, prev_body = merged[-1]
            merged[-1] = (prev_title, f"{prev_body}\n\n{body}")
        else:
            merged.append((title, body))

    return [
        Chunk(title=t, body=b, source_file=filename, index=i)
        for i, (t, b) in enumerate(merged)
        if b.strip()
    ]


def _sub_split(body: str) -> list[str]:
    """Split an oversized body at paragraph or word boundaries."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]

    if len(paragraphs) > 1:
        groups: list[str] = []
        current: list[str] = []
        current_len = 0
        for para in paragraphs:
            if current and current_len + len(para) > MAX_CHUNK_SIZE:
                groups.append("\n\n".join(current))
                current = [para]
                current_len = len(para)
            else:
                current.append(para)
                current_len += len(para)
        if current:
            groups.append("\n\n".join(current))
        return groups

    result: list[str] = []
    remaining = body
    while len(remaining) > MAX_CHUNK_SIZE:
        split_at = remaining.rfind(" ", 0, MAX_CHUNK_SIZE)
        if split_at == -1:
            split_at = MAX_CHUNK_SIZE
        result.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    if remaining:
        result.append(remaining)
    return result
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_chunking.py -q
```

Expected: all passing

- [ ] **Step 5: Commit**

```bash
git add wiki_notebook/chunking.py tests/test_chunking.py
git commit -m "feat(chunking): add hybrid file chunking algorithm"
```

---

## Task 2: Import Endpoint (TDD)

**Files:**
- Create: `tests/test_import.py`
- Modify: `wiki_notebook/routes/notes.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_import.py`:

```python
"""Integration tests for POST /api/notes/import endpoint."""
from __future__ import annotations

import io
import pytest


def _upload(client, files: list[tuple[str, bytes, str]]):
    """POST files to /api/notes/import."""
    file_list = [(io.BytesIO(content), name, mime) for name, content, mime in files]
    return client.post(
        "/api/notes/import",
        data={"files": file_list},
        content_type="multipart/form-data",
    )


class TestImportEndpoint:
    def test_valid_md_returns_chunks(self, client):
        md = b"# Section One\nBody one.\n\n# Section Two\nBody two.\n"
        resp = _upload(client, [("test.md", md, "text/markdown")])
        assert resp.status_code == 200
        result = resp.get_json()
        assert "chunks" in result
        assert len(result["chunks"]) == 2

    def test_chunk_has_required_fields(self, client):
        md = b"# Title\nBody content here.\n"
        resp = _upload(client, [("doc.md", md, "text/markdown")])
        chunk = resp.get_json()["chunks"][0]
        assert "title" in chunk
        assert "body" in chunk
        assert "source_file" in chunk
        assert "index" in chunk

    def test_chunk_title_matches_heading(self, client):
        md = b"# My Heading\nSome body.\n"
        resp = _upload(client, [("test.md", md, "text/markdown")])
        assert resp.get_json()["chunks"][0]["title"] == "My Heading"

    def test_valid_txt_returns_chunks(self, client):
        txt = b"First paragraph here.\n\nSecond paragraph here.\n"
        resp = _upload(client, [("notes.txt", txt, "text/plain")])
        assert resp.status_code == 200
        assert len(resp.get_json()["chunks"]) >= 1

    def test_multi_file_returns_all_chunks(self, client):
        md1 = b"# A\nBody A.\n"
        md2 = b"# B\nBody B.\n# C\nBody C.\n"
        resp = _upload(client, [
            ("file1.md", md1, "text/markdown"),
            ("file2.md", md2, "text/markdown"),
        ])
        assert resp.status_code == 200
        assert len(resp.get_json()["chunks"]) == 3

    def test_multi_file_source_file_preserved(self, client):
        resp = _upload(client, [
            ("alpha.md", b"# A\nBody.\n", "text/markdown"),
            ("beta.md", b"# B\nBody.\n", "text/markdown"),
        ])
        sources = {c["source_file"] for c in resp.get_json()["chunks"]}
        assert "alpha.md" in sources
        assert "beta.md" in sources

    def test_unsupported_file_type_returns_400(self, client):
        resp = _upload(client, [("doc.pdf", b"%PDF fake content", "application/pdf")])
        assert resp.status_code == 400
        assert "error" in resp.get_json()

    def test_no_files_returns_400(self, client):
        resp = client.post(
            "/api/notes/import", data={}, content_type="multipart/form-data"
        )
        assert resp.status_code == 400

    def test_empty_md_returns_400(self, client):
        resp = _upload(client, [("empty.md", b"", "text/markdown")])
        assert resp.status_code == 400

    def test_notes_not_created_in_db(self, client):
        """Import endpoint must NOT create notes."""
        _upload(client, [("test.md", b"# Title\nBody.\n", "text/markdown")])
        list_resp = client.get("/api/notes")
        assert list_resp.get_json()["total"] == 0

    def test_unicode_content_handled(self, client):
        md = "# Tïtle\nContent.".encode("utf-8")
        resp = _upload(client, [("unicode.md", md, "text/markdown")])
        assert resp.status_code == 200
        assert resp.get_json()["chunks"][0]["title"] == "Tïtle"
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_import.py -q 2>&1 | head -15
```

Expected: `404 NOT FOUND` responses

- [ ] **Step 3: Add import route to `wiki_notebook/routes/notes.py`**

Add to the top-level imports (after the existing imports):

```python
from werkzeug.utils import secure_filename
from ..chunking import chunk_file
```

Add this route immediately after the `notes_bp = Blueprint(...)` line and before the first `@notes_bp.route` decorator:

```python
@notes_bp.route("/import", methods=["POST"])
def import_notes_route():
    """Parse uploaded files and return proposed chunks without creating notes."""
    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "No files uploaded"}), 400

    chunks = []
    for file in files:
        raw_name = file.filename or "unknown"
        filename = secure_filename(raw_name)
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if ext not in ("md", "txt"):
            continue

        raw = file.read()
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError:
            content = raw.decode("latin-1", errors="replace")

        file_chunks = chunk_file(content, filename)
        chunks.extend([c._asdict() for c in file_chunks])

    if not chunks:
        return jsonify({"error": "No valid .txt or .md files found"}), 400

    return jsonify({"chunks": chunks}), 200
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_import.py -q
```

Expected: `11 passed`

- [ ] **Step 5: Run full backend suite**

```bash
pytest tests/ -q --ignore=tests/ui -x
```

Expected: all passing

- [ ] **Step 6: Commit**

```bash
git add wiki_notebook/routes/notes.py wiki_notebook/chunking.py tests/test_import.py
git commit -m "feat(api): add POST /api/notes/import endpoint"
```

---

## Task 3: HTML Structural Changes

**Files:**
- Modify: `static/index.html`

- [ ] **Step 1: Hide the editor container by default**

Find `<section id="editor-container"` and add `style="display: none"`:

```html
<section
  id="editor-container"
  class="editor-container"
  aria-label="Note editor"
  style="display: none"
>
```

- [ ] **Step 2: Add detail top bar as the first child inside `#editor-container`**

Add immediately after the opening `<section id="editor-container" ...>` tag:

```html
<div class="detail-topbar">
  <button
    type="button"
    id="detail-back-btn"
    class="btn btn-link detail-back"
    aria-label="Back to notes list"
  >
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
         aria-hidden="true" width="16" height="16">
      <polyline points="15 18 9 12 15 6" />
    </svg>
    Notes
  </button>
  <button
    type="button"
    id="detail-close-btn"
    class="btn btn-link detail-close"
    aria-label="Close note"
  >
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
         aria-hidden="true" width="16" height="16">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  </button>
</div>
```

- [ ] **Step 3: Add "+ New Note" button with dropdown to the header**

Find `<div class="header-a11y-controls">` and insert the new-note group **before** it:

```html
<div class="new-note-group" style="position: relative">
  <button
    type="button"
    id="new-note-btn"
    class="btn btn-primary btn-new-note"
    aria-label="Create new note"
  >
    + New Note
  </button>
  <button
    type="button"
    id="new-note-caret"
    class="btn btn-primary btn-new-note-caret"
    aria-label="More creation options"
    aria-expanded="false"
    aria-haspopup="true"
  >
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
         aria-hidden="true" width="12" height="12">
      <polyline points="6 9 12 15 18 9" />
    </svg>
  </button>
  <ul
    id="new-note-menu"
    class="new-note-menu"
    role="menu"
    aria-label="Creation options"
    style="display: none"
  >
    <li role="none">
      <button
        type="button"
        id="import-file-btn"
        class="new-note-menu-item"
        role="menuitem"
      >
        Import from file…
      </button>
    </li>
  </ul>
  <input
    type="file"
    id="import-file-input"
    accept=".txt,.md"
    multiple
    style="display: none"
    aria-hidden="true"
  />
</div>
```

- [ ] **Step 4: Add import preview section inside `.page-content`**

Add after the closing `</section>` tag of `#editor-container` and before `#notes-list-container`:

```html
<section
  id="import-preview-container"
  class="import-preview-container"
  aria-label="Import preview"
  style="display: none"
>
  <div class="detail-topbar">
    <button
      type="button"
      id="import-cancel-top-btn"
      class="btn btn-link detail-back"
      aria-label="Cancel import"
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
           aria-hidden="true" width="16" height="16">
        <polyline points="15 18 9 12 15 6" />
      </svg>
      Cancel
    </button>
  </div>
  <div id="import-preview-header" class="import-preview-header"></div>
  <div id="import-chunk-list" class="import-chunk-list"></div>
  <div class="import-preview-actions">
    <button type="button" id="import-confirm-btn" class="btn btn-primary">
      Import Selected
    </button>
    <button type="button" id="import-cancel-bottom-btn" class="btn btn-secondary">
      Cancel
    </button>
  </div>
</section>
```

- [ ] **Step 5: Commit**

```bash
git add static/index.html
git commit -m "feat(ui): add grid-first HTML structure and import preview section"
```

---

## Task 4: CSS — New Styles

**Files:**
- Modify: `static/styles.css`

- [ ] **Step 1: Append all new styles at the end of `static/styles.css`**

```css
/* ── New Note button group ───────────────────────────────────────────────── */
.new-note-group {
  display: flex;
  align-items: stretch;
  gap: 0;
  flex-shrink: 0;
}

.btn-new-note {
  border-radius: var(--cc-radius-sm) 0 0 var(--cc-radius-sm);
  border-right: 1px solid var(--cc-blue-600);
  white-space: nowrap;
  font-size: 0.78rem;
  padding: 0.4rem 0.85rem;
  min-height: 36px;
}

.btn-new-note-caret {
  border-radius: 0 var(--cc-radius-sm) var(--cc-radius-sm) 0;
  padding: 0.4rem 0.55rem;
  min-height: 36px;
}

.new-note-menu {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  min-width: 180px;
  background: var(--cc-bg-elevated);
  border: 1px solid var(--cc-border);
  border-radius: var(--cc-radius-sm);
  box-shadow: var(--cc-shadow-elevated);
  list-style: none;
  z-index: 200;
  padding: 0.25rem 0;
}

.new-note-menu-item {
  width: 100%;
  text-align: left;
  background: none;
  border: none;
  padding: 0.6rem 1rem;
  font-family: var(--cc-font-body);
  font-size: 0.85rem;
  color: var(--cc-text-primary);
  cursor: pointer;
  display: block;
}

.new-note-menu-item:hover {
  background: var(--cc-blue-glow);
  color: var(--cc-blue-600);
}

/* ── Detail view top bar ─────────────────────────────────────────────────── */
.detail-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--cc-border-subtle);
}

.detail-back {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.82rem;
  padding: 0.3rem 0;
  text-decoration: none;
}

.detail-back:hover {
  text-decoration: none;
}

.detail-close {
  padding: 0.3rem;
  color: var(--cc-text-muted);
  border: 1px solid transparent;
  border-radius: var(--cc-radius-sm);
  display: inline-flex;
  align-items: center;
}

.detail-close:hover {
  color: var(--cc-error);
  border-color: var(--cc-border-subtle);
  background: var(--cc-error-bg);
  text-decoration: none;
}

/* ── Import preview ──────────────────────────────────────────────────────── */
.import-preview-container {
  background: var(--cc-bg-card);
  border: 1px solid var(--cc-border-subtle);
  border-radius: var(--cc-radius-md);
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: var(--cc-shadow-card);
}

.import-preview-header {
  margin-bottom: 1rem;
}

.import-chunk-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
  max-height: 60vh;
  overflow-y: auto;
}

.import-source-heading {
  font-family: var(--cc-font-mono);
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--cc-text-faint);
  margin: 0.5rem 0 0.25rem;
}

.import-chunk-card {
  background: var(--cc-bg-elevated);
  border: 1px solid var(--cc-border-subtle);
  border-radius: var(--cc-radius-sm);
  padding: 0.75rem 1rem;
  overflow: hidden;
}

.import-chunk-card::before {
  content: "";
  display: block;
  height: 3px;
  background: linear-gradient(90deg, var(--cc-blue-500), var(--cc-orange-500));
  margin: -0.75rem -1rem 0.75rem;
}

.import-chunk-label {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 0.4rem;
}

.import-chunk-label input[type="checkbox"] {
  accent-color: var(--cc-blue-500);
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  cursor: pointer;
}

.import-chunk-title {
  flex: 1;
  font-family: var(--cc-font-display);
  font-size: 0.9rem;
  font-weight: 600;
  background: transparent;
  border: none;
  border-bottom: 1px dashed var(--cc-border-subtle);
  color: var(--cc-text-primary);
  padding: 0.15rem 0;
  outline: none;
}

.import-chunk-title:focus {
  border-bottom-color: var(--cc-blue-500);
}

.import-chunk-preview {
  font-size: 0.8rem;
  color: var(--cc-text-muted);
  line-height: 1.5;
  margin: 0.25rem 0;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.import-chunk-charcount {
  font-family: var(--cc-font-mono);
  font-size: 0.65rem;
  color: var(--cc-text-faint);
  display: block;
  text-align: right;
}

.import-preview-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  padding-top: 1rem;
  border-top: 1px solid var(--cc-border-subtle);
}
```

- [ ] **Step 2: Commit**

```bash
git add static/styles.css
git commit -m "style(ui): add detail topbar, dropdown, and import preview styles"
```

---

## Task 5: JS — State Machine and View Rendering

**Files:**
- Modify: `static/app.js`

- [ ] **Step 1: Add `view`, `hasUnsavedChanges`, `importChunks` to `state`**

Find the end of the `const state = {` block (the `isPreviewMode` line) and add:

```javascript
  isPreviewMode: false, // true = viewing rendered markdown, false = editing
  view: "grid",         // "grid" | "detail" | "import-preview"
  hasUnsavedChanges: false,
  importChunks: [],     // proposed chunks from /api/notes/import
};
```

- [ ] **Step 2: Add `renderView()`, `confirmLeaveEdit()`, and `navigateTo()` after the `state` block**

```javascript
function renderView() {
  const gridEl = document.getElementById("notes-list-container");
  const detailEl = document.getElementById("editor-container");
  const importEl = document.getElementById("import-preview-container");

  if (gridEl) gridEl.style.display = state.view === "grid" ? "" : "none";
  if (detailEl) detailEl.style.display = state.view === "detail" ? "" : "none";
  if (importEl) importEl.style.display = state.view === "import-preview" ? "" : "none";
}

function confirmLeaveEdit() {
  if (state.hasUnsavedChanges) {
    return confirm("You have unsaved changes. Discard?");
  }
  return true;
}

function navigateTo(view) {
  state.view = view;
  if (view === "grid") {
    state.currentId = null;
    state.hasUnsavedChanges = false;
    renderApp();
  }
  renderView();
}
```

- [ ] **Step 3: Call `renderView()` at the end of `init()`**

At the very end of the `init()` function, just before `console.log("Wiki Notebook initialized")`:

```javascript
  renderView();
```

- [ ] **Step 4: Expose `navigateTo` on window**

At the bottom of `app.js` with the other `window.` exports:

```javascript
window.navigateTo = navigateTo;
```

- [ ] **Step 5: Commit**

```bash
git add static/app.js
git commit -m "feat(ui): add view state machine and renderView()"
```

---

## Task 6: JS — Detail View Behavior

**Files:**
- Modify: `static/app.js`

- [ ] **Step 1: Track unsaved changes on title and body input**

In `init()`, after the `// Event listeners` comment block, add:

```javascript
  const titleInput = document.getElementById("note-title");
  const bodyTextarea = document.getElementById("note-body");
  if (titleInput) {
    titleInput.addEventListener("input", () => {
      if (state.view === "detail" && !state.isPreviewMode) {
        state.hasUnsavedChanges = true;
      }
    });
  }
  if (bodyTextarea) {
    bodyTextarea.addEventListener("input", () => {
      if (state.view === "detail" && !state.isPreviewMode) {
        state.hasUnsavedChanges = true;
      }
    });
  }
```

- [ ] **Step 2: Wire back and close buttons in `init()`**

```javascript
  document.getElementById("detail-back-btn")?.addEventListener("click", () => {
    if (confirmLeaveEdit()) navigateTo("grid");
  });
  document.getElementById("detail-close-btn")?.addEventListener("click", () => {
    if (confirmLeaveEdit()) navigateTo("grid");
  });
```

- [ ] **Step 3: Replace the Escape block in `handleKeydown()`**

Find the `if (e.key === "Escape")` block and replace it entirely with:

```javascript
  if (e.key === "Escape") {
    const searchInput = document.getElementById("search-input");
    if (searchInput?.value && searchInput === document.activeElement) {
      searchInput.value = "";
      renderApp();
    } else if (state.view === "detail") {
      if (confirmLeaveEdit()) navigateTo("grid");
    } else if (state.view === "import-preview") {
      navigateTo("grid");
    }
  }
```

- [ ] **Step 4: Update `viewNote()` to use state machine**

In `viewNote()`, replace the final `switchToPreviewMode()` call and the `scrollIntoView()` call with:

```javascript
    state.hasUnsavedChanges = false;
    switchToPreviewMode();
    navigateTo("detail");
```

(Remove the `scrollIntoView` line — not needed when we replace the full view.)

- [ ] **Step 5: Update `editNote()` to use state machine**

In `editNote()`, replace `switchToEditMode()` and `scrollIntoView()` with:

```javascript
    state.hasUnsavedChanges = false;
    switchToEditMode();
    navigateTo("detail");
```

- [ ] **Step 6: Update `handleSave()` — stay in detail, reset unsaved flag**

In `handleSave()`, inside the `.then((note) => { ... })` callback, replace `alert("Note saved!")` and `renderApp()` with:

```javascript
      state.currentId = note.id;
      state.hasUnsavedChanges = false;
      renderApp();
      api.categories().then((data) => renderCategories(data.items, state.category));
      displayEditorCategory(note);
      switchToPreviewMode();
```

- [ ] **Step 7: Update `handleDelete()` — navigate to grid**

Replace the entire `.then()` callback in `handleDelete()` with:

```javascript
  api.remove(state.currentId).then(() => {
    navigateTo("grid");
    api.categories().then((data) => renderCategories(data.items, state.category));
  });
```

- [ ] **Step 8: Update preview toggle to reset unsaved flag on entering preview**

Find the `previewToggle.addEventListener("click", ...)` block and update:

```javascript
  if (previewToggle) {
    previewToggle.addEventListener("click", function () {
      if (state.isPreviewMode) {
        switchToEditMode();
      } else {
        state.hasUnsavedChanges = false;
        switchToPreviewMode();
      }
    });
  }
```

- [ ] **Step 9: Commit**

```bash
git add static/app.js
git commit -m "feat(ui): wire detail view back/close, unsaved-changes guard, save flow"
```

---

## Task 7: JS — New Note Button and Dropdown

**Files:**
- Modify: `static/app.js`

- [ ] **Step 1: Add new note handler and dropdown toggle in `init()`**

Add after the `// Save button` wiring:

```javascript
  // New Note button
  document.getElementById("new-note-btn")?.addEventListener("click", () => {
    state.currentId = null;
    state.hasUnsavedChanges = false;
    const ids = [
      "note-title", "note-body", "delete-btn", "undo-btn",
      "categorize-btn", "editor-category-section", "editor-enrichment-pending",
    ];
    for (const id of ids) {
      const el = document.getElementById(id);
      if (!el) continue;
      if (id === "note-title" || id === "note-body") {
        el.value = "";
      } else {
        el.style.display = "none";
      }
    }
    switchToEditMode();
    navigateTo("detail");
  });

  // Dropdown caret
  const caretBtn = document.getElementById("new-note-caret");
  const noteMenu = document.getElementById("new-note-menu");
  if (caretBtn && noteMenu) {
    caretBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      const isOpen = noteMenu.style.display !== "none";
      noteMenu.style.display = isOpen ? "none" : "block";
      caretBtn.setAttribute("aria-expanded", isOpen ? "false" : "true");
    });
    document.addEventListener("click", () => {
      if (noteMenu.style.display !== "none") {
        noteMenu.style.display = "none";
        caretBtn.setAttribute("aria-expanded", "false");
      }
    });
  }

  // Import menu item — open file picker
  document.getElementById("import-file-btn")?.addEventListener("click", () => {
    if (noteMenu) {
      noteMenu.style.display = "none";
      caretBtn?.setAttribute("aria-expanded", "false");
    }
    document.getElementById("import-file-input")?.click();
  });
```

- [ ] **Step 2: Commit**

```bash
git add static/app.js
git commit -m "feat(ui): add new note button and import dropdown"
```

---

## Task 8: JS — Import Flow

**Files:**
- Modify: `static/app.js`

- [ ] **Step 1: Add import helper functions after `navigateTo()`**

```javascript
async function uploadForChunking(files) {
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }
  const response = await fetch("/api/notes/import", {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.error || "Import failed");
  }
  return response.json();
}

function renderImportPreview(data, files) {
  state.importChunks = data.chunks;

  const headerEl = document.getElementById("import-preview-header");
  const listEl = document.getElementById("import-chunk-list");
  if (!headerEl || !listEl) return;

  headerEl.replaceChildren();
  const heading = document.createElement("h2");
  heading.className = "section-title";
  const fileNames = [...files].map((f) => f.name).join(", ");
  heading.textContent = `Import Preview — ${fileNames} (${data.chunks.length} chunk${data.chunks.length !== 1 ? "s" : ""})`;
  headerEl.appendChild(heading);

  listEl.replaceChildren();

  const groups = {};
  for (const chunk of data.chunks) {
    if (!groups[chunk.source_file]) groups[chunk.source_file] = [];
    groups[chunk.source_file].push(chunk);
  }

  const fileCount = Object.keys(groups).length;
  for (const [sourceFile, chunks] of Object.entries(groups)) {
    if (fileCount > 1) {
      const subheading = document.createElement("h3");
      subheading.className = "import-source-heading";
      subheading.textContent = sourceFile;
      listEl.appendChild(subheading);
    }

    for (const chunk of chunks) {
      const card = document.createElement("div");
      card.className = "import-chunk-card";
      card.dataset.chunkIndex = chunk.index;

      const label = document.createElement("label");
      label.className = "import-chunk-label";

      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = true;
      checkbox.dataset.chunkIndex = chunk.index;
      checkbox.setAttribute("aria-label", `Include: ${chunk.title}`);

      const titleInput = document.createElement("input");
      titleInput.type = "text";
      titleInput.className = "import-chunk-title";
      titleInput.value = chunk.title;
      titleInput.dataset.chunkIndex = chunk.index;
      titleInput.setAttribute("aria-label", "Chunk title");

      label.appendChild(checkbox);
      label.appendChild(titleInput);

      const preview = document.createElement("p");
      preview.className = "import-chunk-preview";
      preview.textContent = chunk.body.substring(0, 200);

      const charCount = document.createElement("span");
      charCount.className = "import-chunk-charcount";
      charCount.textContent = `${chunk.body.length} chars`;

      card.appendChild(label);
      card.appendChild(preview);
      card.appendChild(charCount);
      listEl.appendChild(card);
    }
  }

  navigateTo("import-preview");
}

async function handleImportSelected() {
  const cards = document.querySelectorAll("#import-chunk-list .import-chunk-card");
  const selected = [];

  for (const card of cards) {
    const idx = parseInt(card.dataset.chunkIndex, 10);
    const checkbox = card.querySelector('input[type="checkbox"]');
    if (!checkbox?.checked) continue;

    const chunk = state.importChunks.find((c) => c.index === idx);
    if (!chunk) continue;

    const titleInput = card.querySelector(".import-chunk-title");
    const title = titleInput?.value?.trim() || chunk.title;
    selected.push({ title, body: chunk.body });
  }

  if (selected.length === 0) {
    alert("No chunks selected.");
    return;
  }

  const confirmBtn = document.getElementById("import-confirm-btn");
  if (confirmBtn) {
    confirmBtn.disabled = true;
    confirmBtn.textContent = "Importing\u2026";
  }

  try {
    for (const note of selected) {
      await api.create({ title: note.title, body: note.body, tags: [] });
    }
    state.importChunks = [];
    navigateTo("grid");
    api.categories().then((data) => renderCategories(data.items, state.category));
  } catch (err) {
    console.error("Import error:", err);
    alert("Import failed: " + (err.message || "Unknown error"));
  } finally {
    if (confirmBtn) {
      confirmBtn.disabled = false;
      confirmBtn.textContent = "Import Selected";
    }
  }
}
```

- [ ] **Step 2: Wire file input and import cancel buttons in `init()`**

Add after the import-file-btn click handler:

```javascript
  const fileInput = document.getElementById("import-file-input");
  if (fileInput) {
    fileInput.addEventListener("change", async () => {
      const files = fileInput.files;
      if (!files || files.length === 0) return;
      try {
        const data = await uploadForChunking(files);
        renderImportPreview(data, files);
      } catch (err) {
        console.error("Import upload error:", err);
        alert("Failed to parse files: " + (err.message || "Unknown error"));
      }
      fileInput.value = "";
    });
  }

  document.getElementById("import-confirm-btn")?.addEventListener("click", handleImportSelected);

  const cancelImport = () => {
    state.importChunks = [];
    navigateTo("grid");
  };
  document.getElementById("import-cancel-top-btn")?.addEventListener("click", cancelImport);
  document.getElementById("import-cancel-bottom-btn")?.addEventListener("click", cancelImport);
```

- [ ] **Step 3: Expose on window**

```javascript
window.handleImportSelected = handleImportSelected;
```

- [ ] **Step 4: Commit**

```bash
git add static/app.js
git commit -m "feat(ui): add file import flow with chunk preview and confirm"
```

---

## Task 9: Update and Extend UI Tests

**Files:**
- Modify: `tests/ui/test_ui.py`

- [ ] **Step 1: Fix `test_page_loads_successfully` — editor is now hidden**

```python
def test_page_loads_successfully(self, app_page: Page):
    """Verify the main page loads without errors."""
    # Grid view is the default — editor is hidden
    expect(app_page.locator("#notes-list-container")).to_be_visible()
    expect(app_page.locator("#editor-container")).not_to_be_visible()
    expect(app_page.locator("#category-list")).to_be_attached()
    expect(app_page.locator("#search-input")).to_be_visible()
```

- [ ] **Step 2: Fix `test_initial_state_empty_editor` — editor only shows after new-note click**

Replace the existing test with:

```python
def test_initial_state_shows_grid(self, app_page: Page):
    """Grid is visible and editor is hidden on fresh load."""
    expect(app_page.locator("#notes-list-container")).to_be_visible()
    expect(app_page.locator("#editor-container")).not_to_be_visible()
    expect(app_page.locator("#import-preview-container")).not_to_be_visible()
```

- [ ] **Step 3: Add `TestGridFirstNavigation` class after existing test classes**

```python
class TestGridFirstNavigation:
    """Tests for the view-switching state machine."""

    def test_new_note_opens_detail_edit(self, app_page: Page):
        """+ New Note transitions to detail view in edit mode."""
        app_page.click("#new-note-btn")
        app_page.wait_for_timeout(300)
        expect(app_page.locator("#editor-container")).to_be_visible()
        expect(app_page.locator("#notes-list-container")).not_to_be_visible()
        expect(app_page.locator("#note-body")).to_be_visible()

    def test_new_note_fields_are_blank(self, app_page: Page):
        """+ New Note opens with empty title and body."""
        app_page.click("#new-note-btn")
        app_page.wait_for_timeout(300)
        expect(app_page.locator("#note-title")).to_be_empty()
        expect(app_page.locator("#note-body")).to_be_empty()

    def test_back_button_returns_to_grid(self, app_page: Page):
        """Back button in detail view returns to grid."""
        app_page.click("#new-note-btn")
        app_page.wait_for_timeout(300)
        app_page.click("#detail-back-btn")
        app_page.wait_for_timeout(300)
        expect(app_page.locator("#notes-list-container")).to_be_visible()
        expect(app_page.locator("#editor-container")).not_to_be_visible()

    def test_close_button_returns_to_grid(self, app_page: Page):
        """X button in detail view returns to grid."""
        app_page.click("#new-note-btn")
        app_page.wait_for_timeout(300)
        app_page.click("#detail-close-btn")
        app_page.wait_for_timeout(300)
        expect(app_page.locator("#notes-list-container")).to_be_visible()

    def test_escape_from_preview_returns_to_grid(self, app_page: Page):
        """Pressing Escape in preview mode returns to grid without dialog."""
        app_page.wait_for_selector(".note-card", timeout=5000)
        app_page.locator(".note-card").first.click(position={"x": 50, "y": 50})
        app_page.wait_for_timeout(500)
        expect(app_page.locator("#editor-container")).to_be_visible()
        app_page.keyboard.press("Escape")
        app_page.wait_for_timeout(300)
        expect(app_page.locator("#notes-list-container")).to_be_visible()

    def test_dropdown_caret_opens_menu(self, app_page: Page):
        """Caret button reveals the import menu."""
        expect(app_page.locator("#new-note-menu")).not_to_be_visible()
        app_page.click("#new-note-caret")
        app_page.wait_for_timeout(200)
        expect(app_page.locator("#new-note-menu")).to_be_visible()

    def test_dropdown_closes_on_outside_click(self, app_page: Page):
        """Clicking outside closes the dropdown."""
        app_page.click("#new-note-caret")
        app_page.wait_for_timeout(200)
        expect(app_page.locator("#new-note-menu")).to_be_visible()
        app_page.locator(".site-logo").click()
        app_page.wait_for_timeout(200)
        expect(app_page.locator("#new-note-menu")).not_to_be_visible()
```

- [ ] **Step 4: Add `TestImportPreview` class**

```python
class TestImportPreview:
    """Tests for import preview view state."""

    def test_import_preview_hidden_by_default(self, app_page: Page):
        """Import preview is not visible on load."""
        expect(app_page.locator("#import-preview-container")).not_to_be_visible()

    def test_cancel_top_returns_to_grid(self, app_page: Page):
        """Top cancel button returns to grid."""
        app_page.evaluate("navigateTo('import-preview')")
        app_page.wait_for_timeout(200)
        expect(app_page.locator("#import-preview-container")).to_be_visible()
        app_page.click("#import-cancel-top-btn")
        app_page.wait_for_timeout(300)
        expect(app_page.locator("#notes-list-container")).to_be_visible()

    def test_cancel_bottom_returns_to_grid(self, app_page: Page):
        """Bottom cancel button returns to grid."""
        app_page.evaluate("navigateTo('import-preview')")
        app_page.wait_for_timeout(200)
        app_page.click("#import-cancel-bottom-btn")
        app_page.wait_for_timeout(300)
        expect(app_page.locator("#notes-list-container")).to_be_visible()
```

- [ ] **Step 5: Run the full UI test suite**

```bash
pytest tests/ui/test_ui.py -q
```

Expected: all passing

- [ ] **Step 6: Run the complete test suite**

```bash
pytest -q
```

Expected: all passing

- [ ] **Step 7: Commit**

```bash
git add tests/ui/test_ui.py
git commit -m "test(ui): update grid-first assertions, add navigation and import tests"
```

---

## Self-Review

### Spec coverage

| Spec requirement | Task |
|-----------------|------|
| Grid is home view; editor hidden by default | Task 3 + Task 5 |
| Click card opens detail in preview mode | Task 6 (`viewNote` update) |
| Back arrow + X in detail top bar | Task 3 + Task 6 |
| Preview to grid: instant | Task 6 (`confirmLeaveEdit` no-changes path) |
| Edit with unsaved changes: confirm dialog | Task 6 (change tracking + `confirmLeaveEdit`) |
| Save stays in detail, switches to preview | Task 6 (`handleSave` update) |
| "+ New Note" button in header | Task 3 + Task 7 |
| Import dropdown on caret | Task 3 + Task 7 |
| File picker accepts `.txt`, `.md`, multiple | Task 3 (`<input type="file">`) + Task 8 |
| `POST /api/notes/import` endpoint | Task 2 |
| Hybrid chunking algorithm | Task 1 |
| Import preview with editable titles + checkboxes | Task 8 (`renderImportPreview`) |
| Multi-file grouped by source | Task 8 |
| "Import Selected" creates notes | Task 8 (`handleImportSelected`) |
| Cancel import returns to grid | Task 8 |
| Backend chunking tests (all edge cases) | Task 1 |
| Import endpoint integration tests | Task 2 |
| UI tests: view switching | Task 9 |
| UI tests: import preview | Task 9 |

### No placeholders — all steps contain complete code

### Type/name consistency verified

- `navigateTo()` — defined Task 5, used Tasks 6, 7, 8, 9 — consistent
- `renderView()` — defined Task 5, called by `navigateTo()` — consistent
- `confirmLeaveEdit()` — defined Task 5, called Task 6 — consistent
- `uploadForChunking()` — defined Task 8, wired Task 8 — consistent
- `renderImportPreview()` — defined Task 8, wired Task 8 — consistent
- `handleImportSelected()` — defined Task 8, wired Task 8 — consistent
- `state.importChunks` — added Task 5, written Task 8 (`renderImportPreview`), read Task 8 (`handleImportSelected`) — consistent
- `state.hasUnsavedChanges` — added Task 5, set Task 6, read Task 5 (`confirmLeaveEdit`) — consistent
- `chunk.index` — field of `Chunk` NamedTuple (Task 1), serialized via `_asdict()` (Task 2), used as `card.dataset.chunkIndex` (Task 8) — consistent
