# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""Application service layer — turn in-memory uploads into a governance run.

This is the streamlit-free core behind the Streamlit MVP: it materializes
uploaded bytes to a scratch workdir, runs the pipeline, and reads the artifacts
back as text. Keeping it here (not in ``app/``) means the app logic is unit
testable without importing streamlit or driving a browser.
"""
from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from .contract import OUTPUT_FILES
from .pipeline import RunConfig, run

__all__ = ["GovernResult", "govern_bytes", "ARTIFACT_ORDER"]

# Display order for the UI (contract artifacts first, then dogfooding extras).
ARTIFACT_ORDER = (
    "CLEAN_CONTEXT_PACK.md",
    "NON_INJECTION_REPORT.md",
    "CONFLICT_MAP.md",
    "MINIMAL_DATA_CONTRACT_DIFF.md",
    "AUTHORITY_REVIEW_QUEUE.jsonl",
    "OVERRIDE_LOG.jsonl",
    "DOWNSTREAM_OUTCOME_LOG.jsonl",
    "CONTEXT_MANIFEST.json",
)


@dataclass
class GovernResult:
    summary: str
    artifacts: dict[str, str]  # filename -> text content
    manifest: dict = field(default_factory=dict)
    workdir: Path | None = None


def govern_bytes(
    inputs: list[tuple[str, bytes]],
    task: str,
    *,
    profile: str = "Balanced",
    temporal_attention: bool = False,
    commitments: bytes | None = None,
    workdir: str | Path | None = None,
) -> GovernResult:
    """Govern uploaded ``(filename, bytes)`` inputs and return artifact text.

    A scratch ``workdir`` is created if none is given. ``commitments`` is an
    optional commitment-manifest YAML; when omitted, no authority is committed.
    """
    root = Path(workdir) if workdir is not None else Path(tempfile.mkdtemp(prefix="rcgov_"))
    in_dir = root / "inputs"
    in_dir.mkdir(parents=True, exist_ok=True)

    paths: list[str] = []
    for name, data in inputs:
        safe = Path(name).name or "upload"
        p = in_dir / safe
        p.write_bytes(data)
        paths.append(str(p))

    commitments_path = None
    if commitments is not None:
        commitments_path = root / "commitments.yaml"
        commitments_path.write_bytes(commitments)

    cfg = RunConfig(
        task=task,
        profile=profile,
        temporal_attention=temporal_attention,
        output_dir=root / "out",
        store_dir=root / "store",
        commitments_path=commitments_path,
    )
    result = run(paths, cfg)

    artifacts: dict[str, str] = {}
    for name in OUTPUT_FILES + ("CONFLICT_MAP.md", "MINIMAL_DATA_CONTRACT_DIFF.md"):
        p = cfg.output_dir / name
        if p.exists():
            artifacts[name] = p.read_text(encoding="utf-8")

    manifest: dict = {}
    if "CONTEXT_MANIFEST.json" in artifacts:
        manifest = json.loads(artifacts["CONTEXT_MANIFEST.json"])

    return GovernResult(summary=result.summary, artifacts=artifacts,
                        manifest=manifest, workdir=root)
