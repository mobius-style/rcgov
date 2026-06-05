# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""Tests for the streamlit-free application service layer."""
from __future__ import annotations

from rcgov.service import ARTIFACT_ORDER, govern_bytes

DOC_A = b"# Policy\n\n## License\n\nThe code is AGPL-3.0-or-later; non-negotiable.\n"
DOC_B = b"# Notes\n\nUse the key AKIAIOSFODNN7EXAMPLE to deploy.\n"


def test_govern_bytes_produces_artifacts(tmp_path):
    result = govern_bytes(
        [("policy.md", DOC_A), ("notes.md", DOC_B)],
        task="What is the license policy?",
        workdir=tmp_path,
    )
    # Every advertised artifact came back as text.
    for name in ARTIFACT_ORDER:
        assert name in result.artifacts, f"missing artifact {name}"

    assert result.manifest["counts"]["documents"] == 2
    # The secret is quarantined: absent from the pack, present in the report.
    assert "AKIAIOSFODNN7EXAMPLE" not in result.artifacts["CLEAN_CONTEXT_PACK.md"]
    assert "aws_access_key" in result.artifacts["NON_INJECTION_REPORT.md"]
    assert result.summary


def test_govern_bytes_honors_commitments(tmp_path):
    commitments = b"commitments:\n  - heading_match: License\n    authority: canonical\n    commitment_source: signed_policy\n"
    result = govern_bytes(
        [("policy.md", DOC_A)],
        task="license",
        commitments=commitments,
        workdir=tmp_path,
    )
    assert result.manifest["counts"]["committed"] >= 1
    assert "AGPL-3.0-or-later" in result.artifacts["CLEAN_CONTEXT_PACK.md"]


def test_filename_is_sanitized(tmp_path):
    """A traversal-style upload name is reduced to its basename."""
    result = govern_bytes(
        [("../../etc/evil.md", b"# X\n\nhello\n")],
        task="x",
        workdir=tmp_path,
    )
    assert result.manifest["counts"]["documents"] == 1
    # nothing was written outside the scratch inputs dir
    assert (tmp_path / "inputs" / "evil.md").exists()
