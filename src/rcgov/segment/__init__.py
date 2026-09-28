# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""Segment stage — a ``Document`` into traceable ``Segment`` units (spec §5).

Markdown heading-aware splitter. Each heading opens a new segment whose
``heading_path`` is the active heading stack; the segment text runs from its
heading line to the next heading of equal-or-higher level. Provenance is
preserved as ``heading_path`` + ``source_span`` (char offsets) + content hash;
full text is stored by reference, with a short, secret-free preview inline.
"""
from __future__ import annotations

import re

from ..contract import Document, Segment, SourceSpan
from ..store import TextStore
from ..scan import scan_secrets

__all__ = ["segment_document"]

_HEADING_OPEN = re.compile(r"^(#{1,6})\s+")


def _heading(line: str) -> tuple[int, str] | None:
    """(level, title) of an ATX heading line, else None. For a single line (no
    interior newline, which is all the segmenter passes) the same result as the
    pattern ``^(#{1,6})\\s+(.*?)\\s*#*\\s*$`` used until 0.2.0, which took cubic
    time on ``# x<many spaces>y`` (two minutes for a 4 KB line)."""
    m = _HEADING_OPEN.match(line)
    if m is None:
        return None
    return len(m.group(1)), line[m.end():].rstrip().rstrip("#").rstrip()
_PREVIEW_LEN = 160


def _redact_preview(text: str) -> str:
    """First non-heading prose, collapsed, with any secret excerpt masked."""
    body_lines = [ln for ln in text.splitlines() if _heading(ln) is None]
    body = " ".join(ln.strip() for ln in body_lines if ln.strip())
    preview = re.sub(r"\s+", " ", body)[:_PREVIEW_LEN]
    for f in scan_secrets(preview):
        preview = preview[: f.start] + "[redacted]" + preview[f.end :]
    return preview


def segment_document(document: Document, raw_text: str, store: TextStore) -> list[Segment]:
    """Split ``raw_text`` into heading-delimited Segments with provenance."""
    lines = raw_text.splitlines(keepends=True)

    # Locate headings: (char_offset, level, title, line_index).
    heads: list[tuple[int, int, str, int]] = []
    offset = 0
    for idx, line in enumerate(lines):
        h = _heading(line.rstrip("\n"))
        if h:
            heads.append((offset, h[0], h[1].strip(), idx))
        offset += len(line)

    # Preamble (text before the first heading) becomes its own segment.
    boundaries: list[tuple[int, list[str]]] = []
    if not heads or heads[0][0] > 0:
        boundaries.append((0, []))

    stack: list[tuple[int, str]] = []  # (level, title)
    for start, level, title, _ in heads:
        while stack and stack[-1][0] >= level:
            stack.pop()
        stack.append((level, title))
        boundaries.append((start, [t for _, t in stack]))

    segments: list[Segment] = []
    total = len(raw_text)
    for i, (start, heading_path) in enumerate(boundaries):
        end = boundaries[i + 1][0] if i + 1 < len(boundaries) else total
        text = raw_text[start:end]
        if not text.strip():
            continue
        text_ref = store.put(text)
        seg = Segment(
            segment_id=f"{document.document_id}_seg_{i:04d}",
            document_id=document.document_id,
            text_ref=text_ref,
            hash=TextStore.hash_of(text),
            heading_path=heading_path,
            text_preview=_redact_preview(text),
            token_estimate=max(1, len(text) // 4),
            source_span=SourceSpan(start, end),
        )
        segments.append(seg)
    return segments
