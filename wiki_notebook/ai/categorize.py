"""Categorization logic using Ollama or keyword fallback."""

from __future__ import annotations

from typing import Any

from .ollama_client import OllamaClient, OllamaError

# Common English stopwords for keyword fallback
STOPWORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "with",
    "by",
    "from",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "must",
    "shall",
    "can",
    "need",
    "dare",
    "ought",
    "used",
    "it",
    "its",
    "this",
    "that",
    "these",
    "those",
    "i",
    "me",
    "my",
    "myself",
    "we",
    "our",
    "ours",
    "ourselves",
    "you",
    "your",
    "yours",
    "yourself",
    "yourselves",
    "he",
    "him",
    "his",
    "himself",
    "she",
    "her",
    "hers",
    "herself",
    "they",
    "them",
    "their",
    "theirs",
    "themselves",
    "what",
    "which",
    "who",
    "whom",
    "when",
    "where",
    "why",
    "how",
    "all",
    "each",
    "few",
    "more",
    "most",
    "other",
    "some",
    "such",
    "no",
    "nor",
    "not",
    "only",
    "own",
    "same",
    "so",
    "than",
    "too",
    "very",
    "s",
    "t",
    "just",
    "now",
    "here",
    "there",
    "then",
    "once",
    "if",
    "because",
    "as",
    "until",
    "while",
    "about",
    "against",
    "between",
    "into",
    "through",
    "during",
    "before",
    "after",
    "above",
    "below",
    "up",
    "down",
    "out",
    "off",
    "over",
    "under",
    "again",
    "further",
    "then",
    "once",
    "here",
    "there",
    "when",
    "where",
    "why",
    "how",
    "each",
    "both",
    "any",
    "about",
    "against",
    "between",
    "into",
    "through",
    "during",
    "before",
    "after",
    "above",
    "below",
    "up",
    "down",
    "out",
    "off",
    "over",
    "under",
    "again",
    "further",
    "then",
    "once",
    "here",
    "there",
    "when",
    "where",
    "why",
    "how",
    "all",
    "each",
    "few",
    "more",
    "most",
    "other",
    "some",
    "such",
    "no",
    "nor",
    "not",
    "only",
    "own",
    "same",
    "so",
    "than",
    "too",
    "very",
}

# Category keywords mapping for fallback heuristic
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "meetings": [
        "meeting",
        "meeting",
        "agenda",
        "attendees",
        "discussion",
        "talk",
        "call",
        "zoom",
        "teams",
        "conference",
        "presentation",
        " seminar",
        "workshop",
        "panel",
        "roundtable",
        "briefing",
        "sync",
        "standup",
    ],
    "project ideas": [
        "project",
        "idea",
        "feature",
        "concept",
        "plan",
        "proposal",
        "vision",
        "prototype",
        "sprint",
        " MVP",
        " MVP",
        "scope",
        "requirements",
        "spec",
        "specification",
        "design",
        "wireframe",
        "mockup",
    ],
    "journal": [
        "journal",
        "entry",
        "thought",
        "feeling",
        "reflection",
        "daily",
        "note",
        "mood",
        "emotional",
        "personal",
        "mindset",
        "growth",
        "gratitude",
        "improvement",
        "progress",
        "review",
        "retrospective",
    ],
    "recipes": [
        "recipe",
        "cook",
        "bake",
        "meal",
        "food",
        "dish",
        "ingredient",
        "recipe",
        "meal prep",
        "diet",
        "nutritional",
        "healthy",
        "vegetarian",
        "vegan",
        "gluten-free",
        "recipe",
        "cooking",
        "recipe",
        "chef",
    ],
    "notes": [
        "note",
        "remind",
        "todo",
        "task",
        "item",
        "point",
        "idea",
        "thought",
        "observation",
        "insight",
        "takeaway",
        "key point",
    ],
    "learning": [
        "learn",
        "study",
        "learn",
        "course",
        "tutorial",
        "guide",
        "guide",
        "lesson",
        "lesson",
        "module",
        "chapter",
        "concept",
        "theory",
        "knowledge",
        "skill",
        "practice",
        "exercise",
        "homework",
        "exam",
    ],
}


def _load_prompt(name: str) -> str:
    """Load a prompt template from the prompts directory."""
    import os
    from pathlib import Path

    prompts_dir = Path(__file__).parent / "prompts"
    prompt_path = prompts_dir / name

    with open(prompt_path, "r") as f:
        return f.read()


def _format_prompt(template: str, title: str, body: str) -> str:
    """Format a prompt template using %s placeholders.

    This avoids issues with { } being used in JSON in the template.
    """
    import re

    # Replace {title} and {body} with %s for safe formatting
    template = template.replace("{title}", "%s")
    template = template.replace("{body}", "%s")
    return template % (title[:200], body[:4000])


def _keyword_fallback(title: str, body: str) -> dict[str, Any]:
    """Fallback categorization using keyword heuristic.

    Args:
        title: Note title
        body: Note body content

    Returns:
        Dict with category and tags keys
    """
    import re

    # Combine title and body, lowercase, strip markdown
    text = f"{title} {body}".lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    words = text.split()

    # Remove stopwords
    content_words = [w for w in words if w not in STOPWORDS and len(w) > 2]

    if not content_words:
        return {"category": "uncategorized", "tags": []}

    # Count word frequencies
    word_counts: dict[str, int] = {}
    for word in content_words:
        word_counts[word] = word_counts.get(word, 0) + 1

    # Find best category based on keyword matching
    best_category = "uncategorized"
    best_score = 0

    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(
            word_counts.get(keyword, 0)
            for keyword in keywords
            if keyword in word_counts
        )
        if score > best_score:
            best_score = score
            best_category = category

    # If we have a positive score, use the category; otherwise default
    if best_score > 0:
        category = best_category
    else:
        category = "uncategorized"

    # Get top 3-5 words as tags
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    tags = [word for word, count in sorted_words[:5] if word not in STOPWORDS]

    # Ensure category is not in tags
    if category in tags:
        tags = [t for t in tags if t != category]

    return {"category": category, "tags": tags}


def categorize(
    title: str,
    body: str,
    client: OllamaClient | None = None,
) -> dict[str, Any]:
    """Categorize a note using Ollama or keyword fallback.

    Args:
        title: Note title
        body: Note body content
        client: OllamaClient instance (creates new if None)

    Returns:
        Dict with category and tags keys
    """
    if client is None:
        client = OllamaClient()

    # Check if Ollama is available
    if not client.is_available():
        return _keyword_fallback(title, body)

    try:
        prompt = _format_prompt(
            _load_prompt("categorize.txt"),
            title=title[:200],
            body=body[:4000],
        )
        result = client.generate_json(prompt)

        # Validate result structure
        if not isinstance(result.get("category"), str):
            raise ValueError("Invalid category")
        if not isinstance(result.get("tags"), list):
            raise ValueError("Invalid tags")

        # Clean category
        category = result["category"].strip().lower()
        if not category:
            category = "uncategorized"

        # Clean tags
        tags = [t.strip().lower() for t in result["tags"] if isinstance(t, str)]
        tags = [t for t in tags if t]  # Remove empty strings
        tags = list(dict.fromkeys(tags))[:20]  # Dedupe, limit to 20

        # Ensure category is not in tags
        if category in tags:
            tags = [t for t in tags if t != category]

        return {"category": category, "tags": tags}

    except (OllamaError, ValueError, KeyError) as e:
        # Fall back to keyword heuristic on error
        return _keyword_fallback(title, body)
