# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""Ingest stage — files in, ``Document`` records out (spec v0.4 §5).

Robust-core scope (spec §8.1.1): Markdown, text, JSON for the MVP; DOCX/PDF are
future work. Encoding is cleaned (mojibake repair) on entry so the dirty form
only survives inside the dogfooding fixture; whether a file *was* dirty is
recorded so the conflict stage can raise ``encoding_mojibake``.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from ..contract import Document
from ..store import TextStore
from ..textutils import has_mojibake

__all__ = ["compute_hash", "clean_encoding", "ingest_file", "IngestResult"]

# UTF-8 punctuation mis-decoded as cp1252. Order matters (longest first).
_MOJIBAKE_REPAIRS = (
    ("â€”", "—"),
    ("â€“", "–"),
    ("â€™", "’"),
    ("â€œ", "“"),
    ("â€\x9d", "”"),
    ("â€¦", "…"),
    ("Ã©", "é"),
)

_TYPE_BY_SUFFIX = {
    ".md": "markdown",
    ".markdown": "markdown",
    ".txt": "text",
    ".json": "json",
    ".jsonl": "jsonl",
}


@dataclass
class IngestResult:
    """A Document plus the cleaned text and a mojibake-was-present flag."""

    document: Document
    clean_text: str
    had_mojibake: bool


def compute_hash(data: bytes) -> str:
    """Content hash in the contract's ``sha256:...`` form."""
    return "sha256:" + hashlib.sha256(data).hexdigest()


def clean_encoding(text: str) -> str:
    """Repair known mojibake sequences (Decision Record carried-forward note)."""
    for bad, good in _MOJIBAKE_REPAIRS:
        text = text.replace(bad, good)
    return text


def ingest_file(
    path: str | Path,
    *,
    document_id: str,
    ingested_at: str,
    store: TextStore,
) -> IngestResult:
    """Read a file into a ``Document``, cleaning encoding and storing raw text.

    Caller supplies ``ingested_at`` (no wall-clock inside the library) and the
    ``store`` that backs ``raw_text_ref``.
    """
    p = Path(path)
    raw = p.read_text(encoding="utf-8", errors="replace")
    had_mojibake = has_mojibake(raw)
    clean = clean_encoding(raw)
    raw_text_ref = store.put(clean)
    document_type = _TYPE_BY_SUFFIX.get(p.suffix.lower(), "text")
    doc = Document(
        document_id=document_id,
        source_path=str(p),
        document_type=document_type,
        ingested_at=ingested_at,
        hash=compute_hash(clean.encode("utf-8")),
        raw_text_ref=raw_text_ref,
    )
    return IngestResult(document=doc, clean_text=clean, had_mojibake=had_mojibake)
