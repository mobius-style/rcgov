# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""Ingest stage — files in, ``Document`` records out (spec v0.4 §5).

STATUS: stub. Robust-core scope (spec §8.1.1): Markdown, text, JSON, DOCX, PDF
where possible. The MVP cleans encoding on entry (mojibake repair) so the dirty
form only survives inside the dogfooding fixture.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from ..contract import Document

__all__ = ["compute_hash", "clean_encoding", "ingest_file"]

# Minimal mojibake repair table. The source drafts carried a literal "â" where
# an em dash belonged (UTF-8 em dash mis-decoded as cp1252). Expand as needed;
# a fuller pass (ftfy-style) is future work.
_MOJIBAKE_REPAIRS = {
    "â€”": "—",  # â€” -> em dash
    "â€™": "’",  # â€™ -> right single quote
    "â ": "— ",            # bare "â " seen in drafts -> "— "
}


def compute_hash(data: bytes) -> str:
    """Content hash in the contract's ``sha256:...`` form."""
    return "sha256:" + hashlib.sha256(data).hexdigest()


def clean_encoding(text: str) -> str:
    """Repair known mojibake sequences (Decision Record carried-forward note)."""
    for bad, good in _MOJIBAKE_REPAIRS.items():
        text = text.replace(bad, good)
    return text


def ingest_file(path: str | Path, *, document_id: str, ingested_at: str) -> Document:
    """Read a file into a ``Document``. Caller supplies timestamps (no wall-clock
    inside the library so runs stay reproducible)."""
    raise NotImplementedError(
        "ingest_file: store raw text behind raw_text_ref, set document_type from "
        "suffix, and return a Document. See spec v0.4 §4.1 / §8.1."
    )
