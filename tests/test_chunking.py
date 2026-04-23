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
