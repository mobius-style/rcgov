# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""RCGov data contract — canonical mirror of Minimal Data Contract v0.1.

This package is the single source of truth for the implementation. The prose
definition lives in ``docs/minimal_data_contract_v0_1.md``; this code expression
is AGPL-3.0-or-later.
"""
from __future__ import annotations

from .enums import (
    AuthorityState,
    DownstreamOutcomeType,
    GateResult,
    InjectionDecision,
    OverrideReason,
    SegmentRole,
    TemporalStratum,
    HARD_GATE_RESULTS,
    HIGH_AUTHORITY_STATES,
)
from .models import (
    Disagreement,
    Document,
    DownstreamOutcome,
    GovernedSegment,
    Override,
    Segment,
    SourceSpan,
)

# Output file names — contract v0.1 §11.
OUTPUT_FILES = (
    "CLEAN_CONTEXT_PACK.md",
    "NON_INJECTION_REPORT.md",
    "AUTHORITY_REVIEW_QUEUE.jsonl",
    "OVERRIDE_LOG.jsonl",
    "DOWNSTREAM_OUTCOME_LOG.jsonl",
    "CONTEXT_MANIFEST.json",
)

CONTRACT_VERSION = "0.1"

__all__ = [
    "AuthorityState",
    "TemporalStratum",
    "SegmentRole",
    "InjectionDecision",
    "GateResult",
    "OverrideReason",
    "DownstreamOutcomeType",
    "HARD_GATE_RESULTS",
    "HIGH_AUTHORITY_STATES",
    "Document",
    "Segment",
    "SourceSpan",
    "GovernedSegment",
    "Disagreement",
    "Override",
    "DownstreamOutcome",
    "OUTPUT_FILES",
    "CONTRACT_VERSION",
]
