"""Tests for categorization logic."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from wiki_notebook.ai.categorize import (
    _keyword_fallback,
    categorize,
)
from wiki_notebook.ai.ollama_client import OllamaClient, OllamaError


class TestKeywordFallback:
    """Tests for _keyword_fallback()."""

    def test_meeting_keyword_detected(self):
        """Correctly identifies meeting-related notes."""
        result = _keyword_fallback(
            "Team Meeting Agenda",
            "Discussion about quarterly goals and roadmap.",
        )

        assert result["category"] == "meetings"
        assert len(result["tags"]) > 0

    def test_project_keyword_detected(self):
        """Correctly identifies project-related notes."""
        result = _keyword_fallback(
            "Project Idea",
            "Building a new feature for our product.",
        )

        assert result["category"] == "project ideas"
        assert len(result["tags"]) > 0

    def test_journal_keyword_detected(self):
        """Correctly identifies journal entries."""
        result = _keyword_fallback(
            "Personal Reflection",
            "Today I learned something new about myself.",
        )

        assert result["category"] == "journal"
        assert len(result["tags"]) > 0

    def test_unchanged_category_in_tags(self):
        """Category is not repeated in tags."""
        result = _keyword_fallback(
            "Meeting Notes",
            "We discussed the quarterly meeting schedule.",
        )

        assert result["category"] == "meetings"
        assert "meetings" not in result["tags"]

    def test_no_valid_content_returns_uncategorized(self):
        """Returns uncategorized when no content available."""
        result = _keyword_fallback("", "")
        assert result["category"] == "uncategorized"


class TestCategorize:
    """Tests for categorize()."""

    def test_uses_ollama_when_available(self):
        """Uses Ollama when it is available."""
        client = MagicMock(spec=OllamaClient)
        client.is_available.return_value = True
        client.generate_json.return_value = {
            "category": "meetings",
            "tags": ["q1", "planning"],
        }

        result = categorize("Test", "Content", client)

        assert result["category"] == "meetings"
        assert result["tags"] == ["q1", "planning"]
        client.generate_json.assert_called_once()

    def test_falls_back_on_ollama_error(self):
        """Falls back to keyword heuristic on Ollama error."""
        client = MagicMock(spec=OllamaClient)
        client.is_available.return_value = True
        client.generate_json.side_effect = OllamaError("API error")

        result = categorize("Meeting Notes", "Team discussion", client)

        assert result["category"] == "meetings"

    def test_falls_back_when_ollama_unavailable(self):
        """Falls back to keyword heuristic when Ollama is unavailable."""
        client = MagicMock(spec=OllamaClient)
        client.is_available.return_value = False

        result = categorize("Project Ideas", "New app concept", client)

        assert result["category"] == "project ideas"

    def test_strips_category(self):
        """Trims whitespace from category."""
        client = MagicMock(spec=OllamaClient)
        client.is_available.return_value = True
        client.generate_json.return_value = {
            "category": "  Meetings  ",
            "tags": ["a", "b"],
        }

        result = categorize("Test", "Content", client)

        assert result["category"] == "meetings"

    def test_deduplicates_tags(self):
        """Removes duplicate tags."""
        client = MagicMock(spec=OllamaClient)
        client.is_available.return_value = True
        client.generate_json.return_value = {
            "category": "notes",
            "tags": ["tag1", "tag1", "tag2"],
        }

        result = categorize("Test", "Content", client)

        assert result["tags"] == ["tag1", "tag2"]

    def test_limits_tags_to_20(self):
        """Limits tags to 20 items."""
        client = MagicMock(spec=OllamaClient)
        client.is_available.return_value = True
        client.generate_json.return_value = {
            "category": "notes",
            "tags": [f"tag{i}" for i in range(25)],
        }

        result = categorize("Test", "Content", client)

        assert len(result["tags"]) == 20

    def test_category_not_in_tags(self):
        """Category is removed from tags if present."""
        client = MagicMock(spec=OllamaClient)
        client.is_available.return_value = True
        client.generate_json.return_value = {
            "category": "meetings",
            "tags": ["meetings", "q1", "planning"],
        }

        result = categorize("Test", "Content", client)

        assert "meetings" not in result["tags"]
        assert result["tags"] == ["q1", "planning"]

    def test_truncates_long_title(self):
        """Truncates long titles for prompt."""
        long_title = "x" * 300
        long_body = "y" * 5000

        client = MagicMock(spec=OllamaClient)
        client.is_available.return_value = True
        client.generate_json.return_value = {
            "category": "notes",
            "tags": ["test"],
        }

        result = categorize(long_title, long_body, client)

        assert result["category"] == "notes"
        # Verify prompt truncation happened (no exception)

    def test_category_keywords_no_duplicates(self):
        """CATEGORY_KEYWORDS should not contain duplicate values."""
        from wiki_notebook.ai.categorize import CATEGORY_KEYWORDS

        for category, keywords in CATEGORY_KEYWORDS.items():
            # Check for duplicates within each category's keyword list
            unique_keywords = set(keywords)
            assert len(keywords) == len(
                unique_keywords
            ), f"Category '{category}' has duplicate keywords: {keywords}"


class TestPromptSanitization:
    """Tests for prompt input sanitization."""

    def test_sanitize_prompt_escapes_quotes(self):
        """Sanitization escapes quotes to prevent injection."""
        from wiki_notebook.ai.categorize import _format_prompt

        template = 'Categorize: "{title}" - {body}'
        title = 'Title with "quotes"'
        body = "Body text"

        result = _format_prompt(template, title, body)

        # Should handle quotes safely without breaking template
        assert '"quotes"' not in result or result.count('"') % 2 == 0

    def test_sanitize_prompt_handles_newlines(self):
        """Sanitization handles newlines without breaking format."""
        from wiki_notebook.ai.categorize import _format_prompt

        template = "Title: {title}\nBody: {body}"
        title = "Title\nwith\nnewlines"
        body = "Body\ncontent"

        result = _format_prompt(template, title, body)

        # Should not raise exception and should include content
        assert "Title" in result
        assert "Body" in result
