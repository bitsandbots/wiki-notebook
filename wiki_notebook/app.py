"""Flask application factory."""

from __future__ import annotations

import json
from http import HTTPStatus

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from .config import config
from .db import check_schema, init_db


def register_static_routes(app):
    """Register static file serving and root route."""
    import os
    from pathlib import Path

    from flask import current_app, send_from_directory

    # Static files route
    static_dir = Path(__file__).parent.parent / "static"
    app.static_folder = str(static_dir)

    # Root route - serve index.html
    @app.route("/")
    def index():
        """Serve the main HTML page."""
        return send_from_directory(str(static_dir), "index.html")

    # Static file serving
    @app.route("/static/<path:path>")
    def serve_static(path):
        """Serve static files."""
        return send_from_directory(str(static_dir), path)


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Configure app
    app.config["bind_host"] = config.bind_host
    app.config["port"] = config.port
    app.config["db_path"] = config.db_path

    # Initialize database on startup
    init_db(config.db_path)
    conn = None
    try:
        import sqlite3

        conn = sqlite3.connect(config.db_path, timeout=10)
        check_schema(conn)
    finally:
        if conn:
            conn.close()

    # Register blueprints
    from .routes.health import health_bp
    from .routes.notes import notes_bp
    from .routes.search import search_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(notes_bp, url_prefix="/api/notes")
    app.register_blueprint(search_bp)

    # Register static routes
    register_static_routes(app)

    # Initialize enrichment worker
    from .ai.worker import EnrichmentWorker
    from .repository import (
        create_note,
        delete_note,
        get_note,
        list_notes,
        update_enrichment,
        update_note,
    )

    # Create a mock config for testing
    class RepoMock:
        pass

    class MockRepo:
        def get_note(self, conn, note_id):
            return get_note(conn, note_id)

        def update_enrichment(self, conn, note_id, category, tags):
            return update_enrichment(conn, note_id, category, tags)

    enrichment = EnrichmentWorker(config, MockRepo())
    enrichment.start()

    # Store on app for routes to access
    app.extensions["enrichment"] = enrichment

    # Register teardown to stop worker on shutdown
    @app.teardown_appcontext
    def shutdown_worker(exception=None):
        if "enrichment" in app.extensions:
            app.extensions["enrichment"].stop()

    # Error handlers for JSON responses
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """Return JSON error response for HTTP exceptions."""
        response = e.get_response()
        response.data = json.dumps(
            {"error": {"code": e.name, "message": e.description}}
        )
        response.content_type = "application/json"
        return response

    @app.errorhandler(Exception)
    def handle_exception(e):
        """Return JSON error response for unhandled exceptions."""
        app.logger.exception("Unhandled exception")
        return {
            "error": {
                "code": "internal_server_error",
                "message": "An unexpected error occurred",
            }
        }, HTTPStatus.INTERNAL_SERVER_ERROR

    return app
