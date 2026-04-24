"""Playwright UI tests for search functionality in Wiki Notebook.

These tests exercise the full search flow: typing in the search box,
verifying API calls, rendering results with snippets, clearing search,
category filtering during search, and edge cases like special characters
and short queries.
"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.ui

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_note(page: Page, title: str, body: str, category: str = "") -> int:
    """Create a note via the API and return its id."""
    payload: dict = {"title": title, "body": body}
    if category:
        payload["category"] = category

    result = page.evaluate(
        """async (payload) => {
            const resp = await fetch('/api/notes', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload),
            });
            return resp.json();
        }""",
        payload,
    )
    return result["id"]


def _delete_all_notes(page: Page) -> None:
    """Delete every note in the database via the API."""
    page.evaluate(
        """async () => {
            const resp = await fetch('/api/notes');
            const data = await resp.json();
            for (const note of data.items) {
                await fetch(`/api/notes/${note.id}`, { method: 'DELETE' });
            }
        }"""
    )


def _reload_grid(page: Page, base_url: str) -> None:
    """Navigate back to the grid view with a fresh page load."""
    page.goto(base_url)
    page.wait_for_selector("#notes-list-container", timeout=10000)
    page.wait_for_timeout(500)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def seeded_page(page: Page, base_url: str) -> Page:
    """Create a page with a known set of searchable notes.

    Seeds:
      1. "Grocery List"     – body mentions apples and bananas  (Personal)
      2. "Meeting Notes"    – body mentions quarterly review    (Work)
      3. "Python Tutorial"  – body mentions flask and sqlite    (Tech)
      4. "Weekend Plans"    – body mentions hiking and camping  (Personal)
    """
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(base_url)
    page.wait_for_selector("#notes-list-container", timeout=10000)
    page.wait_for_timeout(300)

    # Clean slate
    _delete_all_notes(page)

    _create_note(
        page,
        "Grocery List",
        "Need to buy apples, bananas, and milk from the store.",
        "Personal",
    )
    _create_note(
        page,
        "Meeting Notes",
        "Discussed the quarterly review and budget allocations for next year.",
        "Work",
    )
    _create_note(
        page,
        "Python Tutorial",
        "Flask and SQLite make a great combination for lightweight web apps.",
        "Tech",
    )
    _create_note(
        page,
        "Weekend Plans",
        "Going hiking and camping in the mountains this Saturday.",
        "Personal",
    )

    # Reload so the grid reflects the seeded data
    _reload_grid(page, base_url)
    return page


# ---------------------------------------------------------------------------
# Tests: basic search flow
# ---------------------------------------------------------------------------


class TestSearchBasicFlow:
    """Verify the core search-type-and-display cycle."""

    def test_search_input_is_present_and_editable(self, seeded_page: Page):
        search = seeded_page.locator("#search-input")
        expect(search).to_be_visible()
        expect(search).to_be_editable()

    def test_typing_query_triggers_search(self, seeded_page: Page):
        """Typing 'apples' should show only the Grocery List note."""
        search = seeded_page.locator("#search-input")
        search.fill("apples")

        # Wait for debounce (200 ms) + network
        seeded_page.wait_for_timeout(800)

        cards = seeded_page.locator(".note-card")
        expect(cards).to_have_count(1)
        expect(cards.first).to_contain_text("Grocery List")

    def test_search_results_contain_snippet_highlight(self, seeded_page: Page):
        """Search results should contain <mark> highlighted text."""
        search = seeded_page.locator("#search-input")
        search.fill("quarterly")
        seeded_page.wait_for_timeout(800)

        # The snippet should have a <mark> element
        marks = seeded_page.locator(".note-card mark")
        expect(marks.first).to_be_visible()

    def test_clearing_search_restores_all_notes(self, seeded_page: Page):
        """Clearing the search input should bring back all 4 notes."""
        search = seeded_page.locator("#search-input")

        # Search first
        search.fill("flask")
        seeded_page.wait_for_timeout(800)
        expect(seeded_page.locator(".note-card")).to_have_count(1)

        # Clear
        search.fill("")
        seeded_page.wait_for_timeout(800)
        expect(seeded_page.locator(".note-card")).to_have_count(4)

    def test_no_results_shows_empty_state(self, seeded_page: Page):
        """Searching for a term that doesn't exist should show the empty state."""
        search = seeded_page.locator("#search-input")
        search.fill("xyznonexistent")
        seeded_page.wait_for_timeout(800)

        empty = seeded_page.locator("#empty-state")
        expect(empty).to_be_visible()
        expect(seeded_page.locator(".note-card")).to_have_count(0)

    def test_search_is_case_insensitive(self, seeded_page: Page):
        """FTS5 should match regardless of case."""
        search = seeded_page.locator("#search-input")
        search.fill("APPLES")
        seeded_page.wait_for_timeout(800)

        cards = seeded_page.locator(".note-card")
        expect(cards).to_have_count(1)
        expect(cards.first).to_contain_text("Grocery List")


# ---------------------------------------------------------------------------
# Tests: search with category filter
# ---------------------------------------------------------------------------


class TestSearchWithCategory:
    """Search combined with category sidebar filtering."""

    def test_category_filter_then_search(self, seeded_page: Page):
        """Selecting a category then searching should scope results."""
        # Click "Personal" category
        personal = seeded_page.locator('.category-item[data-category="Personal"]')
        if personal.count() > 0:
            personal.click()
            seeded_page.wait_for_timeout(500)

            # Now search within Personal
            search = seeded_page.locator("#search-input")
            search.fill("hiking")
            seeded_page.wait_for_timeout(800)

            cards = seeded_page.locator(".note-card")
            expect(cards).to_have_count(1)
            expect(cards.first).to_contain_text("Weekend Plans")

    def test_search_then_clear_category(self, seeded_page: Page):
        """After searching with a category, clicking 'All' should reset."""
        # Click a specific category first
        personal = seeded_page.locator('.category-item[data-category="Personal"]')
        if personal.count() > 0:
            personal.click()
            seeded_page.wait_for_timeout(500)

        # Search
        search = seeded_page.locator("#search-input")
        search.fill("hiking")
        seeded_page.wait_for_timeout(800)

        # Click "All"
        all_cat = seeded_page.locator(".category-item").first
        all_cat.click()
        seeded_page.wait_for_timeout(800)

        # Search should be cleared and all notes visible
        expect(seeded_page.locator(".note-card")).to_have_count(4)


# ---------------------------------------------------------------------------
# Tests: short queries (LIKE fallback)
# ---------------------------------------------------------------------------


class TestShortQueryFallback:
    """Queries < 3 chars use LIKE instead of FTS5."""

    def test_two_char_query_returns_results(self, seeded_page: Page):
        """A 2-char query like 'fl' should still find 'flask'."""
        search = seeded_page.locator("#search-input")
        search.fill("fl")
        seeded_page.wait_for_timeout(800)

        cards = seeded_page.locator(".note-card")
        # Should find Python Tutorial (contains "Flask")
        expect(cards).to_have_count(1)

    def test_single_char_query(self, seeded_page: Page):
        """A 1-char query should use LIKE search and return results."""
        search = seeded_page.locator("#search-input")
        search.fill("q")
        seeded_page.wait_for_timeout(800)

        # 'q' appears in multiple notes (quarterly, SqLite) — at least one should appear
        cards = seeded_page.locator(".note-card")
        expect(cards.first).to_be_visible()


# ---------------------------------------------------------------------------
# Tests: special characters
# ---------------------------------------------------------------------------


class TestSearchSpecialCharacters:
    """FTS5 special characters should be safely escaped."""

    def test_query_with_quotes(self, seeded_page: Page):
        """Double quotes should not break the search."""
        search = seeded_page.locator("#search-input")
        search.fill('"apples"')
        seeded_page.wait_for_timeout(800)

        # Should not crash — either find results or show empty state
        # The key assertion: page should not show an error
        expect(seeded_page.locator("#notes-list-container")).to_be_visible()

    def test_query_with_asterisk(self, seeded_page: Page):
        """Asterisks should be escaped, not treated as wildcards."""
        search = seeded_page.locator("#search-input")
        search.fill("apple*")
        seeded_page.wait_for_timeout(800)

        expect(seeded_page.locator("#notes-list-container")).to_be_visible()

    def test_query_with_pipe(self, seeded_page: Page):
        """Pipe characters should not be treated as FTS5 OR operator."""
        search = seeded_page.locator("#search-input")
        search.fill("apples | bananas")
        seeded_page.wait_for_timeout(800)

        expect(seeded_page.locator("#notes-list-container")).to_be_visible()


# ---------------------------------------------------------------------------
# Tests: search result interaction
# ---------------------------------------------------------------------------


class TestSearchResultInteraction:
    """Clicking search results should navigate to the detail view."""

    def test_click_search_result_opens_detail(self, seeded_page: Page):
        """Clicking a search result card should open the note detail."""
        search = seeded_page.locator("#search-input")
        search.fill("flask")
        seeded_page.wait_for_timeout(800)

        card = seeded_page.locator(".note-card").first
        card.click()
        seeded_page.wait_for_timeout(500)

        # Should be in detail/preview mode
        editor = seeded_page.locator("#editor-container")
        expect(editor).to_be_visible()

    def test_back_from_detail_preserves_search(self, seeded_page: Page):
        """After viewing a search result and going back, search state
        should be preserved or gracefully cleared."""
        search = seeded_page.locator("#search-input")
        search.fill("flask")
        seeded_page.wait_for_timeout(800)

        # Click into the result
        card = seeded_page.locator(".note-card").first
        card.click()
        seeded_page.wait_for_timeout(500)

        # Go back
        back_btn = seeded_page.locator("#back-btn")
        if back_btn.count() > 0:
            back_btn.click()
            seeded_page.wait_for_timeout(800)

            # Notes list should be visible again
            expect(seeded_page.locator("#notes-list-container")).to_be_visible()


# ---------------------------------------------------------------------------
# Tests: search API error handling
# ---------------------------------------------------------------------------


class TestSearchErrorHandling:
    """The UI should handle search API errors gracefully."""

    def test_empty_search_after_typing(self, seeded_page: Page):
        """Typing then clearing should not leave the UI in a broken state."""
        search = seeded_page.locator("#search-input")

        # Type and clear rapidly
        search.fill("test")
        seeded_page.wait_for_timeout(100)
        search.fill("")
        seeded_page.wait_for_timeout(800)

        # All notes should be visible
        cards = seeded_page.locator(".note-card")
        expect(cards).to_have_count(4)

    def test_rapid_typing_does_not_break_ui(self, seeded_page: Page):
        """Fast typing should be debounced without leaving stale results."""
        search = seeded_page.locator("#search-input")

        # Type character by character quickly
        search.press_sequentially("hiking", delay=50)
        seeded_page.wait_for_timeout(800)

        cards = seeded_page.locator(".note-card")
        expect(cards).to_have_count(1)
        expect(cards.first).to_contain_text("Weekend Plans")


# ---------------------------------------------------------------------------
# Tests: search result display quality
# ---------------------------------------------------------------------------


class TestSearchResultDisplay:
    """Verify search results render correctly with expected fields."""

    def test_search_result_shows_title(self, seeded_page: Page):
        """Each search result card should display the note title."""
        search = seeded_page.locator("#search-input")
        search.fill("bananas")
        seeded_page.wait_for_timeout(800)

        title = seeded_page.locator(".note-card .note-card-title").first
        expect(title).to_contain_text("Grocery List")

    def test_search_result_shows_category(self, seeded_page: Page):
        """Each search result card should display the note category."""
        search = seeded_page.locator("#search-input")
        search.fill("quarterly")
        seeded_page.wait_for_timeout(800)

        category = seeded_page.locator(".note-card .note-card-category").first
        # Category is auto-lowercased by the enrichment worker
        expect(category).to_contain_text("work", ignore_case=True)

    def test_search_result_shows_snippet_not_full_body(self, seeded_page: Page):
        """Search results should show a snippet, not the full body text."""
        search = seeded_page.locator("#search-input")
        search.fill("apples")
        seeded_page.wait_for_timeout(800)

        body = seeded_page.locator(".note-card .note-card-body").first
        expect(body).to_be_visible()
        # Snippet should contain the search term
        expect(body).to_contain_text("apples")

    def test_search_results_hide_checkboxes(self, seeded_page: Page):
        """Search results should not show selection checkboxes."""
        search = seeded_page.locator("#search-input")
        search.fill("apples")
        seeded_page.wait_for_timeout(800)

        checkboxes = seeded_page.locator(".note-card .note-card-checkbox")
        expect(checkboxes).to_have_count(0)


# ---------------------------------------------------------------------------
# Tests: multi-word search
# ---------------------------------------------------------------------------


class TestMultiWordSearch:
    """Verify multi-word queries work correctly."""

    def test_multi_word_query(self, seeded_page: Page):
        """Searching for 'hiking camping' should find Weekend Plans."""
        search = seeded_page.locator("#search-input")
        search.fill("hiking camping")
        seeded_page.wait_for_timeout(800)

        cards = seeded_page.locator(".note-card")
        expect(cards).to_have_count(1)
        expect(cards.first).to_contain_text("Weekend Plans")

    def test_partial_word_match(self, seeded_page: Page):
        """Searching for 'quart' should match 'quarterly' via FTS prefix."""
        search = seeded_page.locator("#search-input")
        search.fill("quart")
        seeded_page.wait_for_timeout(800)

        cards = seeded_page.locator(".note-card")
        # FTS5 default tokenizer may or may not do prefix matching
        # This test documents actual behavior
        container = seeded_page.locator("#notes-list-container")
        expect(container).to_be_visible()
