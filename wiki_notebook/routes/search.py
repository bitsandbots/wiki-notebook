"""Search routes for FTS5-backed queries and categories."""

from __future__ import annotations

from flask import Blueprint, request, jsonify

from ..db import get_conn
from ..validation import ValidationError
from ..search import fts_search, is_short_query, like_search, sanitize_query

search_bp = Blueprint("search", __name__, url_prefix="/api")


@search_bp.route("/search", methods=["GET"])
def search_notes():
    """Search notes using FTS5 with BM25 ranking.

    Query params:
        q: Search query (required, 1-200 chars)
        category: Filter by category (optional)
        limit: Max results (default 50)
        offset: Results to skip (default 0)
    """
    q = request.args.get("q", "").strip()

    # Validate query
    if not q:
        return (
            jsonify(
                {
                    "error": {
                        "code": "validation_failed",
                        "message": "query parameter 'q' is required",
                    }
                }
            ),
            422,
        )

    if len(q) > 200:
        return (
            jsonify(
                {
                    "error": {
                        "code": "validation_failed",
                        "message": "query must be 200 characters or less",
                    }
                }
            ),
            422,
        )

    # Sanitize the query
    sanitized = sanitize_query(q)

    # Check if query is too short for FTS5
    use_fts = not is_short_query(q)

    # Get search params
    category = request.args.get("category")
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)

    conn = get_conn()
    try:
        if use_fts:
            items, total = fts_search(
                conn,
                sanitized,
                category=category,
                limit=limit,
                offset=offset,
            )
        else:
            # Fallback to LIKE search for short queries
            items, total = like_search(
                conn,
                q,
                category=category,
                limit=limit,
                offset=offset,
            )

        return jsonify(
            {
                "items": items,
                "total": total,
                "limit": limit,
                "offset": offset,
                "q": q,
            }
        )
    finally:
        conn.close()


@search_bp.route("/categories", methods=["GET"])
def list_categories():
    """List all note categories with counts.

    Returns a sorted list of categories with their note counts,
    useful for UI filter chips.
    """
    conn = get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM notes
            WHERE category IS NOT NULL AND category != ''
            GROUP BY category
            ORDER BY count DESC
        """)

        rows = cursor.fetchall()
        categories = [{"name": row["category"], "count": row["count"]} for row in rows]

        return jsonify({"items": categories})
    finally:
        conn.close()
