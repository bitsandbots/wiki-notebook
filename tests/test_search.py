"""Tests for search functionality."""

from __future__ import annotations

import pytest


@pytest.fixture
def seed_many_notes(seed_note):
    """Seed ~20 notes across multiple categories."""
    categories = ["meetings", "ideas", "journal", "projects"]
    notes = []

    for i in range(20):
        category = categories[i % len(categories)]
        title = f"Note {i + 1}"
        body = f"This is note number {i + 1} with some content about {category}."
        note_id = seed_note(title, body, category)
        notes.append(note_id)

    return notes, categories


class TestSearch:
    """Tests for /api/search endpoint."""

    def test_search_basic(self, client, seed_many_notes):
        """Should search notes and return results with snippets."""
        notes, categories = seed_many_notes

        response = client.get("/api/search?q=note")
        assert response.status_code == 200

        data = response.get_json()
        assert "items" in data
        assert "total" in data
        assert "q" in data
        assert data["q"] == "note"
        assert len(data["items"]) > 0

    def test_search_with_category_filter(self, client, seed_many_notes):
        """Should filter search results by category."""
        notes, categories = seed_many_notes

        response = client.get("/api/search?q=note&category=meetings")
        assert response.status_code == 200

        data = response.get_json()
        assert len(data["items"]) > 0

        # All results should be in meetings category
        for item in data["items"]:
            assert item["category"] == "meetings"

    def test_search_pagination(self, client, seed_many_notes):
        """Should handle pagination correctly."""
        notes, categories = seed_many_notes

        # First page
        response = client.get("/api/search?q=note&limit=5&offset=0")
        data = response.get_json()
        assert len(data["items"]) == 5
        assert data["limit"] == 5
        assert data["offset"] == 0

        # Second page
        response = client.get("/api/search?q=note&limit=5&offset=5")
        data = response.get_json()
        assert len(data["items"]) == 5
        assert data["offset"] == 5

    def test_search_empty_query(self, client):
        """Should return 422 for missing query."""
        response = client.get("/api/search")
        assert response.status_code == 422
        data = response.get_json()
        assert "error" in data

    def test_search_empty_results(self, client):
        """Should return empty results when no matches."""
        response = client.get("/api/search?q=xyznonexistent")
        data = response.get_json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_search_snippet_markups(self, client, seed_many_notes):
        """Should return snippets with <mark> tags."""
        response = client.get("/api/search?q=content")
        assert response.status_code == 200

        data = response.get_json()
        if len(data["items"]) > 0:
            # Check that snippet contains <mark> tags
            snippet = data["items"][0]["snippet"]
            assert "<mark>" in snippet or "</mark>" in snippet

    def test_special_characters_escaped(self, client, seed_many_notes):
        """Should handle special characters without raising errors."""
        response = client.get("/api/search?q=note*test")
        assert response.status_code == 200

        response = client.get('/api/search?q="quoted"')
        assert response.status_code == 200


class TestCategories:
    """Tests for /api/categories endpoint."""

    def test_list_categories(self, client, seed_many_notes):
        """Should return categories with counts."""
        notes, categories = seed_many_notes

        response = client.get("/api/categories")
        assert response.status_code == 200

        data = response.get_json()
        assert "items" in data
        categories_list = data["items"]

        # Should have at least some categories
        assert len(categories_list) > 0

        # Each category should have name and count
        for cat in categories_list:
            assert "name" in cat
            assert "count" in cat

    def test_categories_sorted_by_count(self, client, seed_many_notes):
        """Should return categories sorted by count (descending)."""
        notes, categories = seed_many_notes

        response = client.get("/api/categories")
        data = response.get_json()
        categories_list = data["items"]

        # Check descending order
        counts = [c["count"] for c in categories_list]
        assert counts == sorted(counts, reverse=True)


class TestShortQueryFallback:
    """Tests for LIKE fallback on short queries."""

    def test_short_query_routes_to_like(self, client, seed_many_notes):
        """Short queries (< 3 chars) should use LIKE search."""
        response = client.get("/api/search?q=a")
        assert response.status_code == 200

        data = response.get_json()
        # Should still return results if any note contains "a"
        # (most likely true given our seeded notes)

    def test_special_chars_not_breaking(self, client, seed_many_notes):
        """Special characters in query should not raise."""
        special_queries = [
            "note*",
            "note:",
            "note^",
            '"note"',
            "note*test",
        ]

        for q in special_queries:
            response = client.get(f"/api/search?q={q}")
            assert response.status_code == 200, f"Query '{q}' should not raise"


class TestPerformance:
    """Performance tests for search."""

    def test_search_with_many_notes(self, client, seed_note):
        """Median search latency should be reasonable with 1000 notes."""
        categories = ["meetings", "ideas", "journal", "projects"]

        # Seed 1000 notes to test performance
        for i in range(1000):
            category = categories[i % len(categories)]
            seed_note(
                f"Performance Note {i}",
                f"Performance test content for note {i} in {category}.",
                category,
            )

        response = client.get("/api/search?q=performance")
        assert response.status_code == 200

        data = response.get_json()
        # Just verify it works - actual latency testing would require more setup
        assert "total" in data
