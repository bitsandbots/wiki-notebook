"""Tests for input validation."""

from __future__ import annotations

import pytest

from wiki_notebook.validation import (
    ValidationError,
    validate_category,
    validate_create,
    validate_tags,
    validate_update,
)


class TestValidateCreate:
    """Tests for validate_create()."""

    def test_valid_payload(self):
        """Should return cleaned payload for valid input."""
        payload = {
            "title": "  My Title  ",
            "body": "  Body content  ",
            "category": "  Meetings  ",
            "tags": ["tag1", "TAG2", "tag3"],
        }

        result = validate_create(payload)

        assert result["title"] == "My Title"
        assert result["body"] == "Body content"
        assert result["category"] == "meetings"
        assert result["tags"] == ["tag1", "tag2", "tag3"]

    def test_empty_title(self):
        """Should raise ValidationError for empty title."""
        with pytest.raises(ValidationError) as exc:
            validate_create({"title": "", "body": "body"})

        assert "title is required" in str(exc.value)

    def test_whitespace_title(self):
        """Should raise ValidationError for whitespace-only title."""
        with pytest.raises(ValidationError) as exc:
            validate_create({"title": "   ", "body": "body"})

        assert "title cannot be empty" in str(exc.value)

    def test_title_too_long(self):
        """Should raise ValidationError for title > 200 chars."""
        long_title = "x" * 201
        with pytest.raises(ValidationError) as exc:
            validate_create({"title": long_title, "body": "body"})

        assert "title must be 200 characters or less" in str(exc.value)

    def test_empty_body(self):
        """Should raise ValidationError for empty body."""
        with pytest.raises(ValidationError) as exc:
            validate_create({"title": "title", "body": ""})

        assert "body is required" in str(exc.value)

    def test_category_too_long(self):
        """Should raise ValidationError for category > 50 chars."""
        long_category = "x" * 51
        with pytest.raises(ValidationError) as exc:
            validate_create(
                {"title": "title", "body": "body", "category": long_category}
            )

        assert "category must be 50 characters or less" in str(exc.value)

    def test_tags_too_long(self):
        """Should raise ValidationError for tag > 30 chars."""
        long_tag = "x" * 31
        with pytest.raises(ValidationError) as exc:
            validate_create({"title": "title", "body": "body", "tags": [long_tag]})

        assert "tag" in str(exc.value).lower() and "30" in str(exc.value)

    def test_too_many_tags(self):
        """Should raise ValidationError for > 20 tags."""
        tags = [f"tag{i}" for i in range(21)]
        with pytest.raises(ValidationError) as exc:
            validate_create({"title": "title", "body": "body", "tags": tags})

        assert "20 tags" in str(exc.value)

    def test_tag_comma_separated(self):
        """Should parse comma-separated tags."""
        payload = {
            "title": "title",
            "body": "body",
            "tags": "tag1, TAG2,  tag3  ",
        }

        result = validate_create(payload)
        assert result["tags"] == ["tag1", "tag2", "tag3"]


class TestValidateUpdate:
    """Tests for validate_update()."""

    def test_partial_update(self):
        """Should handle partial updates."""
        payload = {"title": "New Title"}

        result = validate_update(payload)
        assert result == {"title": "New Title"}

    def test_empty_title_rejected(self):
        """Should reject empty title in update."""
        with pytest.raises(ValidationError) as exc:
            validate_update({"title": "", "body": "body"})

        assert "title is required" in str(exc.value)

    def test_no_valid_fields(self):
        """Should return empty dict when no valid fields provided."""
        result = validate_update({})
        assert result == {}


class TestCategoryValidation:
    """Tests for validate_category() and validate_tags()."""

    def test_validate_category_valid(self):
        """Should return lowercased category."""
        result = validate_category("Research")
        assert result == "research"

    def test_validate_category_none(self):
        """Should return None for None input."""
        result = validate_category(None)
        assert result is None

    def test_validate_category_empty_string(self):
        """Should return None for empty string."""
        result = validate_category("")
        assert result is None

    def test_validate_category_too_long(self):
        """Should raise ValidationError for category > 50 chars."""
        long_category = "x" * 51
        with pytest.raises(ValidationError) as exc:
            validate_category(long_category)

        assert "category must be 50 characters or less" in str(exc.value)

    def test_validate_tags_valid(self):
        """Should return lowercased, deduplicated tags."""
        result = validate_tags(["Python", "python", "Testing"])
        assert result == ["python", "testing"]

    def test_validate_tags_none(self):
        """Should return empty list for None input."""
        result = validate_tags(None)
        assert result == []

    def test_validate_tags_not_list(self):
        """Should raise ValidationError for non-list, non-string input."""
        with pytest.raises(ValidationError) as exc:
            validate_tags({"tag1": "value"})

        assert "tags must be a list or comma-separated string" in str(exc.value)

    def test_validate_tags_item_too_long(self):
        """Should raise ValidationError for tag > 30 chars."""
        long_tag = "x" * 31
        with pytest.raises(ValidationError) as exc:
            validate_tags([long_tag])

        assert "30 characters" in str(exc.value)
