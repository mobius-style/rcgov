# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""Proposal stage — role / authority / temporal labels (spec v0.4 §5).

STATUS: stub. Proposals are *suggestions only*. authority_proposed must never be
promoted to authority_committed here (contract §5 rule 1); commitment requires an
explicit source resolved downstream. When inter-rater kappa is low, the system
surfaces disagreement rather than asserting a label (paper v0.7 §3.2 / §6).
"""
from __future__ import annotations

from ..contract import AuthorityState, SegmentRole, Segment, TemporalStratum

__all__ = ["propose_role", "propose_authority", "propose_temporal"]


def propose_role(segment: Segment, raw_text: str) -> SegmentRole:
    """Propose a single primary segment_role. TODO: heuristic + optional ME5."""
    raise NotImplementedError("propose_role: see contract §2.3 role set")


def propose_authority(segment: Segment, raw_text: str) -> tuple[AuthorityState, float]:
    """Propose (authority_state, confidence). Proposal only — never committed."""
    raise NotImplementedError("propose_authority: see paper v0.7 §3.2")


def propose_temporal(segment: Segment, raw_text: str) -> TemporalStratum:
    """Propose a temporal_stratum (durable/current/temporary/unknown)."""
    raise NotImplementedError("propose_temporal: see contract §2.2")
