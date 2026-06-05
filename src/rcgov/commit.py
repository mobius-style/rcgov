# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""Authority commitment resolution (spec v0.4 §4.4 / §11).

A *proposed* authority label is only a suggestion; it must never bind on its own
(contract §5 rule 1). Commitment is the explicit act that lets authority bind.
For a local-first MVP the commitment source is a small **commitment manifest** —
the user's "smallest anchor set" from Authority Stabilization Mode (spec §11) —
rather than per-segment clicking.

Manifest shape (``config/commitments.yaml``):

    commitments:
      - source_match: "minimal_data_contract"   # substring/glob on source_path
        authority: canonical
        commitment_source: repository_manifest
      - heading_match: "License"                 # substring on any heading crumb
        authority: canonical
        commitment_source: signed_policy

Rules are tried in order; the first match wins. A rule with both ``source_match``
and ``heading_match`` requires both to match. Commitment beats proposal: a
committed segment is placed by its committed authority, and the Authority
Commitment Gate (spec §6.4) no longer foregrounds it.
"""
from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from pathlib import Path

from .contract import AuthorityState, Document, Segment

__all__ = ["CommitmentRule", "CommitmentManifest", "load_commitments", "STABILIZATION_MESSAGE"]

# spec §11 — the smallest anchor set that makes governance possible.
STABILIZATION_MESSAGE = (
    "This project lacks a stable authority baseline. Please decide these five "
    "items: 1) active product target; 2) active version or branch; 3) current "
    "license policy; 4) current implementation priority; 5) deprecated documents "
    "or instructions."
)


def _matches(pattern: str, value: str) -> bool:
    """Substring OR glob match (so both 'License' and '*license*' work)."""
    return pattern in value or fnmatch.fnmatch(value.lower(), pattern.lower())


@dataclass(frozen=True)
class CommitmentRule:
    authority: AuthorityState
    commitment_source: str
    source_match: str | None = None
    heading_match: str | None = None

    def applies(self, document: Document, segment: Segment) -> bool:
        if self.source_match is not None and not _matches(self.source_match, document.source_path):
            return False
        if self.heading_match is not None:
            crumb = " / ".join(segment.heading_path)
            if not _matches(self.heading_match, crumb):
                return False
        # A rule with neither selector never matches (avoids committing everything).
        return self.source_match is not None or self.heading_match is not None


@dataclass(frozen=True)
class CommitmentManifest:
    rules: tuple[CommitmentRule, ...] = ()

    def resolve(self, document: Document, segment: Segment) -> tuple[AuthorityState | None, str | None]:
        """Return (committed_authority, commitment_source) or (None, None)."""
        for rule in self.rules:
            if rule.applies(document, segment):
                return rule.authority, rule.commitment_source
        return None, None

    def __bool__(self) -> bool:
        return bool(self.rules)


def load_commitments(path: str | Path | None) -> CommitmentManifest:
    """Load a commitment manifest, or an empty one if absent/None."""
    if path is None:
        return CommitmentManifest()
    p = Path(path)
    if not p.exists():
        return CommitmentManifest()
    try:
        import yaml
    except ImportError:  # pragma: no cover
        return CommitmentManifest()
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    rules: list[CommitmentRule] = []
    for entry in data.get("commitments", []):
        rules.append(CommitmentRule(
            authority=AuthorityState.coerce(entry.get("authority", "canonical")),
            commitment_source=entry.get("commitment_source", "repository_manifest"),
            source_match=entry.get("source_match"),
            heading_match=entry.get("heading_match"),
        ))
    return CommitmentManifest(tuple(rules))
