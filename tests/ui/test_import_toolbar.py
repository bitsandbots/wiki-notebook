"""Playwright tests for import preview toolbar, filter, keyboard shortcuts."""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FAKE_CHUNKS = [
    {
        "index": 0,
        "title": "Alpha chunk",
        "body": "Body of alpha with unique content",
        "source_file": "test.md",
        "content_type": "markdown",
    },
    {
        "index": 1,
        "title": "Beta chunk",
        "body": "Body of beta with other stuff",
        "source_file": "test.md",
        "content_type": "markdown",
    },
    {
        "index": 2,
        "title": "Gamma chunk",
        "body": "Gamma body content here",
        "source_file": "test.md",
        "content_type": "markdown",
    },
]


def _seed_import_preview(page: Page, chunks: list | None = None) -> None:
    """Inject synthetic chunks into the app and render import-preview."""
    data = chunks if chunks is not None else _FAKE_CHUNKS
    page.evaluate(
        """(data) => {
            const fakeFile = new File([''], 'test.md', { type: 'text/plain' });
            const dt = new DataTransfer();
            dt.items.add(fakeFile);
            renderImportPreview({ chunks: data }, dt.files);
        }""",
        data,
    )
    page.wait_for_timeout(300)


# ---------------------------------------------------------------------------
# Toolbar — selection count and select-all button
# ---------------------------------------------------------------------------


class TestImportSelectionCount:
    """Selection counter and confirm button text update correctly."""

    def test_counter_shows_all_selected_on_load(self, app_page: Page):
        """All chunks checked by default; counter shows N of N."""
        _seed_import_preview(app_page)
        count_el = app_page.locator("#import-selection-count")
        expect(count_el).to_have_text("3 of 3 selected")

    def test_counter_updates_on_uncheck(self, app_page: Page):
        """Unchecking a card decrements the counter."""
        _seed_import_preview(app_page)
        first_cb = app_page.locator(
            "#import-chunk-list .import-chunk-card input[type='checkbox']"
        ).first
        first_cb.uncheck()
        app_page.wait_for_timeout(100)
        expect(app_page.locator("#import-selection-count")).to_have_text(
            "2 of 3 selected"
        )

    def test_confirm_button_shows_count(self, app_page: Page):
        """Confirm button label includes selected count when >0."""
        _seed_import_preview(app_page)
        expect(app_page.locator("#import-confirm-btn")).to_have_text(
            "Import 3 Selected"
        )

    def test_confirm_button_generic_when_none_checked(self, app_page: Page):
        """Confirm button shows generic label when nothing is selected."""
        _seed_import_preview(app_page)
        for cb in app_page.locator(
            "#import-chunk-list .import-chunk-card input[type='checkbox']"
        ).all():
            cb.uncheck()
        app_page.wait_for_timeout(100)
        expect(app_page.locator("#import-confirm-btn")).to_have_text("Import Selected")


class TestSelectAllButton:
    """Select All / Deselect All toggle behaviour."""

    def test_button_shows_deselect_all_when_all_checked(self, app_page: Page):
        """Button text is 'Deselect All' when every visible chunk is checked."""
        _seed_import_preview(app_page)
        expect(app_page.locator("#import-select-all-btn")).to_have_text("Deselect All")

    def test_deselect_all_unchecks_all(self, app_page: Page):
        """Clicking 'Deselect All' unchecks every visible checkbox."""
        _seed_import_preview(app_page)
        app_page.click("#import-select-all-btn")
        app_page.wait_for_timeout(100)
        for cb in app_page.locator(
            "#import-chunk-list .import-chunk-card input[type='checkbox']"
        ).all():
            expect(cb).not_to_be_checked()

    def test_button_shows_select_all_after_deselect(self, app_page: Page):
        """Button text switches to 'Select All' after deselecting."""
        _seed_import_preview(app_page)
        app_page.click("#import-select-all-btn")
        app_page.wait_for_timeout(100)
        expect(app_page.locator("#import-select-all-btn")).to_have_text("Select All")

    def test_select_all_rechecks_all(self, app_page: Page):
        """Clicking 'Select All' re-checks every visible checkbox."""
        _seed_import_preview(app_page)
        app_page.click("#import-select-all-btn")  # deselect all
        app_page.wait_for_timeout(100)
        app_page.click("#import-select-all-btn")  # select all
        app_page.wait_for_timeout(100)
        for cb in app_page.locator(
            "#import-chunk-list .import-chunk-card input[type='checkbox']"
        ).all():
            expect(cb).to_be_checked()

    def test_select_all_skips_hidden_cards(self, app_page: Page):
        """Select All only affects visible (non-filtered) cards."""
        _seed_import_preview(app_page)
        # Uncheck all first
        app_page.click("#import-select-all-btn")
        app_page.wait_for_timeout(100)
        # Filter to show only "Alpha"
        app_page.fill("#import-chunk-search", "alpha")
        app_page.wait_for_timeout(300)
        # Select all visible (should only check the alpha card)
        app_page.click("#import-select-all-btn")
        app_page.wait_for_timeout(100)
        # Counter reflects only visible
        expect(app_page.locator("#import-selection-count")).to_have_text(
            "1 of 1 selected"
        )
        # Clear filter — beta and gamma are still unchecked
        app_page.fill("#import-chunk-search", "")
        app_page.wait_for_timeout(300)
        expect(app_page.locator("#import-selection-count")).to_have_text(
            "1 of 3 selected"
        )


# ---------------------------------------------------------------------------
# Chunk search filter
# ---------------------------------------------------------------------------


class TestChunkSearchFilter:
    """Client-side filter hides non-matching cards."""

    def test_filter_hides_non_matching_cards(self, app_page: Page):
        """Typing a query hides cards that don't match."""
        _seed_import_preview(app_page)
        app_page.fill("#import-chunk-search", "alpha")
        app_page.wait_for_timeout(300)
        cards = app_page.locator("#import-chunk-list .import-chunk-card")
        expect(cards).to_have_count(3)
        # Only first card visible
        expect(cards.nth(0)).to_be_visible()
        expect(cards.nth(1)).not_to_be_visible()
        expect(cards.nth(2)).not_to_be_visible()

    def test_filter_is_case_insensitive(self, app_page: Page):
        """Filter matches regardless of case."""
        _seed_import_preview(app_page)
        app_page.fill("#import-chunk-search", "BETA")
        app_page.wait_for_timeout(300)
        cards = app_page.locator("#import-chunk-list .import-chunk-card")
        expect(cards.nth(0)).not_to_be_visible()
        expect(cards.nth(1)).to_be_visible()
        expect(cards.nth(2)).not_to_be_visible()

    def test_filter_matches_body_text(self, app_page: Page):
        """Filter matches against card body, not just title."""
        _seed_import_preview(app_page)
        app_page.fill("#import-chunk-search", "unique content")
        app_page.wait_for_timeout(300)
        cards = app_page.locator("#import-chunk-list .import-chunk-card")
        expect(cards.nth(0)).to_be_visible()  # "unique content" is in alpha body
        expect(cards.nth(1)).not_to_be_visible()
        expect(cards.nth(2)).not_to_be_visible()

    def test_clear_filter_restores_all_cards(self, app_page: Page):
        """Clearing the filter makes all cards visible again."""
        _seed_import_preview(app_page)
        app_page.fill("#import-chunk-search", "alpha")
        app_page.wait_for_timeout(300)
        app_page.fill("#import-chunk-search", "")
        app_page.wait_for_timeout(300)
        for card in app_page.locator("#import-chunk-list .import-chunk-card").all():
            expect(card).to_be_visible()

    def test_counter_excludes_hidden_cards(self, app_page: Page):
        """Selection counter only counts visible cards."""
        _seed_import_preview(app_page)
        app_page.fill("#import-chunk-search", "beta")
        app_page.wait_for_timeout(300)
        expect(app_page.locator("#import-selection-count")).to_have_text(
            "1 of 1 selected"
        )


# ---------------------------------------------------------------------------
# Keyboard shortcuts
# ---------------------------------------------------------------------------


class TestKeyboardShortcuts:
    """Keyboard shortcuts behave correctly across views."""

    def test_question_mark_opens_shortcut_modal(self, app_page: Page):
        """? key opens the keyboard shortcuts help modal."""
        app_page.keyboard.press("?")
        app_page.wait_for_timeout(200)
        modal = app_page.locator("#shortcut-help-modal")
        expect(modal).to_be_visible()
        # Close it
        app_page.keyboard.press("Escape")
        app_page.wait_for_timeout(200)
        expect(modal).not_to_be_attached()

    def test_shortcut_modal_lists_shortcuts(self, app_page: Page):
        """Shortcut help modal contains expected keyboard shortcuts."""
        app_page.keyboard.press("?")
        app_page.wait_for_timeout(200)
        modal_text = app_page.locator("#shortcut-help-modal").inner_text()
        assert "Ctrl+Enter" in modal_text
        assert "Ctrl+A" in modal_text
        assert "Ctrl+F" in modal_text
        app_page.keyboard.press("Escape")
        app_page.wait_for_timeout(200)

    def test_shortcut_n_creates_new_note_in_grid(self, app_page: Page):
        """N key opens new note form from grid view."""
        expect(app_page.locator("#notes-list-container")).to_be_visible()
        app_page.keyboard.press("n")
        app_page.wait_for_timeout(400)
        expect(app_page.locator("#editor-container")).to_be_visible()
        # Go back to grid for subsequent tests
        app_page.keyboard.press("Escape")
        app_page.wait_for_timeout(300)

    def test_shortcut_n_ignored_while_typing(self, app_page: Page):
        """N key does not trigger new note when user is typing in search."""
        app_page.click("#search-input")
        app_page.keyboard.press("n")
        app_page.wait_for_timeout(200)
        # Should still be in grid, not detail view
        expect(app_page.locator("#notes-list-container")).to_be_visible()
        expect(app_page.locator("#editor-container")).not_to_be_visible()
        # Clear search and blur
        app_page.fill("#search-input", "")
        app_page.keyboard.press("Escape")
        app_page.wait_for_timeout(200)

    def test_ctrl_a_selects_all_in_import_preview(self, app_page: Page):
        """Ctrl+A selects all visible chunks in import-preview view."""
        _seed_import_preview(app_page)
        # Uncheck all first
        app_page.click("#import-select-all-btn")
        app_page.wait_for_timeout(100)
        expect(app_page.locator("#import-selection-count")).to_have_text(
            "0 of 3 selected"
        )
        # Ctrl+A should re-check all
        app_page.keyboard.press("Control+a")
        app_page.wait_for_timeout(100)
        expect(app_page.locator("#import-selection-count")).to_have_text(
            "3 of 3 selected"
        )
        # Return to grid
        app_page.keyboard.press("Escape")
        app_page.wait_for_timeout(300)

    def test_ctrl_shift_a_deselects_all_in_import_preview(self, app_page: Page):
        """Ctrl+Shift+A deselects all visible chunks."""
        _seed_import_preview(app_page)
        expect(app_page.locator("#import-selection-count")).to_have_text(
            "3 of 3 selected"
        )
        app_page.keyboard.press("Control+Shift+A")
        app_page.wait_for_timeout(100)
        expect(app_page.locator("#import-selection-count")).to_have_text(
            "0 of 3 selected"
        )
        app_page.keyboard.press("Escape")
        app_page.wait_for_timeout(300)

    def test_ctrl_f_focuses_chunk_search(self, app_page: Page):
        """Ctrl+F focuses the chunk search input in import-preview."""
        _seed_import_preview(app_page)
        app_page.keyboard.press("Control+f")
        app_page.wait_for_timeout(100)
        focused = app_page.evaluate("document.activeElement?.id")
        assert focused == "import-chunk-search"
        app_page.keyboard.press("Escape")
        app_page.wait_for_timeout(300)

    def test_escape_clears_filter_before_exiting_preview(self, app_page: Page):
        """First Escape clears filter; second Escape exits import-preview."""
        _seed_import_preview(app_page)
        app_page.fill("#import-chunk-search", "alpha")
        app_page.wait_for_timeout(200)
        app_page.click("#import-chunk-search")  # focus the search
        # First Escape clears filter but stays in import-preview
        app_page.keyboard.press("Escape")
        app_page.wait_for_timeout(200)
        filter_val = app_page.input_value("#import-chunk-search")
        assert filter_val == "", "Filter should be cleared after first Escape"
        expect(app_page.locator("#import-preview-container")).to_be_visible()
        # Second Escape exits import-preview
        app_page.keyboard.press("Escape")
        app_page.wait_for_timeout(300)
        expect(app_page.locator("#notes-list-container")).to_be_visible()
