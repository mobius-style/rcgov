# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""Small lexical helpers shared by the priority and conflict stages.

Deliberately model-independent (Decision Record 4): tokenization + term-frequency
cosine. The ME5 embedding path is an experimental *upgrade* layered on top of
these, not a dependency of the robust core.
"""
from __future__ import annotations

import math
import re
from collections import Counter

__all__ = ["tokenize", "cosine", "jaccard", "MOJIBAKE_MARKERS", "has_mojibake"]

# Mojibake markers: UTF-8 punctuation mis-decoded as cp1252. Used by both ingest
# (repair) and conflict detection (flagging).
MOJIBAKE_MARKERS = ("â€”", "â€™", "â€œ", "â€\x9d", "Ã©", " Â")

_STOPWORDS = frozenset(
    """a an the of to in on for and or is are be as at by with from this that these those
    it its into not no than then so such may can should must will shall would could
    we you they i he she them their our your his her not""".split()
)
_WORD = re.compile(r"[a-z0-9_]+")


def tokenize(text: str) -> list[str]:
    """Lowercase alphanumeric tokens with stopwords removed."""
    return [t for t in _WORD.findall(text.lower()) if t not in _STOPWORDS and len(t) > 1]


def cosine(a: str, b: str) -> float:
    """Term-frequency cosine similarity of two strings in [0, 1]."""
    ca, cb = Counter(tokenize(a)), Counter(tokenize(b))
    if not ca or not cb:
        return 0.0
    common = set(ca) & set(cb)
    dot = sum(ca[t] * cb[t] for t in common)
    na = math.sqrt(sum(v * v for v in ca.values()))
    nb = math.sqrt(sum(v * v for v in cb.values()))
    return dot / (na * nb) if na and nb else 0.0


def jaccard(a: str, b: str) -> float:
    """Jaccard overlap of token sets in [0, 1]."""
    sa, sb = set(tokenize(a)), set(tokenize(b))
    if not sa and not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb) if (sa | sb) else 0.0


def has_mojibake(text: str) -> bool:
    """Whether ``text`` carries any known mojibake marker."""
    return any(m in text for m in MOJIBAKE_MARKERS)
