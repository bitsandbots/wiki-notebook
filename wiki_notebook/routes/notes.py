"""Notes CRUD routes."""

from __future__ import annotations

from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, current_app

from ..config import config
from ..db import get_conn
from ..repository import (
    combine_notes,
    create_note,
    delete_note,
    get_note,
    list_notes,
    optimize_note,
    undo_optimize,
    update_note,
)
from ..validation import (
    ValidationError,
    validate_category,
    validate_create,
    validate_tags,
    validate_update,
)

notes_bp = Blueprint("notes", __name__, url_prefix="/api/notes")


def _is_user_supplied_category(payload: dict) -> bool:
    """Check if user provided both category and tags."""
    return "category" in payload and "tags" in payload


def _should_enqueue_enrichment(payload: dict) -> bool:
    """Determine if enrichment should be enqueued.

    Enrichment is skipped if user provided both category and tags.
    """
    if not isinstance(payload, dict):
        return True

    has_category = "category" in payload
    has_tags = "tags" in payload

    return not (has_category and has_tags)


@notes_bp.route("", methods=["GET"])
def list_notes_route():
    """List notes with pagination and filters."""
    category = request.args.get("category")
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)
    order = request.args.get("order", "new")

    conn = get_conn()
    try:
        items, total = list_notes(
            conn,
            category=category,
            limit=limit,
            offset=offset,
            order=order,
        )
        return jsonify(
            {
                "items": items,
                "total": total,
                "limit": limit,
                "offset": offset,
            }
        )
    finally:
        conn.close()


@notes_bp.route("", methods=["POST"])
def create_note_route():
    """Create a new note."""
    payload = request.get_json()

    if not payload:
        return (
            jsonify(
                {
                    "error": {
                        "code": "validation_failed",
                        "message": "request body required",
                    }
                }
            ),
            422,
        )

    try:
        cleaned = validate_create(payload)
    except ValidationError as e:
        return jsonify({"error": {"code": "validation_failed", "message": str(e)}}), 422

    conn = get_conn()
    try:
        note = create_note(conn, cleaned)

        # Enqueue enrichment if user didn't provide category and tags
        if _should_enqueue_enrichment(payload):
            app = current_app._get_current_object()
            if "enrichment" in app.extensions:
                enrichment = app.extensions["enrichment"]
                enrichment.enqueue(note["id"])

        return jsonify(note), 201
    finally:
        conn.close()


@notes_bp.route("/<int:id>", methods=["GET"])
def get_note_route(id):
    """Get a specific note."""
    conn = get_conn()
    try:
        note = get_note(conn, id)
        if note:
            # Add enrichment_pending flag for notes < 60 seconds old
            # without category/tags set
            if note.get("category") is None:
                created = note["created_at"]
                now = datetime.now(timezone.utc).isoformat().replace("+00:00", "")
                # Simple check: if created recently (< 60s)
                try:
                    created_dt = datetime.fromisoformat(created)
                    now_dt = datetime.now(timezone.utc)
                    diff = (now_dt - created_dt).total_seconds()
                    if diff < 60:
                        note["enrichment_pending"] = True
                except Exception:
                    pass

            return jsonify(note)
        return (
            jsonify({"error": {"code": "not_found", "message": "note not found"}}),
            404,
        )
    finally:
        conn.close()


@notes_bp.route("/<int:id>", methods=["PUT"])
def update_note_route(id):
    """Update a note."""
    payload = request.get_json()

    if not payload:
        return (
            jsonify(
                {
                    "error": {
                        "code": "validation_failed",
                        "message": "request body required",
                    }
                }
            ),
            422,
        )

    try:
        cleaned = validate_update(payload)
    except ValidationError as e:
        return jsonify({"error": {"code": "validation_failed", "message": str(e)}}), 422

    if not cleaned:
        return (
            jsonify(
                {
                    "error": {
                        "code": "validation_failed",
                        "message": "no valid fields to update",
                    }
                }
            ),
            422,
        )

    conn = get_conn()
    try:
        note = update_note(conn, id, cleaned)
        if note:
            # Enqueue enrichment if user didn't provide category and tags
            # AND we're actually updating category or tags
            if _should_enqueue_enrichment(payload):
                if "category" in payload or "tags" in payload:
                    app = current_app._get_current_object()
                    if "enrichment" in app.extensions:
                        enrichment = app.extensions["enrichment"]
                        enrichment.enqueue(note["id"])

            return jsonify(note)
        return (
            jsonify({"error": {"code": "not_found", "message": "note not found"}}),
            404,
        )
    finally:
        conn.close()


@notes_bp.route("/<int:id>", methods=["DELETE"])
def delete_note_route(id):
    """Delete a note."""
    conn = get_conn()
    try:
        if delete_note(conn, id):
            return "", 204
        return (
            jsonify({"error": {"code": "not_found", "message": "note not found"}}),
            404,
        )
    finally:
        conn.close()


@notes_bp.route("/<int:id>/optimize", methods=["POST"])
def optimize_note_route(id):
    """Optimize a note by rewriting its content with AI.

    Creates a revision for undo support and updates the note with
    improved content (clarity, conciseness, grammar).

    Body params:
        title: Optional new title
        body: Optional new body content

    If neither title nor body is provided, only creates a revision
    (no content changes).
    """
    payload = request.get_json()

    if not payload or not isinstance(payload, dict):
        return (
            jsonify(
                {
                    "error": {
                        "code": "validation_failed",
                        "message": "request body required",
                    }
                }
            ),
            422,
        )

    title = payload.get("title")
    body = payload.get("body")

    conn = get_conn()
    try:
        note = optimize_note(conn, id, title, body)
        if note:
            return jsonify(note)
        return (
            jsonify({"error": {"code": "not_found", "message": "note not found"}}),
            404,
        )
    finally:
        conn.close()


@notes_bp.route("/<int:id>/undo", methods=["POST"])
def undo_optimize_route(id):
    """Undo the last optimize by restoring the previous revision."""
    conn = get_conn()
    try:
        note = undo_optimize(conn, id)
        if note:
            return jsonify(note)
        return (
            jsonify({"error": {"code": "not_found", "message": "no revision to undo"}}),
            404,
        )
    finally:
        conn.close()


@notes_bp.route("/combine", methods=["POST"])
def combine_notes_route():
    """Combine multiple notes into a new note."""
    payload = request.get_json()

    if not payload:
        return (
            jsonify(
                {
                    "error": {
                        "code": "validation_failed",
                        "message": "request body required",
                    }
                }
            ),
            422,
        )

    # Validate note_ids
    note_ids = payload.get("note_ids")
    if not note_ids or not isinstance(note_ids, list) or len(note_ids) < 2:
        return (
            jsonify(
                {
                    "error": {
                        "code": "validation_failed",
                        "message": "note_ids must be a list with at least 2 note IDs",
                    }
                }
            ),
            422,
        )

    # Validate mode
    mode = payload.get("mode", "concatenate")
    if mode not in ("concatenate", "ai"):
        return (
            jsonify(
                {
                    "error": {
                        "code": "validation_failed",
                        "message": "mode must be 'concatenate' or 'ai'",
                    }
                }
            ),
            422,
        )

    # Validate title if provided
    title = payload.get("title")
    if title is not None and (not isinstance(title, str) or len(title) > 200):
        return (
            jsonify(
                {
                    "error": {
                        "code": "validation_failed",
                        "message": "title must be a string with max 200 characters",
                    }
                }
            ),
            422,
        )

    conn = get_conn()
    try:
        note = combine_notes(conn, note_ids, mode, title)
        if note:
            return jsonify(note), 201
        return (
            jsonify({"error": {"code": "not_found", "message": "notes not found"}}),
            404,
        )
    finally:
        conn.close()


@notes_bp.route("/<int:id>/categorize", methods=["POST"])
def categorize_note_route(id: int) -> tuple:
    """Manually trigger categorization for a note.

    Re-categorizes the note using Ollama if available, or keyword fallback.
    Updates category and tags, preserving other note fields.

    Args:
        id: Note ID to categorize

    Returns:
        Updated note with new category and tags (200) or error (4xx/5xx)
    """
    import logging

    from ..ai.categorize import categorize

    logger = logging.getLogger(__name__)

    # Validate note ID
    if not isinstance(id, int) or id < 1:
        return (
            jsonify(
                {
                    "error": {
                        "code": "invalid_input",
                        "message": "invalid note ID",
                    }
                }
            ),
            400,
        )

    conn = get_conn()
    try:
        note = get_note(conn, id)
        if not note:
            return (
                jsonify(
                    {
                        "error": {
                            "code": "not_found",
                            "message": "note not found",
                        }
                    }
                ),
                404,
            )

        # Validate note has content
        if not note.get("title") or not note.get("body"):
            return (
                jsonify(
                    {
                        "error": {
                            "code": "invalid_state",
                            "message": ("note must have title and body to categorize"),
                        }
                    }
                ),
                400,
            )

        try:
            # Run categorization
            result = categorize(note["title"], note["body"])

            # Validate result before updating
            try:
                validated_category = validate_category(result["category"])
                validated_tags = validate_tags(result["tags"])
            except ValidationError as e:
                logger.warning(f"Categorization result validation failed: {e}")
                return (
                    jsonify(
                        {
                            "error": {
                                "code": "invalid_input",
                                "message": f"Invalid categorization result: {str(e)}",
                            }
                        }
                    ),
                    400,
                )

            # Update the note with new category and tags
            update_payload = {
                "category": validated_category,
                "tags": validated_tags,
            }
            updated_note = update_note(conn, id, update_payload)

            # Enrich response with confidence and suggestions
            response_data = dict(updated_note)
            response_data["confidence"] = result.get("confidence", 0)
            response_data["suggestions"] = result.get("suggestions", [])

            return jsonify(response_data), 200
        except Exception as e:
            logger.exception(f"Categorization failed for note {id}")

            return (
                jsonify(
                    {
                        "error": {
                            "code": "categorization_failed",
                            "message": "Failed to categorize note",
                        }
                    }
                ),
                500,
            )
    finally:
        conn.close()
