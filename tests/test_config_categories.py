"""Tests for category configuration system."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from wiki_notebook.config_categories import (
    get_custom_categories,
    load_category_keywords,
)


class TestLoadCategoryKeywords:
    """Tests for load_category_keywords()."""

    def test_load_default_keywords_when_env_unset(self):
        """Returns default keywords when WIKI_NOTE_CATEGORIES env var is unset."""
        with patch.dict(os.environ, {}, clear=False):
            if "WIKI_NOTE_CATEGORIES" in os.environ:
                del os.environ["WIKI_NOTE_CATEGORIES"]
            keywords = load_category_keywords()
            assert "meetings" in keywords
            assert "project ideas" in keywords
            assert "journal" in keywords
            assert "recipes" in keywords
            assert "notes" in keywords
            assert "learning" in keywords

    def test_load_custom_keywords_from_env(self):
        """Loads custom categories from WIKI_NOTE_CATEGORIES env var."""
        custom_cats = '{"custom_cat1": ["word1", "word2"], "custom_cat2": ["word3"]}'
        with patch.dict(os.environ, {"WIKI_NOTE_CATEGORIES": custom_cats}):
            keywords = load_category_keywords()
            assert "custom_cat1" in keywords
            assert "custom_cat2" in keywords
            assert "word1" in keywords["custom_cat1"]
            assert "word3" in keywords["custom_cat2"]

    def test_invalid_json_in_env_falls_back_to_default(self):
        """Falls back to defaults when WIKI_NOTE_CATEGORIES contains invalid JSON."""
        with patch.dict(os.environ, {"WIKI_NOTE_CATEGORIES": "invalid_json{"}):
            keywords = load_category_keywords()
            # Should not raise exception, should return defaults
            assert "meetings" in keywords


class TestGetCustomCategories:
    """Tests for get_custom_categories()."""

    def test_returns_sorted_list_of_categories(self):
        """Returns sorted list of category names."""
        categories = get_custom_categories()
        assert isinstance(categories, list)
        assert len(categories) > 0
        # Check it's sorted
        assert categories == sorted(categories)

    def test_includes_default_categories(self):
        """Returned list includes default categories when no custom env var."""
        with patch.dict(os.environ, {}, clear=False):
            if "WIKI_NOTE_CATEGORIES" in os.environ:
                del os.environ["WIKI_NOTE_CATEGORIES"]
            categories = get_custom_categories()
            assert "meetings" in categories
            assert "project ideas" in categories
            assert "journal" in categories
            assert "recipes" in categories
            assert "notes" in categories
            assert "learning" in categories

    def test_includes_custom_categories_from_env(self):
        """Returned list includes custom categories from env var."""
        custom_cats = '{"my_custom_category": ["word1"]}'
        with patch.dict(os.environ, {"WIKI_NOTE_CATEGORIES": custom_cats}):
            categories = get_custom_categories()
            assert "my_custom_category" in categories
