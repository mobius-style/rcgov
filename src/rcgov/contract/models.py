# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""RCGov core object model — strict mirror of Minimal Data Contract v0.1 (§3-§8).

Design rules carried directly from the contract:

- ``Segment`` stores text by **reference** (``text_ref`` + ``text_preview``),
  not inline. See Decision Record 3(a): provenance hashing and the "do not
  duplicate secret text everywhere" rule both favour storage by reference.
- ``GovernedSegment.authority_proposed`` may **never** substitute for
  ``authority_committed`` (contract §5 rule 1). They are distinct fields and the
  commitment must come from an explicit source.
- ``priority_score`` is populated **only after** non-compensatory gates have run
  (contract §5 rule 2 / §9).

Every model offers ``to_dict()`` / ``from_dict()`` that round-trip to the JSON
shape shown in the contract document, so the dogfooding diff can compare on-disk
artifacts field-for-field.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional

from .enums import (
    AuthorityState,
    DownstreamOutcomeType,
    GateResult,
    InjectionDecision,
    OverrideReason,
    SegmentRole,
    TemporalStratum,
)

__all__ = [
    "SourceSpan",
    "Document",
    "Segment",
    "GovernedSegment",
    "Disagreement",
    "Override",
    "DownstreamOutcome",
]


def _require(value: Any, name: str) -> Any:
    """Contract required-field guard: reject None / empty string."""
    if value is None or (isinstance(value, str) and value == ""):
        raise ValueError(f"required field {name!r} is missing or empty")
    return value


@dataclass(frozen=True)
class SourceSpan:
    """Byte offsets of a segment within its source document."""

    start: int
    end: int

    def __post_init__(self) -> None:
        if self.start < 0 or self.end < self.start:
            raise ValueError(f"invalid source_span: ({self.start}, {self.end})")

    def to_dict(self) -> dict[str, int]:
        return {"start": self.start, "end": self.end}

    @classmethod
    def from_dict(cls, d: dict[str, int]) -> "SourceSpan":
        return cls(start=int(d["start"]), end=int(d["end"]))


@dataclass
class Document:
    """Contract v0.1 §3. Required: document_id, source_path, document_type,
    ingested_at, hash, raw_text_ref."""

    document_id: str
    source_path: str
    document_type: str
    ingested_at: str
    hash: str
    raw_text_ref: str
    created_at: Optional[str] = None
    modified_at: Optional[str] = None

    def __post_init__(self) -> None:
        for name in (
            "document_id",
            "source_path",
            "document_type",
            "ingested_at",
            "hash",
            "raw_text_ref",
        ):
            _require(getattr(self, name), name)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Document":
        return cls(
            document_id=d["document_id"],
            source_path=d["source_path"],
            document_type=d["document_type"],
            ingested_at=d["ingested_at"],
            hash=d["hash"],
            raw_text_ref=d["raw_text_ref"],
            created_at=d.get("created_at"),
            modified_at=d.get("modified_at"),
        )


@dataclass
class Segment:
    """Contract v0.1 §4. Required: segment_id, document_id, text_ref, hash.

    Note the canonical text-by-reference shape (Decision Record 3a): the raw text
    lives in the store behind ``text_ref``; ``text_preview`` is a short,
    secret-free excerpt for human display only.
    """

    segment_id: str
    document_id: str
    text_ref: str
    hash: str
    heading_path: list[str] = field(default_factory=list)
    text_preview: str = ""
    token_estimate: int = 0
    source_span: Optional[SourceSpan] = None

    def __post_init__(self) -> None:
        for name in ("segment_id", "document_id", "text_ref", "hash"):
            _require(getattr(self, name), name)

    def to_dict(self) -> dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "document_id": self.document_id,
            "heading_path": list(self.heading_path),
            "text_ref": self.text_ref,
            "text_preview": self.text_preview,
            "token_estimate": self.token_estimate,
            "source_span": self.source_span.to_dict() if self.source_span else None,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Segment":
        span = d.get("source_span")
        return cls(
            segment_id=d["segment_id"],
            document_id=d["document_id"],
            text_ref=d["text_ref"],
            hash=d["hash"],
            heading_path=list(d.get("heading_path", [])),
            text_preview=d.get("text_preview", ""),
            token_estimate=int(d.get("token_estimate", 0)),
            source_span=SourceSpan.from_dict(span) if span else None,
        )


@dataclass
class GovernedSegment:
    """Contract v0.1 §5. The result of running a Segment through proposal,
    provenance appraisal, and the non-compensatory gate layer.

    Invariants enforced here:
      1. authority_proposed never substitutes for authority_committed;
      2. priority_score is None until gates have run (set by the priority stage);
      3. a hard gate_result (block/quarantine) forbids an ``inject`` decision.
    """

    segment_id: str
    role_proposed: SegmentRole
    authority_proposed: AuthorityState
    temporal_stratum_proposed: TemporalStratum
    provenance_quality: str
    safety_status: str
    gate_result: GateResult
    injection_decision: InjectionDecision
    authority_committed: Optional[AuthorityState] = None
    commitment_source: Optional[str] = None
    priority_score: Optional[float] = None
    notes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        # Coerce any raw strings into the closed contract enums.
        self.role_proposed = SegmentRole.coerce(self.role_proposed)
        self.authority_proposed = AuthorityState.coerce(self.authority_proposed)
        self.temporal_stratum_proposed = TemporalStratum.coerce(
            self.temporal_stratum_proposed
        )
        self.gate_result = GateResult.coerce(self.gate_result)
        self.injection_decision = InjectionDecision.coerce(self.injection_decision)
        if self.authority_committed is not None:
            self.authority_committed = AuthorityState.coerce(self.authority_committed)
            if self.commitment_source is None:
                raise ValueError(
                    "authority_committed requires a commitment_source "
                    "(contract §4.4): commitment must have an explicit origin"
                )
        # Hard gates cannot resolve to an injecting decision.
        from .enums import HARD_GATE_RESULTS

        if (
            self.gate_result in HARD_GATE_RESULTS
            and self.injection_decision == InjectionDecision.INJECT
        ):
            raise ValueError(
                f"gate_result={self.gate_result.value} (hard gate) cannot pair "
                f"with injection_decision=inject (contract §5 rule 3)"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "role_proposed": self.role_proposed.value,
            "authority_proposed": self.authority_proposed.value,
            "authority_committed": (
                self.authority_committed.value if self.authority_committed else None
            ),
            "commitment_source": self.commitment_source,
            "temporal_stratum_proposed": self.temporal_stratum_proposed.value,
            "provenance_quality": self.provenance_quality,
            "safety_status": self.safety_status,
            "gate_result": self.gate_result.value,
            "injection_decision": self.injection_decision.value,
            "priority_score": self.priority_score,
            "notes": list(self.notes),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "GovernedSegment":
        return cls(
            segment_id=d["segment_id"],
            role_proposed=d["role_proposed"],
            authority_proposed=d["authority_proposed"],
            temporal_stratum_proposed=d["temporal_stratum_proposed"],
            provenance_quality=d["provenance_quality"],
            safety_status=d["safety_status"],
            gate_result=d["gate_result"],
            injection_decision=d["injection_decision"],
            authority_committed=d.get("authority_committed"),
            commitment_source=d.get("commitment_source"),
            priority_score=d.get("priority_score"),
            notes=list(d.get("notes", [])),
        )


@dataclass
class Disagreement:
    """Contract v0.1 §6. A surfaced authority/version/constraint conflict."""

    disagreement_id: str
    type: str
    segments: list[str]
    summary: str
    task_relevance: float = 0.0
    base_severity: float = 0.0
    impact_scope: str = "unknown"
    irreversibility_risk: float = 0.0
    alert_route: Optional[GateResult] = None

    def __post_init__(self) -> None:
        _require(self.disagreement_id, "disagreement_id")
        if self.alert_route is not None:
            self.alert_route = GateResult.coerce(self.alert_route)

    def to_dict(self) -> dict[str, Any]:
        return {
            "disagreement_id": self.disagreement_id,
            "type": self.type,
            "segments": list(self.segments),
            "summary": self.summary,
            "task_relevance": self.task_relevance,
            "base_severity": self.base_severity,
            "impact_scope": self.impact_scope,
            "irreversibility_risk": self.irreversibility_risk,
            "alert_route": self.alert_route.value if self.alert_route else None,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Disagreement":
        return cls(
            disagreement_id=d["disagreement_id"],
            type=d["type"],
            segments=list(d.get("segments", [])),
            summary=d.get("summary", ""),
            task_relevance=float(d.get("task_relevance", 0.0)),
            base_severity=float(d.get("base_severity", 0.0)),
            impact_scope=d.get("impact_scope", "unknown"),
            irreversibility_risk=float(d.get("irreversibility_risk", 0.0)),
            alert_route=d.get("alert_route"),
        )


@dataclass
class Override:
    """Contract v0.1 §7. A reasoned override of a surfaced disagreement."""

    override_id: str
    disagreement_id: str
    reason_code: OverrideReason
    free_text_reason: str = ""
    timestamp: Optional[str] = None
    downstream_outcome: Optional[str] = None

    def __post_init__(self) -> None:
        _require(self.override_id, "override_id")
        _require(self.disagreement_id, "disagreement_id")
        self.reason_code = OverrideReason.coerce(self.reason_code)

    def to_dict(self) -> dict[str, Any]:
        return {
            "override_id": self.override_id,
            "disagreement_id": self.disagreement_id,
            "reason_code": self.reason_code.value,
            "free_text_reason": self.free_text_reason,
            "timestamp": self.timestamp,
            "downstream_outcome": self.downstream_outcome,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Override":
        return cls(
            override_id=d["override_id"],
            disagreement_id=d["disagreement_id"],
            reason_code=d["reason_code"],
            free_text_reason=d.get("free_text_reason", ""),
            timestamp=d.get("timestamp"),
            downstream_outcome=d.get("downstream_outcome"),
        )


@dataclass
class DownstreamOutcome:
    """Contract v0.1 §8. The observed result attached to an override later."""

    outcome_id: str
    override_id: str
    event_type: DownstreamOutcomeType
    timestamp: Optional[str] = None
    evidence_ref: Optional[str] = None
    severity: str = "unknown"

    def __post_init__(self) -> None:
        _require(self.outcome_id, "outcome_id")
        _require(self.override_id, "override_id")
        self.event_type = DownstreamOutcomeType.coerce(self.event_type)

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome_id": self.outcome_id,
            "override_id": self.override_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "evidence_ref": self.evidence_ref,
            "severity": self.severity,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "DownstreamOutcome":
        return cls(
            outcome_id=d["outcome_id"],
            override_id=d["override_id"],
            event_type=d["event_type"],
            timestamp=d.get("timestamp"),
            evidence_ref=d.get("evidence_ref"),
            severity=d.get("severity", "unknown"),
        )
