"""Hybrid file chunking algorithm for .txt, .md, and .html import."""

from __future__ import annotations

import re
from dataclasses import dataclass

MAX_CHUNK_SIZE = 2000
# 10 preserves short-but-valid bodies (e.g. 24-char section content).
# A value of 50 would merge semantically complete short sections into their predecessor.
MIN_CHUNK_SIZE = 10


@dataclass
class Chunk:
    title: str
    body: str
    source_file: str
    index: int
    content_type: str = "markdown"


def chunk_file(content: str, filename: str) -> list[Chunk]:
    """Dispatch to the right chunker based on file extension.

    Args:
        content: Raw file text.
        filename: Original filename (used for titles and extension detection).

    Returns:
        List of Chunk dataclasses ordered by appearance.
    """
    if not content or not content.strip():
        return []

    content = content.replace("\r\n", "\n").replace("\r", "\n")

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext in ("md",):
        return _chunk_markdown(content, filename)
    if ext in ("html", "htm"):
        return _chunk_html(content, filename)
    return _chunk_by_paragraphs(content, filename)


def _chunk_markdown(content: str, filename: str) -> list[Chunk]:
    """Split markdown on #–###### heading boundaries.

    Content before the first heading becomes a preamble chunk with the
    filename as its title.  Each heading becomes the chunk title; the
    body between it and the next heading becomes the chunk body.
    """
    heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
    matches = list(heading_pattern.finditer(content))

    if not matches:
        return _chunk_by_paragraphs(content, filename)

    chunks: list[tuple[str, str]] = []

    # Preamble before first heading
    first_pos = matches[0].start()
    preamble = content[:first_pos].strip()
    if preamble and len(preamble) >= MIN_CHUNK_SIZE:
        chunks.append((filename, preamble))

    for i, m in enumerate(matches):
        title = m.group(2).strip()
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body = content[body_start:body_end].strip()

        if body:
            chunks.append((title, body))
        elif i == 0 and not chunks:
            # First heading with no body — still create a placeholder
            chunks.append((title, ""))

    return _finalize_chunks(chunks, filename)


def _chunk_html(content: str, filename: str) -> list[Chunk]:
    """Extract a single chunk from an HTML file, preserving all formatting.

    HTML is a tree structure — splitting on arbitrary boundaries would
    produce orphaned closing tags.  Each HTML file maps to a single chunk.
    """
    from .html_utils import extract_title_from_html

    body = content.strip()
    if not body:
        return []

    title = extract_title_from_html(body, fallback=filename)

    return [
        Chunk(
            title=title,
            body=body,
            source_file=filename,
            index=0,
            content_type="html",
        )
    ]


def _chunk_by_paragraphs(content: str, filename: str) -> list[Chunk]:
    """Split on blank-line-delimited paragraphs."""
    paragraphs = re.split(r"\n\s*\n", content)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    if not paragraphs:
        return []

    chunks: list[tuple[str, str]] = []

    for i, para in enumerate(paragraphs):
        # Use filename + part number as title for plain text
        title = f"{filename} - Part {i + 1}" if len(paragraphs) > 1 else filename
        chunks.append((title, para))

    return _finalize_chunks(chunks, filename)


def _finalize_chunks(chunks: list[tuple[str, str]], filename: str) -> list[Chunk]:
    """Apply size constraints: merge tiny chunks, sub-split oversized ones."""
    if not chunks:
        return []

    # Merge tiny chunks into predecessor
    merged: list[tuple[str, str]] = []
    for title, body in chunks:
        if (
            len(body) < MIN_CHUNK_SIZE
            and merged
            and len(merged[-1][1]) + len(body) <= MAX_CHUNK_SIZE
        ):
            merged[-1] = (merged[-1][0], f"{merged[-1][1]}\n\n{body}")
        elif body.strip():
            merged.append((title, body))

    # Sub-split oversized chunks
    result_chunks: list[tuple[str, str]] = []
    for title, body in merged:
        if len(body) > MAX_CHUNK_SIZE:
            sub_chunks = _sub_split(title, body)
            result_chunks.extend(sub_chunks)
        else:
            result_chunks.append((title, body))

    # Filter empties and assign indices
    return [
        Chunk(title=t, body=b, source_file=filename, index=i)
        for i, (t, b) in enumerate(result_chunks)
        if b.strip()
    ]


def _sub_split(title: str, body: str) -> list[tuple[str, str]]:
    """Split an oversized chunk at paragraph or word boundaries."""
    paragraphs = re.split(r"\n\s*\n", body)
    chunks: list[tuple[str, str]] = []

    current: list[str] = []
    current_len = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if current_len + len(para) > MAX_CHUNK_SIZE and current:
            chunks.append((f"{title} (Part {len(chunks) + 1})", "\n\n".join(current)))
            current = [para]
            current_len = len(para)
        else:
            current.append(para)
            current_len += len(para)

    if current:
        chunks.append((f"{title} (Part {len(chunks) + 1})", "\n\n".join(current)))

    # Word-boundary fallback if any chunk still oversized
    final: list[tuple[str, str]] = []
    for t, b in chunks:
        if len(b) > MAX_CHUNK_SIZE:
            words = b.split()
            part: list[str] = []
            part_len = 0
            part_num = 1
            for w in words:
                if part_len + len(w) > MAX_CHUNK_SIZE and part:
                    final.append((f"{t} p{part_num}", " ".join(part)))
                    part = [w]
                    part_len = len(w)
                    part_num += 1
                else:
                    part.append(w)
                    part_len += len(w) + 1
            if part:
                final.append((f"{t} p{part_num}", " ".join(part)))
        else:
            final.append((t, b))

    return final
