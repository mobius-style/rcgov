# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""Internal working record threaded through the pipeline.

``Governed`` pairs the contract ``Segment`` and ``GovernedSegment`` with the
resolved text and the intermediate signals (proposals, scan findings,
provenance) that downstream stages — conflict detection, priority, pack — need
but the slim contract objects intentionally do not carry.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .contract import (
    AuthorityState,
    Document,
    GovernedSegment,
    Segment,
    SegmentRole,
    TemporalStratum,
)

__all__ = ["Governed"]


@dataclass
class Governed:
    document: Document
    segment: Segment
    text: str
    role: SegmentRole
    authority: AuthorityState
    authority_confidence: float
    temporal: TemporalStratum
    provenance: str
    secret_findings: list[Any] = field(default_factory=list)
    injection_findings: list[Any] = field(default_factory=list)
    governed: GovernedSegment | None = None
    priority: float | None = None

    @property
    def title(self) -> str:
        return self.segment.heading_path[-1] if self.segment.heading_path else "(preamble)"

    @property
    def injectable(self) -> bool:
        from .contract import InjectionDecision

        return (
            self.governed is not None
            and self.governed.injection_decision == InjectionDecision.INJECT
        )
