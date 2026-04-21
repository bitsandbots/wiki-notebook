"""Health check route."""

from __future__ import annotations

import json
from http import HTTPStatus

import requests
from flask import Blueprint, jsonify, current_app

from ..config import config

health_bp = Blueprint("health", __name__)


@health_bp.route("/api/health", methods=["GET"])
def health_check() -> tuple[dict, int]:
    """Return health status for app, DB, and Ollama."""
    db_ok = True
    db_path = current_app.config.get("db_path", config.db_path)

    # Check database connectivity
    try:
        import sqlite3

        conn = sqlite3.connect(db_path, timeout=5)
        conn.execute("SELECT 1")
        conn.close()
    except Exception:
        db_ok = False

    # Check Ollama availability
    ollama_reachable = False
    ollama_url = config.ollama_url
    ollama_model = config.ollama_model

    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=2)
        ollama_reachable = response.status_code == HTTPStatus.OK
        if ollama_reachable:
            # Get actual model in use
            data = response.json()
            models = data.get("models", [])
            if models:
                # Find model matching our configured model
                for m in models:
                    if ollama_model in m.get("name", ""):
                        ollama_model = m.get("name", ollama_model)
                        break
    except (requests.exceptions.RequestException, ValueError, KeyError):
        ollama_reachable = False

    status = {
        "status": "ok",
        "db": {"ok": db_ok, "path": db_path},
        "ollama": {
            "reachable": ollama_reachable,
            "url": ollama_url,
            "model": ollama_model,
        },
    }

    # Add enrichment worker stats
    if "enrichment" in current_app.extensions:
        enrichment = current_app.extensions["enrichment"]
        status["enrichment_queue_size"] = enrichment.get_queue_size()

    return jsonify(status), HTTPStatus.OK
