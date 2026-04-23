"""Hybrid file chunking algorithm for .txt and .md import."""

from __future__ import annotations

import re
from typing import NamedTuple

MAX_CHUNK_SIZE = 2000
# 10 preserves short-but-valid bodies (e.g. 24-char section content).
# A value of 50 would merge semantically complete short sections into their predecessor.
MIN_CHUNK_SIZE = 10


class Chunk(NamedTuple):
    title: str
    body: str
    source_file: str
    index: int


def chunk_file(content: str, filename: str) -> list[Chunk]:
    """Dispatch to the right chunker based on file extension.

    Args:
        content: Raw file text.
        filename: Original filename (used for titles and extension detection).

    Returns:
        List of Chunk namedtuples ordered by appearance.
    """
    if not content or not content.strip():
        return []

    content = content.replace("\r\n", "\n").replace("\r", "\n")

    if filename.lower().endswith(".md"):
        return _chunk_markdown(content, filename)
    return _chunk_by_paragraphs(content, filename)


def _chunk_markdown(content: str, filename: str) -> list[Chunk]:
    """Split on ATX headings (#...######). Falls back to paragraphs if none found."""
    heading_re = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)
    matches = list(heading_re.finditer(content))

    if not matches:
        return _chunk_by_paragraphs(content, filename)

    pairs: list[tuple[str, str]] = []

    if matches[0].start() > 0:
        preamble = content[: matches[0].start()].strip()
        if preamble:
            pairs.append((f"{filename} - Preamble", preamble))

    for i, match in enumerate(matches):
        title = match.group(1).strip()
        body_start = match.end() + 1
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body = content[body_start:body_end].strip()
        pairs.append((title, body))

    return _finalize_chunks(pairs, filename)


def _group_paragraphs(paragraphs: list[str]) -> list[str]:
    """Group paragraphs into chunks up to MAX_CHUNK_SIZE.

    Args:
        paragraphs: List of paragraph strings.

    Returns:
        List of grouped paragraph strings (multiple paragraphs joined by double newlines).
    """
    groups: list[str] = []
    current: list[str] = []
    current_len = 0

    for para in paragraphs:
        if current and current_len + len(para) > MAX_CHUNK_SIZE:
            groups.append("\n\n".join(current))
            current = [para]
            current_len = len(para)
        else:
            current.append(para)
            current_len += len(para)

    if current:
        groups.append("\n\n".join(current))

    return groups


def _chunk_by_paragraphs(content: str, filename: str) -> list[Chunk]:
    """Split on double newlines (blank lines). Falls back to word-boundary split."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", content) if p.strip()]

    if not paragraphs:
        return []

    groups = _group_paragraphs(paragraphs)
    pairs = [(f"{filename} - Part {i + 1}", g) for i, g in enumerate(groups)]
    return _finalize_chunks(pairs, filename)


def _finalize_chunks(pairs: list[tuple[str, str]], filename: str) -> list[Chunk]:
    """Sub-split oversized chunks, merge tiny ones, assign sequential indices.

    Args:
        pairs: List of (title, body) tuples.
        filename: Source filename.
    """
    expanded: list[tuple[str, str]] = []
    for title, body in pairs:
        if len(body) > MAX_CHUNK_SIZE:
            sub_bodies = _sub_split(body)
            for j, sub in enumerate(sub_bodies):
                expanded.append((f"{title} - Part {j + 1}", sub))
        else:
            expanded.append((title, body))

    merged: list[tuple[str, str]] = []
    for title, body in expanded:
        # Merge if: body exists, is tiny, and there's a previous chunk
        if body and len(body) < MIN_CHUNK_SIZE and merged:
            prev_title, prev_body = merged[-1]
            merged[-1] = (prev_title, f"{prev_body}\n\n{body}")
        else:
            merged.append((title, body))

    return [
        Chunk(title=t, body=b, source_file=filename, index=i)
        for i, (t, b) in enumerate(merged)
        if b.strip()
    ]


def _sub_split(body: str) -> list[str]:
    """Split an oversized body at paragraph or word boundaries."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]

    if len(paragraphs) > 1:
        return _group_paragraphs(paragraphs)

    result: list[str] = []
    remaining = body
    while len(remaining) > MAX_CHUNK_SIZE:
        split_at = remaining.rfind(" ", 0, MAX_CHUNK_SIZE)
        if split_at == -1:
            split_at = MAX_CHUNK_SIZE
        result.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    if remaining:
        result.append(remaining)
    return result
