# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""Segment stage — a ``Document`` into traceable ``Segment`` units (spec §5).

STATUS: stub. Each segment must keep provenance (heading_path, source_span,
hash) so later gates can refuse orphaned high-authority context. Text is stored
by reference (Decision Record 3a); only a short, secret-free preview is inline.
"""
from __future__ import annotations

from ..contract import Document, Segment

__all__ = ["segment_document"]


def segment_document(document: Document, raw_text: str) -> list[Segment]:
    """Split a document into Segments along heading / block boundaries.

    TODO: Markdown-aware splitter that preserves heading_path and byte spans.
    Must write each segment's full text to the store and set ``text_ref``;
    ``text_preview`` is a truncated, redaction-safe excerpt.
    """
    raise NotImplementedError(
        "segment_document: implement heading-aware segmentation with provenance "
        "(heading_path, source_span, hash) and text-by-reference."
    )
