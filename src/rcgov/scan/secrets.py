# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""Secret detection — regex + Shannon entropy (Decision Record 4).

``shannon_entropy`` is fully implemented (it is pure and trivially testable).
``scan_secrets`` runs the named patterns below and an entropy backstop. A
named hit routes the segment to the Safety Gate
(``gate_result = quarantine``), which relevance can never override.
"""
from __future__ import annotations

import bisect
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


# Named patterns. These are the whole library: ``config/secret_patterns.yaml``
# documents intent and is not loaded.
#
# 0.2.1 — why this changed. AWS secret access keys and ``sk-`` API keys used to
# reach only the entropy backstop (``high_entropy_token``), which
# ``rebuild_bytes`` keeps by default, so a labelled secret survived verbatim.
# They now have named kinds, which are always excised.
#
# Two rules keep the named kinds from eating ordinary text:
#   * of the five patterns that existed before 0.2.1, four are unchanged byte
#     for byte; ``private_key_block`` was widened to any ``BEGIN … PRIVATE
#     KEY`` header (DSA, ENCRYPTED, PGP ``… BLOCK``);
#   * every pattern added in 0.2.1 must also pass a randomness gate — a
#     documentation placeholder (``hf_xxxxxxxx…``), an identifier
#     (``settings_secret_key_v2``) or a code expression
#     (``"token": self.api_key``) is not a secret.
#
# Scan time must stay linear in the input. Two rules, both learned from
# review: a value class must not contain the separator that precedes it
# (``token=token=…``), and a pattern that can fail after a long scan must not
# be able to start inside its own value class (``eyJ-eyJ-…``).
#
# Known limits: a bare 40-character string with no label is indistinguishable
# from a hash and stays in the backstop; vendors' published example keys
# (AWS's ``wJalr…EXAMPLEKEY``, Stripe's ``sk_test_4eC39…``) have the shape of
# real ones and are excised; bearer tokens with no recognisable prefix and
# passwords written as prose are not detected.
_PRE = r"(?:(?<![A-Za-z0-9])|(?<=%[0-9A-Fa-f]{2}))"   # not \b: \b fails after CJK text

# (kind, pattern, group holding the value or 0, gate: None or a key of _GATES)
_PATTERNS: list[tuple[str, re.Pattern[str], int, str | None]] = [
    # --- present in 0.2.0 (private_key_block widened in 0.2.1, rest unchanged) -
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}"), 0, None),
    ("private_key_block",
     re.compile(r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY(?: BLOCK)?-----"), 0, None),
    ("github_token", re.compile(r"ghp_[0-9A-Za-z]{36}"), 0, None),
    ("slack_token", re.compile(r"xox[baprs]-[0-9A-Za-z-]{10,}"), 0, None),
    ("generic_assignment", re.compile(
        r"(?i)(?:api[_-]?key|secret|password|token)\s*[:=]\s*['\"]?[^\s'\"]{8,}"), 0, None),
    # --- added in 0.2.1, all gated (see _GATES) --------------------------------
    # Label and value may be separated by anything short on the same line:
    # "Secret access key: X", "`aws_secret_access_key`: X", "<SecretAccessKey>X",
    # ":secret_access_key => 'X'", "aws.secret.key=X", full-width colon, a table bar.
    ("aws_secret_key", re.compile(
        r"(?i)(?:secret[\s_.\-]?(?:access[\s_.\-]?)?key|シークレット(?:アクセス)?キー)"
        r"[^\n]{0,24}?(?<![A-Za-z0-9/+])([A-Za-z0-9/+]{40})(?![A-Za-z0-9/+=])"), 1, "aws"),
    ("api_key_sk", re.compile(
        _PRE + r"((?:sk-(?:proj-|ant-|or-)?|gsk_)[A-Za-z0-9_\-]{20,512})"), 1, "sk"),
    ("github_token", re.compile(
        _PRE + r"((?:gh[ousr]_[0-9A-Za-z]{36}|github_pat_[0-9A-Za-z_]{40,512}))"), 1, "prefix"),
    ("huggingface_token", re.compile(_PRE + r"(hf_[A-Za-z0-9]{30,512})"), 1, "prefix"),
    ("google_api_key", re.compile(_PRE + r"(AIza[0-9A-Za-z_\-]{35})"), 1, "prefix"),
    ("gitlab_token", re.compile(_PRE + r"(glpat-[0-9A-Za-z_\-]{20,512})"), 1, "prefix"),
    ("stripe_key", re.compile(_PRE + r"([sr]k_(?:live|test)_[0-9A-Za-z]{20,512})"), 1, "prefix"),
    ("jwt", re.compile(
        r"(?:(?<![A-Za-z0-9_\-])|(?<=%[0-9A-Fa-f]{2}))(eyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,})"), 1, "prefix"),
    ("slack_webhook", re.compile(
        r"(hooks\.slack\.com/services/T[A-Za-z0-9]+/B[A-Za-z0-9]+/[A-Za-z0-9]{20,})"), 1, "last_segment"),
    ("bearer_token", re.compile(
        r"(?i)\bBearer\s+([A-Za-z0-9._~+/\-]{20,}={0,2})"), 1, "prefix"),
    ("azure_account_key", re.compile(
        r"(?i)AccountKey=([A-Za-z0-9+/]{40,}={0,2})"), 1, "prefix"),
    ("url_credentials", re.compile(
        r"[a-z][a-z0-9+.\-]{1,15}://[^\s:/@]{0,64}:([^\s:/@]{8,256})@"), 1, "url"),
    # Key names the 0.2.0 pattern could not reach (secret_key, access_key,
    # private_key, quoted JSON keys, "=>", full-width colon). The value must be
    # one unbroken token of key characters, so ``kwargs.get(...)`` or
    # ``self.api_key`` never qualifies. "=" is not in the value class (padding
    # is matched separately): with it, a run of ``token=token=…`` was scanned
    # from every label to the end — quadratic, 79 s on 200 KB.
    ("secret_assignment", re.compile(
        r"(?i)(?:api[_-]?key|secret(?:[_-]?(?:access[_-]?)?key)?|access[_-]?key"
        r"|private[_-]?key|client[_-]?secret|passwd|password|token)"
        r"['\"`]?\s*(?:[:=：]|=>)\s*['\"`]?"
        r"([A-Za-z0-9/+_\-~]{16,512}={0,2})(?![A-Za-z0-9/+_\-=~(\[]|\.[A-Za-z_(])"), 1, "strict"),
]

_RANDOM_MIN_ENTROPY = 3.0
_PIECES = re.compile(r"[A-Za-z0-9]+")
_VENDOR_PREFIX = re.compile(
    r"^(?:sk-(?:proj-|ant-(?:api\d\d-)?|or-(?:v\d-)?)?|gsk_|gh[opusr]_|github_pat_|hf_"
    r"|AIza|glpat-|[sr]k_(?:live|test)_)")


def _wordy(piece: str) -> bool:
    """A piece that reads like part of an identifier: a number, a word in one
    case, a Capitalised or camelCase word, or any of those with a trailing
    number (``v2``, ``Provider1``, ``Loader2048``)."""
    if len(piece) <= 2 or piece.isdigit():
        return True
    letters = piece.rstrip("0123456789")
    if not letters.isalpha():
        return False            # a digit between letters
    upper = sum(c.isupper() for c in letters) / len(letters)
    if upper in (0.0, 1.0):
        return len(letters) <= 24      # no single-case word is longer
    if not 0.25 <= upper <= 0.75:
        return True
    # Acronym-heavy camelCase (``RSAPrivateKeyLoader``) has the upper-case
    # share of a random string but changes case far less often.
    changes = sum(a.isupper() != b.isupper() for a, b in zip(letters, letters[1:]))
    return changes < 0.3 * (len(letters) - 1)


def _random_share(value: str) -> tuple[int, int]:
    """(characters in pieces that do not read like words, all alphanumerics)."""
    pieces = _PIECES.findall(value)
    return (sum(len(p) for p in pieces if not _wordy(p)), sum(len(p) for p in pieces))


def _gate_token(v: str) -> bool:
    """Credential-shaped: at least 8 characters, and at least half of the
    value, sit in pieces that do not read like words. Rejects placeholders
    (``xxxxxxxx``), identifiers (``settings_production_secret_key_v2``,
    ``AccessKeyCredentialProvider1``) and kebab-case names."""
    body = _VENDOR_PREFIX.sub("", v, count=1)
    rnd, total = _random_share(body)
    return (rnd >= 8 and 2 * rnd >= total
            and shannon_entropy(body) >= _RANDOM_MIN_ENTROPY)


def _gate_aws(v: str) -> bool:
    # Mixed case is required: 40 hex characters are a git SHA.
    return (any(c.islower() for c in v) and any(c.isupper() for c in v)
            and _gate_token(v))


def _gate_url(v: str) -> bool:
    # A password in a URL: two or more character classes, and not a template
    # (${VAR}, {var}, <password>, [password], %s, %(name)s).
    if v[0] in "${<[" or v.startswith(("%s", "%(")) or "${" in v:
        return False
    classes = (any(c.islower() for c in v) + any(c.isupper() for c in v)
               + any(c.isdigit() for c in v) + any(not c.isalnum() for c in v))
    floor = min(2.5, math.log2(len(v)) - 0.5)   # 16 hex characters sit near 2.8
    return classes >= 2 and shannon_entropy(v) >= floor


def _gate_last_segment(v: str) -> bool:
    return _gate_token(v.rsplit("/", 1)[-1])


_GATES = {"last_segment": _gate_last_segment, "strict": _gate_token, "prefix": _gate_token, "sk": _gate_token,
          "aws": _gate_aws, "url": _gate_url}


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
    """Return secret findings in ``text``. Named patterns first, then an entropy
    backstop for anything they missed."""
    findings: list[SecretFinding] = []
    spans: list[tuple[int, int]] = []
    seen: set[tuple[str, int, int]] = set()

    for kind, pat, group, gate in _PATTERNS:
        for m in pat.finditer(text):
            value = m.group(group)
            if gate is not None and not _GATES[gate](value):
                continue
            start, end = m.span(group)
            if (kind, start, end) in seen:
                continue
            seen.add((kind, start, end))
            findings.append(
                SecretFinding(kind=kind, start=start, end=end, excerpt=_redact(value))
            )
            spans.append((start, end))

    # Named spans, reduced to those no other span contains and sorted, so the
    # containment test below is one bisect instead of a walk over every span.
    spans.sort(key=lambda se: (se[0], -se[1]))
    outer: list[tuple[int, int]] = []
    for s, e in spans:
        if not outer or e > outer[-1][1]:
            outer.append((s, e))
    starts = [s for s, _ in outer]

    for m in _ENTROPY_CANDIDATE.finditer(text):
        i = bisect.bisect_right(starts, m.start()) - 1
        if i >= 0 and m.end() <= outer[i][1]:
            continue  # wholly inside a named finding
        if shannon_entropy(m.group(0)) >= _ENTROPY_THRESHOLD:
            findings.append(
                SecretFinding(kind="high_entropy_token", start=m.start(),
                              end=m.end(), excerpt=_redact(m.group(0)))
            )
    return findings
