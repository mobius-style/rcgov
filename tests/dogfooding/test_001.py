# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""Dogfooding Test 001 — RCGov governs its own documentation.

Decision Record 3(b): retargeted to the current synchronized trio
(paper_v0_7 / spec_v0_4 / minimal_data_contract_v0_1).

What runs today (scaffold):
  - contract <-> doc consistency: every enum value in code appears in the
    canonical contract document (guards against schema_field_mismatch drift);
  - encoding_mojibake: the dirty fixture is detected and repaired by ingest.

What is deferred (xfail): the full pipeline run that emits CONFLICT_MAP.md etc.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from rcgov.contract import (
    AuthorityState,
    DownstreamOutcomeType,
    GateResult,
    InjectionDecision,
    OverrideReason,
    SegmentRole,
    TemporalStratum,
)
from rcgov.ingest import clean_encoding

DOCS = Path(__file__).resolve().parents[2] / "docs"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
CONTRACT_DOC = DOCS / "minimal_data_contract_v0_1.md"

ALL_ENUMS = [
    AuthorityState, TemporalStratum, SegmentRole, InjectionDecision,
    GateResult, OverrideReason, DownstreamOutcomeType,
]


def test_inputs_present():
    for name in ("paper_v0_7.md", "spec_v0_4.md", "minimal_data_contract_v0_1.md"):
        assert (DOCS / name).exists(), f"dogfooding input missing: {name}"


@pytest.mark.parametrize("enum_cls", ALL_ENUMS, ids=[e.__name__ for e in ALL_ENUMS])
def test_contract_enum_values_appear_in_doc(enum_cls):
    """Every code-side enum value must appear in the canonical contract doc.

    This is the schema_field_mismatch guard: if code and the contract drift
    apart, this fails — exactly the kind of drift RCGov is built to detect.
    """
    doc = CONTRACT_DOC.read_text(encoding="utf-8")
    for value in enum_cls.values():
        assert value in doc, (
            f"{enum_cls.__name__} value {value!r} not found in {CONTRACT_DOC.name}"
        )


def test_clean_docs_have_no_mojibake():
    """The cleaned docs in docs/ must not carry the known mojibake sequence."""
    for md in DOCS.glob("*.md"):
        text = md.read_text(encoding="utf-8")
        assert "â€”" not in text, f"mojibake leaked into {md.name}"


def test_mojibake_fixture_is_detected_and_repaired():
    dirty = (FIXTURES / "mojibake_dirty.md").read_text(encoding="utf-8")
    assert "â€”" in dirty  # fixture really is dirty
    repaired = clean_encoding(dirty)
    assert "â€”" not in repaired
    assert "—" in repaired  # em dash restored


@pytest.mark.xfail(reason="pipeline stages (ingest/segment/propose) not yet built",
                   raises=NotImplementedError, strict=True)
def test_full_dogfooding_run_emits_artifacts():
    from rcgov.pipeline import RunConfig, run

    cfg = RunConfig(task="Audit RCGov's own docs for drift")
    run([str(DOCS / "paper_v0_7.md"), str(DOCS / "spec_v0_4.md"),
         str(CONTRACT_DOC)], cfg)
