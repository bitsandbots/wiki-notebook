"""Configuration loaded from environment with sane defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Config:
    """Application configuration - mutable for testing."""

    bind_host: str
    port: int
    db_path: str
    ollama_url: str
    ollama_model: str
    ollama_timeout: int
    optimize_tone: str


def _load_config() -> Config:
    """Load configuration from environment variables with defaults."""
    return Config(
        bind_host=os.getenv("BIND_HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5000")),
        db_path=os.getenv("DB_PATH", "./data/notebook.db"),
        ollama_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
        ollama_model=os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct"),
        ollama_timeout=int(os.getenv("OLLAMA_TIMEOUT", "30")),
        optimize_tone=os.getenv("OPTIMIZE_TONE", "balanced, professional, clear"),
    )


# Singleton instance - loaded once on import
config = _load_config()
