"""Search module for FTS5-backed querying and indexing."""

from __future__ import annotations

import re
from typing import Any

import sqlite3


def sanitize_query(q: str) -> str:
    """Sanitize user query for FTS5 by escaping special characters.

    FTS5 special chars: " * : ^ | &
    We escape them by wrapping in quotes as literal text tokens.
    This makes them behave as search terms rather than operators.
    """
    if not q:
        return ""

    # Replace FTS5 special characters with quoted versions
    # This forces them to be treated as literal text tokens
    escaped = q
    for char in ['"', "*", ":", "^", "|", "&"]:
        escaped = escaped.replace(char, f'"{char}"')

    # Collapse multiple spaces, strip
    escaped = re.sub(r"\s+", " ", escaped).strip()

    # Limit length
    if len(escaped) > 200:
        escaped = escaped[:200].strip()

    return escaped


def is_short_query(q: str) -> bool:
    """Check if query is too short for FTS5 (less than 3 chars after strip)."""
    return len(q.strip()) < 3


def fts_search(
    conn: sqlite3.Connection,
    q: str,
    *,
    category: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """Search notes using FTS5 with BM25 ranking.

    Args:
        conn: Database connection
        q: Search query (already sanitized)
        category: Filter by category (optional)
        limit: Maximum results
        offset: Results to skip

    Returns:
        Tuple of (search results, total count)
    """
    cursor = conn.cursor()

    # Build the base query
    base_query = """
        SELECT n.id,
               snippet(notes_fts, -1, '<mark>', '</mark>', '…', 16) AS snippet,
               bm25(notes_fts) AS score,
               n.title, n.category, n.tags, n.updated_at
        FROM notes_fts
        JOIN notes n ON n.id = notes_fts.rowid
        WHERE notes_fts MATCH :q
    """

    if category:
        base_query += " AND n.category = :category"

    base_query += " ORDER BY bm25(notes_fts) LIMIT :limit OFFSET :offset"

    # Get total count first
    count_query = f"""
        SELECT COUNT(*) FROM (
            {base_query.replace(' LIMIT :limit OFFSET :offset', '')}
        )
    """

    params: dict[str, Any] = {"q": q, "limit": limit, "offset": offset}
    if category:
        params["category"] = category

    # Get count
    cursor.execute(count_query, params)
    total = cursor.fetchone()[0]

    # Get results
    cursor.execute(base_query, params)
    rows = cursor.fetchall()

    results = []
    for row in rows:
        results.append(
            {
                "id": row["id"],
                "title": row["title"],
                "snippet": row["snippet"],
                "category": row["category"],
                "tags": row["tags"],
                "updated_at": row["updated_at"],
                "score": row["score"],
            }
        )

    return results, total


def like_search(
    conn: sqlite3.Connection,
    q: str,
    *,
    category: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """Fallback search using LIKE for very short queries.

    Args:
        conn: Database connection
        q: Search query
        category: Filter by category (optional)
        limit: Maximum results
        offset: Results to skip

    Returns:
        Tuple of (search results, total count)
    """
    cursor = conn.cursor()

    # For LIKE search, we search in title and body
    search_pattern = f"%{q}%"

    # Build base query
    base_query = """
        SELECT id, title, body, category, tags, created_at, updated_at,
               optimized_at, source_ids
        FROM notes
        WHERE (title LIKE :q OR body LIKE :q)
    """

    if category:
        base_query += " AND category = :category"

    base_query += " ORDER BY updated_at DESC LIMIT :limit OFFSET :offset"

    # Get total count
    count_query = f"""
        SELECT COUNT(*) FROM (
            {base_query.replace(' ORDER BY updated_at DESC LIMIT :limit OFFSET :offset', '')}
        )
    """

    params: dict[str, Any] = {"q": search_pattern, "limit": limit, "offset": offset}
    if category:
        params["category"] = category

    # Get count
    cursor.execute(count_query, params)
    total = cursor.fetchone()[0]

    # Get results
    cursor.execute(base_query, params)
    rows = cursor.fetchall()

    from .models import Note, note_to_dict

    results = []
    for row in rows:
        note = Note.from_row(dict(row))
        # Create a simple snippet for LIKE results
        # Highlight the matching term
        snippet = create_like_snippet(note.title, note.body, q)
        result = note_to_dict(note)
        result["snippet"] = snippet
        result["score"] = 0.0  # No BM25 score available for LIKE
        results.append(result)

    return results, total


def create_like_snippet(title: str, body: str, q: str) -> str:
    """Create a simple snippet for LIKE search results."""
    # Find the first occurrence of the query
    search_lower = q.lower()
    body_lower = body.lower()
    pos = body_lower.find(search_lower)

    if pos >= 0:
        # Extract context around the match (100 chars)
        start = max(0, pos - 50)
        end = min(len(body), pos + 50)
        snippet = body[start:end]

        # Highlight the match
        highlight_start = pos - start
        highlight_end = highlight_start + len(q)

        # Add ellipsis if we truncated
        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(body) else ""

        return f"{prefix}{snippet[:highlight_start]}<mark>{q}</mark>{snippet[highlight_end:]}{suffix}"

    # If no match in body, try title
    title_pos = title.lower().find(search_lower)
    if title_pos >= 0:
        prefix = "..." if title_pos > 0 else ""
        suffix = "..." if title_pos + len(q) < len(title) else ""
        return f"{prefix}<mark>{q}</mark>{suffix}"

    # Fallback
    return body[:100] + "..." if len(body) > 100 else body
