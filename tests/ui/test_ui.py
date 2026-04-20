"""Playwright UI tests for Wiki Notebook."""

import pytest
from playwright.sync_api import Page, expect


class TestPageLoad:
    """Tests for initial page load and structure."""

    def test_page_loads_successfully(self, app_page: Page):
        """Verify the main page loads without errors."""
        # Check for critical page elements (use to_be_attached for elements that might be hidden)
        expect(app_page.locator("#editor-container")).to_be_visible()
        expect(app_page.locator("#notes-list")).to_be_attached()
        expect(app_page.locator("#category-list")).to_be_attached()
        expect(app_page.locator("#search-input")).to_be_visible()

    def test_header_elements_present(self, app_page: Page):
        """Verify header elements are present."""
        expect(app_page.locator(".site-header")).to_be_visible()
        expect(app_page.locator("#theme-toggle")).to_be_visible()
        # Sidebar toggle is hidden on desktop viewport (only shows on mobile)
        expect(app_page.locator("#sidebar-toggle")).to_be_attached()

    def test_accessibility_skip_link(self, app_page: Page):
        """Verify skip-to-content link is present for accessibility."""
        skip_link = app_page.locator(".skip-link")
        expect(skip_link).to_be_visible()
        expect(skip_link).to_have_attribute("href", "#main-content")

    def test_initial_state_empty_editor(self, app_page: Page):
        """Verify editor starts empty for new notes."""
        title_input = app_page.locator("#note-title")
        body_textarea = app_page.locator("#note-body")

        expect(title_input).to_be_empty()
        expect(body_textarea).to_be_empty()
        expect(app_page.locator("#delete-btn")).not_to_be_visible()


class TestNoteViewMode:
    """Tests for note viewing in preview mode."""

    def test_click_note_opens_preview_mode(self, app_page: Page):
        """Clicking a note card should open it in preview (view) mode."""
        # Wait for notes to load
        app_page.wait_for_selector(".note-card", timeout=5000)

        # Get the first note card
        first_note = app_page.locator(".note-card").first
        expect(first_note).to_be_visible()

        # Click on the note card (not the edit button or checkbox)
        first_note.click(position={"x": 50, "y": 50})

        # Wait for the note to load
        app_page.wait_for_timeout(500)

        # Verify preview mode is active:
        # 1. Title display should be visible (not the input)
        title_display = app_page.locator("#note-title-display")
        expect(title_display).to_be_visible()

        # 2. Title input should be hidden
        title_input = app_page.locator("#note-title")
        expect(title_input).not_to_be_visible()

        # 3. Preview container should be visible
        preview_container = app_page.locator("#preview-container")
        expect(preview_container).to_be_visible()

        # 4. Textarea should be hidden
        body_textarea = app_page.locator("#note-body")
        expect(body_textarea).not_to_be_visible()

        # 5. Edit button should show "Edit" (not "Preview")
        preview_toggle = app_page.locator("#preview-toggle")
        expect(preview_toggle).to_have_text("Edit")

    def test_view_mode_shows_rendered_markdown(self, app_page: Page):
        """Preview mode should show rendered markdown, not raw text."""
        # Click on a note to view it
        app_page.wait_for_selector(".note-card", timeout=5000)
        first_note = app_page.locator(".note-card").first
        first_note.click(position={"x": 50, "y": 50})

        app_page.wait_for_timeout(500)

        # Preview container should contain rendered HTML, not raw markdown
        preview = app_page.locator("#preview-container")
        expect(preview).to_be_visible()

        # The preview should not show raw markdown syntax
        content = preview.inner_html()
        # Should contain HTML elements, not just raw text
        assert "<" in content, "Preview should contain HTML elements"


class TestNoteEditMode:
    """Tests for note editing."""

    def test_edit_button_switches_to_edit_mode(self, app_page: Page):
        """Clicking Edit button should switch to edit mode."""
        # First, view a note in preview mode
        app_page.wait_for_selector(".note-card", timeout=5000)
        first_note = app_page.locator(".note-card").first
        first_note.click(position={"x": 50, "y": 50})
        app_page.wait_for_timeout(500)

        # Click the Edit button in editor
        preview_toggle = app_page.locator("#preview-toggle")
        expect(preview_toggle).to_have_text("Edit")
        preview_toggle.click()

        app_page.wait_for_timeout(300)

        # Verify edit mode is active:
        # 1. Title input should be visible
        title_input = app_page.locator("#note-title")
        expect(title_input).to_be_visible()

        # 2. Title display should be hidden
        title_display = app_page.locator("#note-title-display")
        expect(title_display).not_to_be_visible()

        # 3. Textarea should be visible
        body_textarea = app_page.locator("#note-body")
        expect(body_textarea).to_be_visible()

        # 4. Preview container should be hidden
        preview_container = app_page.locator("#preview-container")
        expect(preview_container).not_to_be_visible()

        # 5. Button should show "Preview"
        expect(preview_toggle).to_have_text("Preview")

    def test_edit_button_on_card_opens_edit_mode(self, app_page: Page):
        """Clicking Edit button on note card should open in edit mode."""
        app_page.wait_for_selector(".note-card", timeout=5000)

        # Click the Edit button on the first note card
        first_note = app_page.locator(".note-card").first
        edit_button = first_note.locator(".note-card-action")
        expect(edit_button).to_have_text("Edit")
        edit_button.click()

        app_page.wait_for_timeout(500)

        # Should be in edit mode (textarea visible)
        body_textarea = app_page.locator("#note-body")
        expect(body_textarea).to_be_visible()


class TestNoteCreation:
    """Tests for creating new notes."""

    def test_create_new_note(self, app_page: Page):
        """Create a new note and verify it appears in the list."""
        # Fill in the editor
        title_input = app_page.locator("#note-title")
        body_textarea = app_page.locator("#note-body")

        test_title = f"Playwright Test Note"
        test_body = "This is a test note created by Playwright."

        title_input.fill(test_title)
        body_textarea.fill(test_body)

        # Handle the alert dialog
        app_page.on("dialog", lambda dialog: dialog.accept())

        # Save the note
        save_button = app_page.locator("#save-btn")
        save_button.click()

        # Wait for save confirmation and page refresh
        app_page.wait_for_timeout(1500)

        # The new note should be at the top
        first_note_title = app_page.locator(".note-card .note-card-title").first
        expect(first_note_title).to_contain_text(test_title[:20])


class TestNoteDeletion:
    """Tests for deleting notes."""

    def test_delete_button_visible_after_view(self, app_page: Page):
        """Delete button should be visible after viewing a note."""
        app_page.wait_for_selector(".note-card", timeout=5000)
        first_note = app_page.locator(".note-card").first
        first_note.click(position={"x": 50, "y": 50})
        app_page.wait_for_timeout(500)

        # Click Edit to enable delete button
        app_page.locator("#preview-toggle").click()
        app_page.wait_for_timeout(300)

        # Delete button should now be visible
        delete_button = app_page.locator("#delete-btn")
        expect(delete_button).to_be_visible()


class TestSearchAndFilter:
    """Tests for search and category filtering."""

    def test_search_input_present(self, app_page: Page):
        """Verify search input is functional."""
        search_input = app_page.locator("#search-input")
        expect(search_input).to_be_visible()
        expect(search_input).to_be_editable()

    def test_category_sidebar_present(self, app_page: Page):
        """Verify category sidebar is present."""
        sidebar = app_page.locator("#sidebar")
        expect(sidebar).to_be_visible()

        category_list = app_page.locator("#category-list")
        expect(category_list).to_be_visible()

        # "All" category should be present
        all_category = category_list.locator(".category-item").first
        expect(all_category).to_contain_text("All")

    def test_category_filter(self, app_page: Page):
        """Test clicking a category filters notes."""
        app_page.wait_for_selector(".category-item", timeout=5000)

        # Click on "All" category
        all_category = app_page.locator(".category-item").first
        all_category.click()

        # Should trigger a refresh but notes should still be visible
        app_page.wait_for_timeout(500)
        expect(app_page.locator("#notes-list")).to_be_visible()


class TestThemeToggle:
    """Tests for theme switching."""

    def test_theme_toggle_present(self, app_page: Page):
        """Verify theme toggle button exists."""
        theme_toggle = app_page.locator("#theme-toggle")
        expect(theme_toggle).to_be_visible()
        expect(theme_toggle).to_have_attribute("aria-label", "Toggle dark mode")

    def test_theme_toggle_changes_theme(self, app_page: Page):
        """Test that clicking theme toggle changes the theme."""
        theme_toggle = app_page.locator("#theme-toggle")

        # Get initial theme
        html = app_page.locator("html")
        initial_theme = html.get_attribute("data-theme")

        # Toggle theme
        theme_toggle.click()
        app_page.wait_for_timeout(300)

        # Theme should have changed
        new_theme = html.get_attribute("data-theme")
        assert new_theme != initial_theme

        # Toggle back
        theme_toggle.click()
        app_page.wait_for_timeout(300)
        final_theme = html.get_attribute("data-theme")
        assert final_theme == initial_theme


class TestAccessibility:
    """Tests for accessibility features."""

    def test_a11y_controls_present(self, app_page: Page):
        """Verify accessibility control buttons are present."""
        contrast_btn = app_page.locator("#btn-contrast")
        font_btn = app_page.locator("#btn-font")

        expect(contrast_btn).to_be_visible()
        expect(font_btn).to_be_visible()

    def test_high_contrast_toggle(self, app_page: Page):
        """Test high contrast mode toggle."""
        contrast_btn = app_page.locator("#btn-contrast")

        # Initial state
        html = app_page.locator("html")
        initial_contrast = html.get_attribute("data-contrast")

        # Toggle
        contrast_btn.click()
        app_page.wait_for_timeout(300)

        # Should have changed
        new_contrast = html.get_attribute("data-contrast")
        assert new_contrast != initial_contrast

    def test_keyboard_navigation_skip_link(self, app_page: Page):
        """Test that skip link works for keyboard users."""
        skip_link = app_page.locator(".skip-link")

        # Focus the skip link
        skip_link.focus()
        expect(skip_link).to_be_focused()

        # Press Enter to skip to main content
        app_page.keyboard.press("Enter")
        app_page.wait_for_timeout(300)

        # Main content should be visible
        main_content = app_page.locator("#main-content")
        expect(main_content).to_be_visible()


class TestMultiSelect:
    """Tests for multi-select functionality."""

    def test_checkbox_visible_on_notes(self, app_page: Page):
        """Verify checkboxes are visible on note cards."""
        app_page.wait_for_selector(".note-card", timeout=5000)

        first_note = app_page.locator(".note-card").first
        checkbox = first_note.locator(".note-card-checkbox input")
        expect(checkbox).to_be_visible()

    def test_selecting_note_shows_action_bar(self, app_page: Page):
        """Selecting a note should show the action bar."""
        app_page.wait_for_selector(".note-card", timeout=5000)

        # Click checkbox on first note (force to bypass visibility checks)
        first_checkbox = app_page.locator(".note-card-checkbox input").first
        first_checkbox.click(force=True)
        app_page.wait_for_timeout(500)

        # Action bar should appear
        action_bar = app_page.locator("#action-bar")
        expect(action_bar).to_be_visible(timeout=5000)

        # Selection count should show
        count_el = app_page.locator("#selection-count")
        expect(count_el).to_contain_text("1 note")

    def test_clear_selection(self, app_page: Page):
        """Test clearing selection."""
        app_page.wait_for_selector(".note-card", timeout=5000)

        # Select a note first
        first_checkbox = app_page.locator(".note-card-checkbox input").first
        first_checkbox.click(force=True)
        app_page.wait_for_timeout(500)

        # Verify action bar is visible
        action_bar = app_page.locator("#action-bar")
        expect(action_bar).to_be_visible(timeout=5000)

        # Clear selection
        clear_btn = app_page.locator("#clear-selection-btn")
        clear_btn.click()
        app_page.wait_for_timeout(300)

        # Action bar should hide
        expect(action_bar).not_to_be_visible()
