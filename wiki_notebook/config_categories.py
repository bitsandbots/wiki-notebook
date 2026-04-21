"""Category configuration system supporting custom categories via environment variables."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# Default category keywords
DEFAULT_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "meetings": [
        "agenda",
        "attendees",
        "briefing",
        "call",
        "conference",
        "discussion",
        "meeting",
        "panel",
        "presentation",
        "roundtable",
        "seminar",
        "standup",
        "sync",
        "talk",
        "teams",
        "workshop",
        "zoom",
    ],
    "project ideas": [
        "concept",
        "design",
        "feature",
        "idea",
        "mockup",
        "MVP",
        "plan",
        "project",
        "proposal",
        "prototype",
        "requirements",
        "scope",
        "spec",
        "specification",
        "sprint",
        "vision",
        "wireframe",
    ],
    "journal": [
        "daily",
        "emotional",
        "entry",
        "feeling",
        "gratitude",
        "growth",
        "improvement",
        "journal",
        "mindset",
        "mood",
        "note",
        "personal",
        "progress",
        "reflection",
        "retrospective",
        "review",
        "thought",
    ],
    "recipes": [
        "bake",
        "chef",
        "cook",
        "cooking",
        "diet",
        "dish",
        "food",
        "gluten-free",
        "healthy",
        "ingredient",
        "meal",
        "meal prep",
        "nutritional",
        "recipe",
        "vegan",
        "vegetarian",
    ],
    "notes": [
        "idea",
        "insight",
        "item",
        "key point",
        "note",
        "observation",
        "point",
        "remind",
        "takeaway",
        "task",
        "thought",
        "todo",
    ],
    "learning": [
        "chapter",
        "concept",
        "course",
        "exercise",
        "exam",
        "guide",
        "homework",
        "knowledge",
        "learn",
        "lesson",
        "module",
        "practice",
        "skill",
        "study",
        "theory",
        "tutorial",
    ],
}


def load_category_keywords() -> dict[str, list[str]]:
    """Load category keywords from environment or defaults.

    Checks WIKI_NOTE_CATEGORIES environment variable for JSON-encoded
    custom categories. Falls back to DEFAULT_CATEGORY_KEYWORDS if not set
    or if JSON parsing fails.

    Returns:
        Dictionary mapping category names to lists of keywords
    """
    env_var = os.environ.get("WIKI_NOTE_CATEGORIES")

    if not env_var:
        return DEFAULT_CATEGORY_KEYWORDS.copy()

    try:
        custom = json.loads(env_var)
        if isinstance(custom, dict):
            return custom
        else:
            logger.warning("WIKI_NOTE_CATEGORIES must be a JSON object, using defaults")
            return DEFAULT_CATEGORY_KEYWORDS.copy()
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse WIKI_NOTE_CATEGORIES: {e}, using defaults")
        return DEFAULT_CATEGORY_KEYWORDS.copy()


def get_custom_categories() -> list[str]:
    """Get sorted list of available category names.

    Returns:
        Sorted list of category names from loaded configuration
    """
    keywords = load_category_keywords()
    return sorted(list(keywords.keys()))
