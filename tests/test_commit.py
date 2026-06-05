# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""Tests for authority commitment resolution and its pipeline effect."""
from __future__ import annotations

import json

from rcgov.commit import (
    CommitmentManifest,
    CommitmentRule,
    load_commitments,
)
from rcgov.contract import AuthorityState, Document, Segment
from rcgov.pipeline import RunConfig, run


def _doc(source_path: str) -> Document:
    return Document(document_id="doc_x", source_path=source_path,
                    document_type="markdown", ingested_at="t",
                    hash="sha256:x", raw_text_ref="rcgovstore://x")


def _seg(heading_path):
    return Segment(segment_id="seg_x", document_id="doc_x",
                   text_ref="rcgovstore://x", hash="sha256:x",
                   heading_path=heading_path)


def test_rule_requires_a_selector():
    """A rule with neither selector never commits anything (no blanket commit)."""
    rule = CommitmentRule(authority=AuthorityState.CANONICAL,
                          commitment_source="repository_manifest")
    assert not rule.applies(_doc("anything.md"), _seg(["A"]))


def test_source_match_resolves():
    m = CommitmentManifest((CommitmentRule(
        authority=AuthorityState.CANONICAL, commitment_source="repository_manifest",
        source_match="contract"),))
    auth, src = m.resolve(_doc("docs/minimal_data_contract_v0_1.md"), _seg(["Enums"]))
    assert auth == AuthorityState.CANONICAL
    assert src == "repository_manifest"
    auth2, _ = m.resolve(_doc("docs/paper.md"), _seg(["X"]))
    assert auth2 is None


def test_heading_and_source_both_required():
    m = CommitmentManifest((CommitmentRule(
        authority=AuthorityState.CANONICAL, commitment_source="signed_policy",
        source_match="constitution", heading_match="License"),))
    assert m.resolve(_doc("constitution.md"), _seg(["Root", "License"]))[0] == AuthorityState.CANONICAL
    assert m.resolve(_doc("constitution.md"), _seg(["Root", "Other"]))[0] is None
    assert m.resolve(_doc("other.md"), _seg(["License"]))[0] is None


def test_load_commitments_from_file(tmp_path):
    p = tmp_path / "commitments.yaml"
    p.write_text(
        "commitments:\n"
        "  - source_match: spec\n"
        "    authority: canonical\n"
        "    commitment_source: repository_manifest\n",
        encoding="utf-8",
    )
    m = load_commitments(p)
    assert len(m.rules) == 1
    assert m.resolve(_doc("docs/spec_v0_4.md"), _seg(["X"]))[0] == AuthorityState.CANONICAL


def test_missing_file_yields_empty_manifest(tmp_path):
    m = load_commitments(tmp_path / "nope.yaml")
    assert not m  # empty manifest is falsy


# --- pipeline effect: commitment makes canonical material injectable -------
_CONSTITUTION = (
    "# Project Constitution\n\n## License\n\n"
    "The code is licensed under AGPL-3.0-or-later; this is non-negotiable.\n"
)


def test_commitment_moves_canonical_into_pack(tmp_path):
    doc = tmp_path / "constitution.md"
    doc.write_text(_CONSTITUTION, encoding="utf-8")
    commitments = tmp_path / "commit.yaml"
    commitments.write_text(
        "commitments:\n"
        "  - heading_match: License\n"
        "    authority: canonical\n"
        "    commitment_source: signed_policy\n",
        encoding="utf-8",
    )

    # Without commitments: uncommitted canonical -> review, stabilization advised.
    cfg0 = RunConfig(task="license", output_dir=tmp_path / "out0",
                     store_dir=tmp_path / "s0", injection_seeds_path=None,
                     commitments_path=None)
    r0 = run([str(doc)], cfg0)
    pack0 = (cfg0.output_dir / "CLEAN_CONTEXT_PACK.md").read_text("utf-8")
    man0 = json.loads((cfg0.output_dir / "CONTEXT_MANIFEST.json").read_text("utf-8"))
    assert "AGPL-3.0-or-later" not in pack0
    assert man0["authority_stabilization"]["recommended"] is True

    # With commitments: the License clause binds and reaches the pack.
    cfg1 = RunConfig(task="license", output_dir=tmp_path / "out1",
                     store_dir=tmp_path / "s1", injection_seeds_path=None,
                     commitments_path=commitments)
    r1 = run([str(doc)], cfg1)
    pack1 = (cfg1.output_dir / "CLEAN_CONTEXT_PACK.md").read_text("utf-8")
    man1 = json.loads((cfg1.output_dir / "CONTEXT_MANIFEST.json").read_text("utf-8"))
    assert "AGPL-3.0-or-later" in pack1
    assert "Active Canonical / Committed Context" in pack1
    assert "committed=canonical(signed_policy)" in pack1
    assert man1["counts"]["committed"] >= 1
    assert man1["authority_stabilization"]["recommended"] is False
