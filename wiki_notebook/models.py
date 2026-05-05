"""Data models for notes."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class Note:
    """Note model matching the database schema."""

    id: int | None
    title: str
    body: str
    category: str | None
    tags: list[str]
    created_at: str
    updated_at: str
    optimized_at: str | None
    source_ids: list[int] | None
    content_type: str = "markdown"

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Note":
        """Create a Note from a database row."""
        return cls(
            id=row["id"],
            title=row["title"],
            body=row["body"],
            category=row.get("category"),
            tags=json.loads(row.get("tags", "[]")) if row.get("tags") else [],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            optimized_at=row.get("optimized_at"),
            source_ids=(
                json.loads(row.get("source_ids", "[]")) if row.get("source_ids") else []
            ),
            content_type=row.get("content_type", "markdown"),
        )


def note_to_dict(note: Note) -> dict[str, Any]:
    """Convert a Note to a dictionary for JSON serialization."""
    return {
        "id": note.id,
        "title": note.title,
        "body": note.body,
        "category": note.category,
        "tags": note.tags,
        "created_at": note.created_at,
        "updated_at": note.updated_at,
        "optimized_at": note.optimized_at,
        "source_ids": note.source_ids,
        "content_type": note.content_type,
    }
