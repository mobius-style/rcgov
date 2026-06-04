# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""Secret detection — regex + Shannon entropy (Decision Record 4).

``shannon_entropy`` is fully implemented (it is pure and trivially testable).
``scan_secrets`` ships with a small starter pattern set and an entropy backstop;
the full pattern library is loaded from ``config/secret_patterns.yaml`` and is
expected to grow. A hit routes the segment to the Safety Gate
(``gate_result = quarantine``), which relevance can never override.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass

__all__ = ["SecretFinding", "shannon_entropy", "scan_secrets"]


@dataclass(frozen=True)
class SecretFinding:
    kind: str  # e.g. "aws_access_key", "high_entropy_token"
    start: int
    end: int
    excerpt: str  # redacted preview, never the raw secret in full


# Starter patterns. The canonical, extensible set lives in
# config/secret_patterns.yaml; these are a conservative built-in floor so the
# Safety Gate is never empty even without config.
_STARTER_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private_key_block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("github_token", re.compile(r"ghp_[0-9A-Za-z]{36}")),
    ("slack_token", re.compile(r"xox[baprs]-[0-9A-Za-z-]{10,}")),
    ("generic_assignment", re.compile(
        r"(?i)(?:api[_-]?key|secret|password|token)\s*[:=]\s*['\"]?[^\s'\"]{8,}")),
]

# Entropy backstop: a long, high-entropy run that looks like a credential.
_ENTROPY_CANDIDATE = re.compile(r"[A-Za-z0-9+/=_\-]{20,}")
_ENTROPY_THRESHOLD = 4.0  # bits/char; ~random base64 sits near 5-6


def shannon_entropy(s: str) -> float:
    """Shannon entropy of ``s`` in bits per character. 0.0 for empty string."""
    if not s:
        return 0.0
    counts: dict[str, int] = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def _redact(token: str) -> str:
    """Keep only a 4-char head so findings never leak the full secret."""
    if len(token) <= 4:
        return "****"
    return token[:4] + "…[redacted]"


def scan_secrets(text: str) -> list[SecretFinding]:
    """Return secret findings in ``text``. Pattern hits first, then an entropy
    backstop for anything pattern-matching missed."""
    findings: list[SecretFinding] = []
    spans: list[tuple[int, int]] = []

    for kind, pat in _STARTER_PATTERNS:
        for m in pat.finditer(text):
            findings.append(
                SecretFinding(kind=kind, start=m.start(), end=m.end(),
                              excerpt=_redact(m.group(0)))
            )
            spans.append((m.start(), m.end()))

    for m in _ENTROPY_CANDIDATE.finditer(text):
        if any(s <= m.start() < e for s, e in spans):
            continue  # already flagged by a named pattern
        if shannon_entropy(m.group(0)) >= _ENTROPY_THRESHOLD:
            findings.append(
                SecretFinding(kind="high_entropy_token", start=m.start(),
                              end=m.end(), excerpt=_redact(m.group(0)))
            )
    return findings
