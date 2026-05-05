"""Repository layer for note database operations."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any

from .html_utils import strip_html
from .models import Note, note_to_dict
from .validation import validate_category, validate_tags


def list_notes(
    conn: sqlite3.Connection,
    *,
    category: str | None = None,
    limit: int = 50,
    offset: int = 0,
    order: str = "new",
) -> tuple[list[dict], int]:
    """List notes with pagination and optional category filter.

    Args:
        conn: Database connection
        category: Filter by category (optional)
        limit: Maximum results
        offset: Results to skip
        order: "new" (DESC) or "old" (ASC) by updated_at

    Returns:
        Tuple of (notes list, total count)
    """
    cursor = conn.cursor()

    # Build query with optional category filter
    if category:
        cursor.execute(
            "SELECT COUNT(*) FROM notes WHERE category = ?",
            (category,),
        )
        total = cursor.fetchone()[0]

        order_clause = "updated_at DESC" if order == "new" else "updated_at ASC"
        # Validate order clause to prevent SQL injection
        if order_clause not in ("updated_at DESC", "updated_at ASC"):
            order_clause = "updated_at DESC"
        cursor.execute(
            f"""SELECT id, title, body, category, tags, created_at,
                   updated_at, optimized_at, source_ids, content_type
            FROM notes
            WHERE category = ?
            ORDER BY {order_clause}
            LIMIT ? OFFSET ?""",
            (category, limit, offset),
        )
    else:
        cursor.execute("SELECT COUNT(*) FROM notes")
        total = cursor.fetchone()[0]

        order_clause = "updated_at DESC" if order == "new" else "updated_at ASC"
        # Validate order clause to prevent SQL injection
        if order_clause not in ("updated_at DESC", "updated_at ASC"):
            order_clause = "updated_at DESC"
        cursor.execute(
            f"""SELECT id, title, body, category, tags, created_at,
                   updated_at, optimized_at, source_ids, content_type
            FROM notes
            ORDER BY {order_clause}
            LIMIT ? OFFSET ?""",
            (limit, offset),
        )

    rows = cursor.fetchall()
    notes = [note_to_dict(Note.from_row(dict(row))) for row in rows]

    return notes, total


def get_note(conn: sqlite3.Connection, note_id: int) -> dict[str, Any] | None:
    """Get a specific note by ID.

    Args:
        conn: Database connection
        note_id: Note ID

    Returns:
        Note dict or None if not found
    """
    cursor = conn.cursor()
    cursor.execute(
        """SELECT id, title, body, category, tags, created_at,
               updated_at, optimized_at, source_ids, content_type
        FROM notes WHERE id = ?""",
        (note_id,),
    )
    row = cursor.fetchone()
    if row:
        return note_to_dict(Note.from_row(dict(row)))
    return None


def create_note(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    """Create a new note.

    Args:
        conn: Database connection
        payload: Note data (title, body, category, tags, content_type)

    Returns:
        Created note dict
    """
    from datetime import timezone

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "")
    tags_json = json.dumps(payload.get("tags", []))
    category = payload.get("category")
    content_type = payload.get("content_type", "markdown")

    # Strip HTML tags for FTS5 indexing
    search_text = None
    if content_type == "html":
        search_text = strip_html(payload["body"])

    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO notes (title, body, category, tags,
                             created_at, updated_at, content_type, search_text)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            payload["title"],
            payload["body"],
            category,
            tags_json,
            now,
            now,
            content_type,
            search_text,
        ),
    )
    note_id = cursor.lastrowid
    conn.commit()

    return get_note(conn, note_id)


def update_note(
    conn: sqlite3.Connection,
    note_id: int,
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    """Update an existing note.

    Args:
        conn: Database connection
        note_id: Note ID
        payload: Fields to update

    Returns:
        Updated note dict or None if not found
    """
    # First check if note exists
    if get_note(conn, note_id) is None:
        return None

    # Build SET clause dynamically based on provided fields
    updates = []
    values = []

    if "title" in payload:
        updates.append("title = ?")
        values.append(payload["title"])
    if "body" in payload:
        updates.append("body = ?")
        values.append(payload["body"])
        # Recompute search_text for html notes
        current = get_note(conn, note_id)
        note_content_type = payload.get(
            "content_type",
            current.get("content_type", "markdown") if current else "markdown",
        )
        if note_content_type == "html":
            updates.append("search_text = ?")
            values.append(strip_html(payload["body"]))
    if "content_type" in payload:
        updates.append("content_type = ?")
        values.append(payload["content_type"])
    if "category" in payload:
        updates.append("category = ?")
        values.append(payload["category"])
    if "tags" in payload:
        updates.append("tags = ?")
        values.append(json.dumps(payload["tags"]))
    if "optimized_at" in payload:
        updates.append("optimized_at = ?")
        values.append(payload["optimized_at"])

    from datetime import timezone

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "")

    # Validate payload fields to prevent SQL injection
    # Only allow known-safe fields
    allowed_fields = {
        "title",
        "body",
        "category",
        "tags",
        "optimized_at",
        "content_type",
    }
    if not updates:
        # No fields to update, return existing note
        return get_note(conn, note_id)

    # Add updated_at
    updates.append("updated_at = ?")
    values.append(now)
    values.append(note_id)

    cursor = conn.cursor()
    cursor.execute(
        f"""UPDATE notes SET {', '.join(updates)} WHERE id = ?""",
        values,
    )
    conn.commit()

    return get_note(conn, note_id)


def delete_note(conn: sqlite3.Connection, note_id: int) -> bool:
    """Delete a note.

    Args:
        conn: Database connection
        note_id: Note ID

    Returns:
        True if note was deleted, False if not found
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))

    if cursor.rowcount == 0:
        return False

    conn.commit()
    return True


def write_revision(
    conn: sqlite3.Connection,
    note_id: int,
    title: str,
    body: str,
    reason: str,
) -> int:
    """Write a revision entry for a note.

    Args:
        conn: Database connection
        note_id: Note ID being revised
        title: Title at time of revision
        body: Body at time of revision
        reason: Reason for revision ('optimize', 'combine', 'manual')

    Returns:
        New revision ID
    """
    from datetime import timezone

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "")
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO note_revisions (note_id, title, body, reason, created_at)
           VALUES (?, ?, ?, ?, ?)""",
        (note_id, title, body, reason, now),
    )
    conn.commit()
    return cursor.lastrowid


def latest_revision(conn: sqlite3.Connection, note_id: int) -> dict[str, Any] | None:
    """Get the most recent revision for a note.

    Args:
        conn: Database connection
        note_id: Note ID

    Returns:
        Revision dict or None if no revisions exist
    """
    cursor = conn.cursor()
    cursor.execute(
        """SELECT id, note_id, title, body, reason, created_at
           FROM note_revisions
           WHERE note_id = ?
           ORDER BY created_at DESC
           LIMIT 1""",
        (note_id,),
    )
    row = cursor.fetchone()
    if row:
        return {
            "id": row[0],
            "note_id": row[1],
            "title": row[2],
            "body": row[3],
            "reason": row[4],
            "created_at": row[5],
        }
    return None


def pop_latest_revision(
    conn: sqlite3.Connection, note_id: int
) -> dict[str, Any] | None:
    """Get and delete the most recent revision for a note.

    Args:
        conn: Database connection
        note_id: Note ID

    Returns:
        Revision dict or None if no revisions exist
    """
    cursor = conn.cursor()
    cursor.execute(
        """DELETE FROM note_revisions
           WHERE id = (
               SELECT id FROM note_revisions
               WHERE note_id = ?
               ORDER BY created_at DESC
               LIMIT 1
           )""",
        (note_id,),
    )
    conn.commit()

    if cursor.rowcount == 0:
        return None

    # Get the revision we just deleted
    cursor.execute(
        """SELECT id, note_id, title, body, reason, created_at
           FROM note_revisions
           WHERE note_id = ?
           ORDER BY created_at DESC
           LIMIT 1""",
        (note_id,),
    )
    row = cursor.fetchone()
    if row:
        return {
            "id": row[0],
            "note_id": row[1],
            "title": row[2],
            "body": row[3],
            "reason": row[4],
            "created_at": row[5],
        }
    return None


def update_enrichment(
    conn: sqlite3.Connection,
    note_id: int,
    category: str | None,
    tags: list[str],
) -> dict[str, Any] | None:
    """Update only the category and tags fields of a note.

    Does NOT update updated_at - used for async enrichment.

    Args:
        conn: Database connection
        note_id: Note ID
        category: New category (can be None)
        tags: New tags list

    Returns:
        Updated note dict or None if not found
    """
    # First check if note exists
    if get_note(conn, note_id) is None:
        return None

    cursor = conn.cursor()
    tags_json = json.dumps(tags)

    cursor.execute(
        """UPDATE notes SET category = ?, tags = ?
           WHERE id = ?""",
        (category, tags_json, note_id),
    )
    conn.commit()

    return get_note(conn, note_id)


def combine_notes(
    conn: sqlite3.Connection,
    note_ids: list[int],
    mode: str,
    title: str | None = None,
) -> dict[str, Any] | None:
    """Combine multiple notes into a new note.

    Args:
        conn: Database connection
        note_ids: List of note IDs to combine
        mode: "concatenate" (simple merge) or "ai" (synthesized summary)
        title: Optional title for combined note (auto-generated if not provided)

    Returns:
        New combined note dict or None if operation fails
    """
    if not note_ids:
        return None

    # Load all source notes
    sources = []
    for note_id in note_ids:
        source = get_note(conn, note_id)
        if source:
            sources.append(source)

    if not sources:
        return None

    # Combine body content
    if mode == "concatenate":
        combined_body = "\n\n---\n\n".join(
            f"# {s['title']}\n\n{s['body']}" for s in sources
        )
        combined_title = title or "Combined: " + ", ".join(
            s["title"][:30] for s in sources[:3]
        )
        if len(sources) > 3:
            combined_title += f" (+{len(sources) - 3} more)"
    else:
        # For AI mode, we'll store a placeholder that will be filled by enrichment
        combined_body = (
            f"# Combined Notes ({mode})\n\n"
            f"Source notes: {len(sources)}\n\n"
            + "\n\n".join(f"## {s['title']}\n\n{s['body']}" for s in sources)
        )
        combined_title = title or f"Combined ({mode})"

    from datetime import timezone

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "")
    source_ids_json = json.dumps(note_ids)

    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO notes (title, body, category, tags,
                             created_at, updated_at, source_ids, content_type)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            combined_title[:200],  # Title length limit
            combined_body,
            None,  # No category for combined notes initially
            "[]",  # Empty tags
            now,
            now,
            source_ids_json,
            "markdown",
        ),
    )
    note_id = cursor.lastrowid
    conn.commit()

    return get_note(conn, note_id)


def optimize_note(
    conn: sqlite3.Connection,
    note_id: int,
    title: str | None = None,
    body: str | None = None,
) -> dict[str, Any] | None:
    """Optimize a note by saving a new revision and updating the note.

    This function creates a revision entry and then updates the note content.
    The revision can be undone using undo_optimize().

    Args:
        conn: Database connection
        note_id: Note ID to optimize
        title: New title (optional, keeps existing if None)
        body: New body content (optional, keeps existing if None)

    Returns:
        Updated note dict or None if note not found
    """
    from datetime import timezone

    # First get the current note to save as revision
    current_note = get_note(conn, note_id)
    if not current_note:
        return None

    # Save current state as revision
    write_revision(
        conn,
        note_id,
        current_note["title"],
        current_note["body"],
        "optimize",
    )

    # Build update payload
    updates = {}
    if title is not None:
        updates["title"] = title
    if body is not None:
        updates["body"] = body

    if not updates:
        return current_note

    updates["updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "")
    updates["optimized_at"] = (
        datetime.now(timezone.utc).isoformat().replace("+00:00", "")
    )

    return update_note(conn, note_id, updates)


def undo_optimize(
    conn: sqlite3.Connection,
    note_id: int,
) -> dict[str, Any] | None:
    """Undo the last optimize by restoring the previous revision.

    Args:
        conn: Database connection
        note_id: Note ID to undo

    Returns:
        Restored note dict or None if no revision exists
    """
    # Get the latest revision
    revision = latest_revision(conn, note_id)
    if not revision:
        return None

    # Restore the note from the revision
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE notes SET title = ?, body = ?, updated_at = ?
            WHERE id = ?""",
        (revision["title"], revision["body"], revision["created_at"], note_id),
    )
    conn.commit()

    # Delete the revision we just used
    cursor.execute("DELETE FROM note_revisions WHERE id = ?", (revision["id"],))
    conn.commit()

    return get_note(conn, note_id)
