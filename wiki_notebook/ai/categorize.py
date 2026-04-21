"""Categorization logic using Ollama or keyword fallback."""

from __future__ import annotations

from typing import Any

from ..config_categories import load_category_keywords
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


# Category keywords mapping loaded from config
# Uses config_categories module to support custom categories via env vars
def _get_category_keywords() -> dict[str, list[str]]:
    """Get category keywords from configuration."""
    return load_category_keywords()


def get_category_keywords() -> dict[str, list[str]]:
    """Public accessor for category keywords.

    Returns:
        Dictionary mapping category names to lists of keywords
    """
    return _get_category_keywords()


def _load_prompt(name: str) -> str:
    """Load a prompt template from the prompts directory."""
    import os
    from pathlib import Path

    prompts_dir = Path(__file__).parent / "prompts"
    prompt_path = prompts_dir / name

    with open(prompt_path, "r") as f:
        return f.read()


def _sanitize(text: str) -> str:
    """Sanitize prompt input to prevent injection attacks.

    Escapes backslashes first, then quotes to prevent breaking out of strings.

    Args:
        text: Raw text to sanitize

    Returns:
        Sanitized text safe for string substitution
    """
    # Escape backslashes first (before other escaping)
    text = text.replace("\\", "\\\\")
    # Escape quotes to prevent breaking out of string context
    text = text.replace('"', '\\"')
    return text


def _format_prompt(template: str, title: str, body: str) -> str:
    """Format a prompt template using %s placeholders.

    This avoids issues with { } being used in JSON in the template.
    Inputs are sanitized to prevent injection attacks.
    """
    import re

    # Sanitize inputs before substitution
    safe_title = _sanitize(title[:200])
    safe_body = _sanitize(body[:4000])

    # Replace {title} and {body} with %s for safe formatting
    template = template.replace("{title}", "%s")
    template = template.replace("{body}", "%s")
    return template % (safe_title, safe_body)


def _categorize_by_keywords(
    title: str, body: str
) -> tuple[str, int, list[dict[str, Any]]]:
    """Categorize by keywords and return category, confidence, and suggestions.

    Args:
        title: Note title
        body: Note body content

    Returns:
        Tuple of (category, confidence, suggestions) where suggestions is a list
        of dicts with 'category' and 'confidence' keys
    """
    import re

    # Combine title and body, lowercase, strip markdown
    text = f"{title} {body}".lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    words = text.split()

    # Remove stopwords
    content_words = [w for w in words if w not in STOPWORDS and len(w) > 2]

    if not content_words:
        return "uncategorized", 0, []

    # Count word frequencies
    word_counts: dict[str, int] = {}
    for word in content_words:
        word_counts[word] = word_counts.get(word, 0) + 1

    # Score all categories
    category_keywords = get_category_keywords()
    scores: dict[str, int] = {}

    for category, keywords in category_keywords.items():
        score = sum(
            word_counts.get(keyword, 0)
            for keyword in keywords
            if keyword in word_counts
        )
        scores[category] = score

    # Find best category
    best_category = max(scores, key=scores.get) if scores else "uncategorized"
    best_score = scores.get(best_category, 0)

    # Calculate confidence: scale score to 0-100
    confidence = min(100, int(best_score * 15)) if best_score > 0 else 0

    # Get top 3 alternatives (excluding best category)
    sorted_by_score = sorted(
        [(cat, score) for cat, score in scores.items() if cat != best_category],
        key=lambda x: x[1],
        reverse=True,
    )
    suggestions = [
        {"category": cat, "confidence": min(100, int(score * 15))}
        for cat, score in sorted_by_score[:3]
        if score > 0
    ]

    return best_category, confidence, suggestions


def _get_category_suggestions(
    title: str, body: str, exclude_category: str
) -> list[dict[str, Any]]:
    """Get alternative category suggestions for a note.

    Args:
        title: Note title
        body: Note body content
        exclude_category: Category to exclude from suggestions (the main category)

    Returns:
        List of dicts with 'category' and 'confidence' keys
    """
    _, _, suggestions = _categorize_by_keywords(title, body)
    # Filter out the exclude_category if it somehow appears
    return [s for s in suggestions if s["category"] != exclude_category]


def _keyword_fallback(title: str, body: str) -> dict[str, Any]:
    """Fallback categorization using keyword heuristic.

    Args:
        title: Note title
        body: Note body content

    Returns:
        Dict with category, tags, confidence, and suggestions keys
    """
    import re

    # Get category and confidence from keyword categorization
    category, confidence, suggestions = _categorize_by_keywords(title, body)

    # Get top 3-5 words as tags
    text = f"{title} {body}".lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    words = text.split()
    content_words = [w for w in words if w not in STOPWORDS and len(w) > 2]

    word_counts: dict[str, int] = {}
    for word in content_words:
        word_counts[word] = word_counts.get(word, 0) + 1

    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    tags = [word for word, count in sorted_words[:5] if word not in STOPWORDS]

    # Ensure category is not in tags
    if category in tags:
        tags = [t for t in tags if t != category]

    return {
        "category": category,
        "tags": tags,
        "confidence": confidence,
        "suggestions": suggestions,
    }


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
        Dict with category, tags, confidence (0-100), and suggestions keys
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

        # AI categorization has high confidence (85)
        confidence = 85

        # Get suggestions from keyword analysis
        suggestions = _get_category_suggestions(title, body, category)

        return {
            "category": category,
            "tags": tags,
            "confidence": confidence,
            "suggestions": suggestions,
        }

    except (OllamaError, ValueError, KeyError) as e:
        # Fall back to keyword heuristic on error
        return _keyword_fallback(title, body)
