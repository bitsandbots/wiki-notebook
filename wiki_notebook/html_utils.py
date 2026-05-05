"""HTML utility functions for import and search."""

from __future__ import annotations

import re

_TAG_RE = re.compile(r"<[^>]*>")
_ENTITY_RE = re.compile(r"&[a-z]+;|&#\d+;")
_WS_RE = re.compile(r"\s+")

# Common HTML entities to decode
_ENTITIES = {
    "&amp;": "&",
    "&lt;": "<",
    "&gt;": ">",
    "&quot;": '"',
    "&#39;": "'",
    "&apos;": "'",
    "&nbsp;": " ",
}


def strip_html(text: str) -> str:
    """Remove HTML tags, decode common entities, collapse whitespace.

    Args:
        text: Raw HTML string.

    Returns:
        Plain text with tags removed and entities decoded.
    """
    stripped = _TAG_RE.sub(" ", text)
    for entity, char in _ENTITIES.items():
        stripped = stripped.replace(entity, char)
    stripped = _ENTITY_RE.sub(" ", stripped)
    stripped = _WS_RE.sub(" ", stripped).strip()
    return stripped


def extract_title_from_html(html: str, fallback: str = "Imported HTML") -> str:
    """Extract a title from <title> tag or first <h1>.

    Args:
        html: Raw HTML content.
        fallback: Title to use if no <title> or <h1> found.

    Returns:
        Extracted title as plain text.
    """
    title_match = re.search(
        r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL
    )
    if title_match:
        return strip_html(title_match.group(1))

    h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL)
    if h1_match:
        return strip_html(h1_match.group(1))

    return fallback
