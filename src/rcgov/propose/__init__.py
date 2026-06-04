# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""Proposal stage — role / authority / temporal labels (spec v0.4 §5).

Proposals are *suggestions only*. ``authority_proposed`` is never promoted to
``authority_committed`` here (contract §5 rule 1); commitment requires an
explicit source resolved downstream. When inter-rater kappa is low, the system
surfaces disagreement rather than asserting a label (paper §3.2 / §6).

The MVP proposers are transparent keyword heuristics (model-independent,
Decision Record 4). Each returns the contract enum plus, for authority, a
confidence in [0, 1] derived from match strength.
"""
from __future__ import annotations

from ..contract import AuthorityState, SegmentRole, Segment, TemporalStratum

__all__ = ["propose_role", "propose_authority", "propose_temporal"]


def _hits(text: str, terms: tuple[str, ...]) -> int:
    return sum(1 for t in terms if t in text)


# Ordered most-specific -> least; first non-zero category wins.
_ROLE_TERMS: tuple[tuple[SegmentRole, tuple[str, ...]], ...] = (
    (SegmentRole.DEPRECATED, ("deprecated", "superseded", "obsolete", "revoked",
                              "do not use", "historical", "no longer")),
    (SegmentRole.CONFLICT, ("conflict", "disagree", "mismatch", "contradict",
                            "drift", " vs ", "competing")),
    (SegmentRole.CONSTRAINT, ("must ", "must not", "never", "do not", "shall",
                              "required", "non-negotiable", "constraint", "always ",
                              "may not", "cannot")),
    (SegmentRole.HYPOTHESIS, ("hypothesis", "experimental", "bet", "untested",
                              "may improve", "should be tested", "ablation")),
    (SegmentRole.PREFERENCE, ("prefer", "style", "tone", "recommended", "default ",
                              "positioning")),
    (SegmentRole.EVIDENCE, ("evidence", "result", "metric", "kappa", "measured",
                            "recall", "precision", "telemetry")),
    (SegmentRole.GOAL, ("goal", "objective", "aim", "in scope", "roadmap",
                        "should ", "we will", "plan")),
)


def propose_role(segment: Segment, raw_text: str) -> SegmentRole:
    """Propose a single primary segment_role (contract §2.3)."""
    t = raw_text.lower()
    best: tuple[int, SegmentRole] | None = None
    for role, terms in _ROLE_TERMS:
        n = _hits(t, terms)
        if n and (best is None or n > best[0]):
            best = (n, role)
    return best[1] if best else SegmentRole.FACT


_AUTHORITY_TERMS: tuple[tuple[AuthorityState, tuple[str, ...]], ...] = (
    (AuthorityState.DEPRECATED_OR_UNAUTHORIZED,
     ("deprecated", "superseded", "revoked", "obsolete", "historical",
      "do not use", "unauthorized", "no longer")),
    (AuthorityState.DISPUTED,
     ("disputed", "conflict", "competing", "mismatch", "drift", "contradict")),
    (AuthorityState.CANONICAL,
     ("canonical", "non-negotiable", "binding", "constitution", "authority",
      "single source of truth", "frozen", "must", "license", "constraint")),
    (AuthorityState.WORKING,
     ("working", "draft", "provisional", "wip", "proposed", "sketch",
      "experimental", "tentative")),
)


def propose_authority(segment: Segment, raw_text: str) -> tuple[AuthorityState, float]:
    """Propose (authority_state, confidence). Proposal only — never committed."""
    t = raw_text.lower()
    best: tuple[int, AuthorityState] | None = None
    for state, terms in _AUTHORITY_TERMS:
        n = _hits(t, terms)
        if n and (best is None or n > best[0]):
            best = (n, state)
    if best is None:
        return AuthorityState.UNKNOWN, 0.2
    # Confidence: saturating in match count, capped so nothing reads as certain.
    confidence = min(0.9, 0.4 + 0.15 * best[0])
    return best[1], confidence


_TEMPORAL_TERMS: tuple[tuple[TemporalStratum, tuple[str, ...]], ...] = (
    (TemporalStratum.TEMPORARY,
     ("log", "error", "today", "temporary", "one-off", "tool output",
      "this branch", "right now", "immediate", "stack trace")),
    (TemporalStratum.DURABLE,
     ("license", "architecture", "principle", "policy", "constitution",
      "durable", "philosophy", "non-negotiable", "longue duree", "always",
      "never")),
    (TemporalStratum.CURRENT,
     ("current", "version", "sprint", "release", "branch", "active", "roadmap",
      "phase", "baseline", "now ")),
)


def propose_temporal(segment: Segment, raw_text: str) -> TemporalStratum:
    """Propose a temporal_stratum (contract §2.2)."""
    t = raw_text.lower()
    best: tuple[int, TemporalStratum] | None = None
    for stratum, terms in _TEMPORAL_TERMS:
        n = _hits(t, terms)
        if n and (best is None or n > best[0]):
            best = (n, stratum)
    return best[1] if best else TemporalStratum.UNKNOWN
