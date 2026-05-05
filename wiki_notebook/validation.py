"""Input validation for notes API."""

from __future__ import annotations

import re
from typing import Any


class ValidationError(Exception):
    """Raised when input validation fails."""


def validate_title(title: str) -> str:
    """Validate and sanitize title.

    Args:
        title: Raw title string

    Returns:
        Sanitized title (stripped, length validated)

    Raises:
        ValidationError: If title is empty or too long
    """
    if not title:
        raise ValidationError("title is required")

    stripped = title.strip()
    if not stripped:
        raise ValidationError("title cannot be empty")

    if len(stripped) > 200:
        raise ValidationError("title must be 200 characters or less")

    return stripped


def validate_body(body: str) -> str:
    """Validate and sanitize body.

    Args:
        body: Raw body string

    Returns:
        Sanitized body (stripped)

    Raises:
        ValidationError: If body is empty
    """
    if not body:
        raise ValidationError("body is required")

    return body.strip()


def validate_category(category: str | None) -> str | None:
    """Validate and sanitize category.

    Args:
        category: Raw category string or None

    Returns:
        Lowercased, trimmed category or None

    Raises:
        ValidationError: If category is too long
    """
    if not category:
        return None

    stripped = category.strip()
    if len(stripped) > 50:
        raise ValidationError("category must be 50 characters or less")

    return stripped.lower()


def validate_tags(tags: Any) -> list[str]:
    """Validate and normalize tags.

    Accepts either a list of strings or a comma-separated string.

    Args:
        tags: Tags input

    Returns:
        Deduplicated, lowercased tag list (max 20 tags)

    Raises:
        ValidationError: If tags are invalid
    """
    if tags is None:
        return []

    tag_list: list[str] = []

    if isinstance(tags, str):
        # Parse comma-separated string
        tag_list = [t.strip() for t in tags.split(",")]
    elif isinstance(tags, list):
        tag_list = tags
    else:
        raise ValidationError("tags must be a list or comma-separated string")

    # Process tags: validate length, dedupe, lowercase
    seen = set()
    result = []

    for tag in tag_list:
        if not tag:
            continue
        if len(tag) > 30:
            raise ValidationError(f"tag '{tag}' exceeds 30 characters")

        normalized = tag.strip().lower()
        if normalized not in seen:
            seen.add(normalized)
            result.append(normalized)

    if len(result) > 20:
        raise ValidationError("maximum 20 tags allowed")

    return result


def validate_create(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate create note payload.

    Args:
        payload: Request body dict

    Returns:
        Cleaned payload dict

    Raises:
        ValidationError: If validation fails
    """
    content_type = payload.get("content_type", "markdown")
    if content_type not in ("markdown", "html"):
        content_type = "markdown"

    result = {
        "title": validate_title(payload.get("title", "")),
        "body": validate_body(payload.get("body", "")),
        "category": validate_category(payload.get("category")),
        "tags": validate_tags(payload.get("tags")),
        "content_type": content_type,
    }

    # Set defaults for empty values
    if not result["category"]:
        result["category"] = None
    if not result["tags"]:
        result["tags"] = []

    return result


def validate_update(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate update note payload (allows partial updates).

    Args:
        payload: Request body dict

    Returns:
        Cleaned payload dict (only contains validated fields)
    """
    result = {}

    if "title" in payload:
        result["title"] = validate_title(payload["title"])

    if "body" in payload:
        result["body"] = validate_body(payload["body"])

    if "category" in payload:
        result["category"] = validate_category(payload["category"])

    if "tags" in payload:
        result["tags"] = validate_tags(payload["tags"])

    return result
