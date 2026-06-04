# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""Contract-layer tests: enums, models, invariants. These must stay green."""
from __future__ import annotations

import pytest

from rcgov.contract import (
    AuthorityState,
    DownstreamOutcome,
    DownstreamOutcomeType,
    Disagreement,
    Document,
    GateResult,
    GovernedSegment,
    InjectionDecision,
    Override,
    OverrideReason,
    Segment,
    SegmentRole,
    SourceSpan,
    TemporalStratum,
)


# --- enums: exact value sets and order (mirror of contract v0.1 §2) --------
def test_authority_state_values():
    assert AuthorityState.values() == [
        "canonical",
        "working",
        "disputed",
        "deprecated_or_unauthorized",
        "unknown",
    ]


def test_temporal_stratum_values():
    assert TemporalStratum.values() == ["durable", "current", "temporary", "unknown"]


def test_segment_role_count_and_members():
    assert SegmentRole.values() == [
        "constraint", "goal", "fact", "hypothesis", "preference",
        "evidence", "deprecated", "conflict", "secret_or_risk", "noise",
    ]


def test_injection_decision_values():
    assert InjectionDecision.values() == [
        "inject", "digest", "background", "quarantine", "archive", "requires_review",
    ]


def test_gate_result_values():
    assert GateResult.values() == [
        "pass", "soft_warn", "foreground_warn", "block", "quarantine",
    ]


def test_override_reason_values():
    assert OverrideReason.values() == [
        "irrelevant_to_current_task", "temporary_working_assumption",
        "user_selects_segment_a", "will_review_later", "known_false_positive", "other",
    ]


def test_downstream_outcome_type_count():
    assert len(DownstreamOutcomeType.values()) == 10


def test_coerce_rejects_unknown():
    with pytest.raises(ValueError):
        AuthorityState.coerce("super_canonical")


def test_enum_is_json_string():
    import json
    assert json.dumps(GateResult.QUARANTINE) == '"quarantine"'


# --- models: required fields + round-trip ----------------------------------
def test_document_requires_core_fields():
    with pytest.raises(ValueError):
        Document(document_id="", source_path="x", document_type="md",
                 ingested_at="t", hash="sha256:..", raw_text_ref="r")


def test_segment_roundtrip():
    seg = Segment(
        segment_id="seg_1", document_id="doc_1",
        text_ref="storage://segments/seg_1", hash="sha256:abc",
        heading_path=["RCGov", "Authority"], text_preview="preview",
        token_estimate=3, source_span=SourceSpan(10, 20),
    )
    again = Segment.from_dict(seg.to_dict())
    assert again == seg


def test_governed_segment_authority_proposed_not_committed():
    """A proposed-canonical with no commitment must be foregrounded and routed
    to review (Authority Commitment Gate, contract §4.4)."""
    gs = GovernedSegment(
        segment_id="seg_1", role_proposed="constraint",
        authority_proposed="canonical", temporal_stratum_proposed="durable",
        provenance_quality="known_source", safety_status="pass",
        gate_result="foreground_warn", injection_decision="requires_review",
    )
    assert gs.authority_committed is None
    assert gs.to_dict()["authority_committed"] is None


def test_committed_authority_requires_source():
    with pytest.raises(ValueError):
        GovernedSegment(
            segment_id="seg_1", role_proposed="constraint",
            authority_proposed="canonical", temporal_stratum_proposed="durable",
            provenance_quality="known_source", safety_status="pass",
            gate_result="pass", injection_decision="inject",
            authority_committed="canonical",  # no commitment_source -> error
        )


def test_hard_gate_cannot_inject():
    with pytest.raises(ValueError):
        GovernedSegment(
            segment_id="seg_1", role_proposed="secret_or_risk",
            authority_proposed="unknown", temporal_stratum_proposed="unknown",
            provenance_quality="weak", safety_status="fail",
            gate_result="quarantine", injection_decision="inject",
        )


def test_override_and_outcome_roundtrip():
    ov = Override(override_id="ovr_1", disagreement_id="dis_1",
                  reason_code="temporary_working_assumption")
    assert Override.from_dict(ov.to_dict()) == ov

    out = DownstreamOutcome(outcome_id="out_1", override_id="ovr_1",
                            event_type="build_failure", severity="medium")
    assert DownstreamOutcome.from_dict(out.to_dict()) == out


def test_disagreement_alert_route_coercion():
    dis = Disagreement(disagreement_id="dis_1", type="api_version_conflict",
                       segments=["s1", "s2"], summary="x", alert_route="foreground_warn")
    assert dis.alert_route == GateResult.FOREGROUND_WARN
