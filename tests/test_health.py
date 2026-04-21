"""Tests for the health check endpoint."""

from __future__ import annotations

import pytest


class TestHealth:
    """Health check endpoint tests."""

    def test_health_check_returns_ok(self, client):
        """Health check endpoint returns status ok."""
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"

    def test_health_includes_db_status(self, client):
        """Health check includes database status."""
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "db" in data
        assert "ok" in data["db"]
        assert "path" in data["db"]
        assert isinstance(data["db"]["ok"], bool)

    def test_health_includes_ollama_status(self, client):
        """Health check includes Ollama status."""
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "ollama" in data
        assert "reachable" in data["ollama"]
        assert "url" in data["ollama"]
        assert "model" in data["ollama"]
        assert isinstance(data["ollama"]["reachable"], bool)

    def test_health_includes_enrichment_stats(self, client):
        """Health endpoint includes enrichment queue metrics."""
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "enrichment_queue_size" in data
        assert isinstance(data["enrichment_queue_size"], int)
        assert data["enrichment_queue_size"] >= 0
