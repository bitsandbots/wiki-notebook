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
        # Short bodies (< MIN_CHUNK_SIZE chars) are merged into the preceding chunk
        assert len(result["chunks"]) == 1

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
        resp = _upload(
            client,
            [
                ("file1.md", md1, "text/markdown"),
                ("file2.md", md2, "text/markdown"),
            ],
        )
        assert resp.status_code == 200
        # Short bodies (< MIN_CHUNK_SIZE chars) are merged into the preceding chunk; so A+A merges to 1, B+C merges to 1 = 2 total
        assert len(resp.get_json()["chunks"]) == 2

    def test_multi_file_source_file_preserved(self, client):
        resp = _upload(
            client,
            [
                ("alpha.md", b"# A\nBody.\n", "text/markdown"),
                ("beta.md", b"# B\nBody.\n", "text/markdown"),
            ],
        )
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


class TestHtmlImport:
    def test_html_file_returns_chunks(self, client):
        html = b"<html><body><h1>Title</h1><p>Body text.</p></body></html>"
        resp = _upload(client, [("page.html", html, "text/html")])
        assert resp.status_code == 200
        result = resp.get_json()
        assert "chunks" in result
        assert len(result["chunks"]) == 1

    def test_html_chunk_has_content_type(self, client):
        html = b"<html><body><h1>Title</h1><p>Body.</p></body></html>"
        resp = _upload(client, [("page.html", html, "text/html")])
        chunk = resp.get_json()["chunks"][0]
        assert chunk["content_type"] == "html"

    def test_html_chunk_preserves_tags(self, client):
        html = b"<html><body><h1>Title</h1><p>Body.</p></body></html>"
        resp = _upload(client, [("page.html", html, "text/html")])
        chunk = resp.get_json()["chunks"][0]
        assert "<h1>Title</h1>" in chunk["body"]
        assert "<p>Body.</p>" in chunk["body"]

    def test_html_chunk_title_from_title_tag(self, client):
        html = (
            b"<html><head><title>Page Title</title></head>"
            b"<body><p>Body.</p></body></html>"
        )
        resp = _upload(client, [("page.html", html, "text/html")])
        assert resp.get_json()["chunks"][0]["title"] == "Page Title"

    def test_htm_extension_accepted(self, client):
        html = b"<html><body><h1>HTM Test</h1><p>Body.</p></body></html>"
        resp = _upload(client, [("page.htm", html, "text/html")])
        assert resp.status_code == 200
        assert resp.get_json()["chunks"][0]["content_type"] == "html"

    def test_html_import_does_not_create_notes(self, client):
        html = b"<html><body><h1>Title</h1><p>Body.</p></body></html>"
        _upload(client, [("page.html", html, "text/html")])
        list_resp = client.get("/api/notes")
        assert list_resp.get_json()["total"] == 0

    def test_empty_html_returns_400(self, client):
        resp = _upload(client, [("empty.html", b"", "text/html")])
        assert resp.status_code == 400
