"""Unit tests for HTML utility functions."""

from __future__ import annotations

import pytest

from wiki_notebook.html_utils import extract_title_from_html, strip_html


class TestStripHtml:
    def test_strips_tags(self):
        assert strip_html("<p>Hello</p>") == "Hello"

    def test_strips_nested_tags(self):
        assert strip_html("<div><p>Hello <b>World</b></p></div>") == "Hello World"

    def test_decodes_common_entities(self):
        assert strip_html("a &amp; b &lt; c &gt; d") == "a & b < c > d"

    def test_decodes_nbsp(self):
        assert strip_html("word1&nbsp;word2") == "word1 word2"

    def test_collapses_whitespace(self):
        assert strip_html("  a   b\n\nc  ") == "a b c"

    def test_empty_input(self):
        assert strip_html("") == ""

    def test_plain_text_unchanged(self):
        assert strip_html("Just plain text.") == "Just plain text."

    def test_self_closing_tags(self):
        assert strip_html("Line 1<br>Line 2<hr>Line 3") == "Line 1 Line 2 Line 3"

    def test_tags_with_attributes(self):
        assert strip_html('<a href="/page" class="link">Click here</a>') == "Click here"


class TestExtractTitleFromHtml:
    def test_from_title_tag(self):
        html = "<html><head><title>My Page</title></head><body></body></html>"
        assert extract_title_from_html(html) == "My Page"

    def test_from_title_tag_case_insensitive(self):
        html = "<TITLE>Uppercase Title</TITLE>"
        assert extract_title_from_html(html) == "Uppercase Title"

    def test_from_h1_fallback(self):
        html = "<html><body><h1>Main Heading</h1><p>Content</p></body></html>"
        assert extract_title_from_html(html) == "Main Heading"

    def test_title_takes_priority_over_h1(self):
        html = (
            "<html><head><title>Page Title</title></head>"
            "<body><h1>Different H1</h1></body></html>"
        )
        assert extract_title_from_html(html) == "Page Title"

    def test_fallback_when_neither_found(self):
        assert (
            extract_title_from_html("<p>No title or h1</p>", "Fallback") == "Fallback"
        )

    def test_default_fallback(self):
        assert extract_title_from_html("<p>No headings</p>") == "Imported HTML"

    def test_title_with_entities_decoded(self):
        html = "<title>Hello &amp; Welcome</title>"
        assert extract_title_from_html(html) == "Hello & Welcome"

    def test_title_with_tags_stripped(self):
        html = "<title><b>Bold</b> Title</title>"
        assert extract_title_from_html(html) == "Bold Title"

    def test_h1_with_nested_tags(self):
        html = "<h1>Section <em>One</em></h1>"
        assert extract_title_from_html(html) == "Section One"

    def test_multiline_title(self):
        html = "<title>\n  Multi\n  Line\n</title>"
        assert extract_title_from_html(html) == "Multi Line"
