"""AI enrichment module for Ollama integration."""

from __future__ import annotations

from .ollama_client import OllamaClient, OllamaError

__all__ = ["OllamaClient", "OllamaError"]
