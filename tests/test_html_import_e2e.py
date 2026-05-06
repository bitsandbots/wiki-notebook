"""Reproduce HTML import end-to-end: upload file → create notes → check grid.

Run with: .venv/bin/pytest _debug_html_e2e.py -v -s
"""

from __future__ import annotations

import io

import pytest

HTML_SIMPLE = b"<html><head><title>Simple Page</title></head><body><p>Hello world.</p></body></html>"
HTML_FULL = b"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>Full Doc Title</title></head>
<body>
<h1>Main Heading</h1>
<p>Paragraph with <strong>bold</strong> and <em>italic</em>.</p>
<table><thead><tr><th>A</th></tr></thead><tbody><tr><td>1</td></tr></tbody></table>
</body>
</html>"""
HTML_ENTITIES = b"<html><body><p>AT&amp;T &lt;rocks&gt; &amp; so does &#39;this&#39;</p></body></html>"
HTML_LARGE = b"<html><body>" + b"<p>Line content here.</p>\n" * 200 + b"</body></html>"


def _upload(client, html_bytes: bytes, filename: str = "test.html"):
    return client.post(
        "/api/notes/import",
        data={"files": [(io.BytesIO(html_bytes), filename, "text/html")]},
        content_type="multipart/form-data",
    )


def _create_from_chunk(client, chunk: dict):
    import json

    return client.post(
        "/api/notes",
        data=json.dumps(
            {
                "title": chunk["title"],
                "body": chunk["body"],
                "tags": [],
                "content_type": chunk["content_type"],
            }
        ),
        content_type="application/json",
    )


class TestHtmlImportEndToEnd:
    def test_simple_html_full_flow(self, client):
        r = _upload(client, HTML_SIMPLE)
        assert r.status_code == 200, r.get_data(as_text=True)
        chunks = r.get_json()["chunks"]
        assert len(chunks) == 1
        chunk = chunks[0]
        assert chunk["content_type"] == "html"

        r2 = _create_from_chunk(client, chunk)
        assert r2.status_code == 201, r2.get_data(as_text=True)
        note = r2.get_json()
        assert note["content_type"] == "html"
        assert note["title"] == "Simple Page"

    def test_full_document_html_flow(self, client):
        r = _upload(client, HTML_FULL)
        assert r.status_code == 200
        chunk = r.get_json()["chunks"][0]

        r2 = _create_from_chunk(client, chunk)
        assert r2.status_code == 201, r2.get_data(as_text=True)
        note = r2.get_json()
        assert note["title"] == "Full Doc Title"
        assert note["content_type"] == "html"

    def test_html_with_entities_flow(self, client):
        r = _upload(client, HTML_ENTITIES)
        assert r.status_code == 200
        chunk = r.get_json()["chunks"][0]
        r2 = _create_from_chunk(client, chunk)
        assert r2.status_code == 201, r2.get_data(as_text=True)

    def test_large_html_stays_single_chunk(self, client):
        """HTML files are never split — always one chunk regardless of size."""
        r = _upload(client, HTML_LARGE)
        assert r.status_code == 200
        chunks = r.get_json()["chunks"]
        assert len(chunks) == 1  # HTML = single chunk always

        chunk = chunks[0]
        r2 = _create_from_chunk(client, chunk)
        assert r2.status_code == 201, r2.get_data(as_text=True)

    def test_note_created_appears_in_list(self, client):
        r = _upload(client, HTML_SIMPLE)
        chunk = r.get_json()["chunks"][0]
        _create_from_chunk(client, chunk)

        r_list = client.get("/api/notes")
        assert r_list.status_code == 200
        items = r_list.get_json()["items"]
        html_notes = [n for n in items if n.get("content_type") == "html"]
        assert len(html_notes) == 1
        assert html_notes[0]["title"] == "Simple Page"

    def test_html_note_searchable_by_text_content(self, client):
        """HTML notes are searchable by their stripped text content via FTS5."""
        r = _upload(client, HTML_SIMPLE)
        chunk = r.get_json()["chunks"][0]
        _create_from_chunk(client, chunk)

        r_search = client.get("/api/search?q=Hello+world")
        assert r_search.status_code == 200
        results = r_search.get_json()
        assert any(n["title"] == "Simple Page" for n in results.get("items", []))

    def test_htm_extension_full_flow(self, client):
        r = _upload(client, HTML_SIMPLE, filename="test.htm")
        assert r.status_code == 200
        chunk = r.get_json()["chunks"][0]
        assert chunk["content_type"] == "html"
        r2 = _create_from_chunk(client, chunk)
        assert r2.status_code == 201, r2.get_data(as_text=True)
