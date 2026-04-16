# routes/__init__.py
"""Route blueprints package."""

from .health import health_bp
from .notes import notes_bp

__all__ = ["health_bp", "notes_bp"]
