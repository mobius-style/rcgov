# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""RCGov pipeline orchestration (spec v0.4 §5).

    Input Files
      -> Ingest -> Segment -> Scan (secret / prompt-injection)
      -> Propose (role / authority / temporal) -> Provenance
      -> Non-Compensatory Gates -> Priority Ranking -> Conflict Detection
      -> Pack Placement
      -> Clean Context Pack + Non-Injection Report + Conflict Map
         + Contract Diff + Review Queue + Override/Outcome logs + Manifest

This wires the stage modules into one run and writes the contract's output files
(plus the dogfooding artifacts) into ``config.output_dir``.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .contract import (
    GovernedSegment,
    GateResult,
    InjectionDecision,
    SegmentRole,
)
from .conflict import detect_conflicts, DETECTOR_NAMES
from .gates import GateInputs, run_gates
from .ingest import ingest_file
from .pack import (
    build_clean_pack,
    build_conflict_map,
    build_contract_diff,
    build_manifest,
    build_non_injection_report,
)
from .priority import score_segment
from .propose import propose_authority, propose_role, propose_temporal
from .provenance import appraise_provenance, meets_minimum
from .records import Governed
from .scan import scan_injection, scan_secrets
from .scan.injection import load_seeds
from .segment import segment_document
from .store import TextStore

__all__ = ["RunConfig", "GovernanceRun", "run"]


@dataclass
class RunConfig:
    """Configuration for one governance run."""

    task: str
    profile: str = "Balanced"  # Conservative / Balanced / Aggressive / Research
    temporal_attention: bool = False  # experimental opt-in (spec §8.3)
    output_dir: Path = field(default_factory=lambda: Path("out"))
    store_dir: Path = field(default_factory=lambda: Path(".rcgov_store"))
    injection_seeds_path: Path | None = Path("config/injection_seeds.yaml")


@dataclass
class GovernanceRun:
    """Result handle: produced artifact paths, the governed records, summary."""

    config: RunConfig
    artifacts: dict[str, Path] = field(default_factory=dict)
    governed: list[Governed] = field(default_factory=list)
    disagreements: list = field(default_factory=list)
    summary: str = ""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _govern_one(rec: Governed, *, requests_injection: bool) -> GovernedSegment:
    """Run scan-driven + structural gates for one record, returning the
    contract GovernedSegment with its injection decision and priority."""
    outcome = run_gates(GateInputs(
        has_secret=bool(rec.secret_findings),
        has_injection=bool(rec.injection_findings),
        provenance_meets_minimum=meets_minimum(rec.provenance),
        requests_injection=requests_injection,
        authority_proposed=rec.authority,
        authority_committed=None,  # nothing is committed in an unattended run
    ))
    # Deprecated material is never injected even if otherwise clean.
    decision = outcome.injection_decision
    if rec.authority.value == "deprecated_or_unauthorized" and decision == InjectionDecision.INJECT:
        decision = InjectionDecision.ARCHIVE
    role = SegmentRole.SECRET_OR_RISK if rec.secret_findings else rec.role
    return GovernedSegment(
        segment_id=rec.segment.segment_id,
        role_proposed=role,
        authority_proposed=rec.authority,
        temporal_stratum_proposed=rec.temporal,
        provenance_quality=rec.provenance,
        safety_status="fail" if rec.secret_findings else "pass",
        gate_result=outcome.gate_result,
        injection_decision=decision,
        notes=list(outcome.notes),
    )


def run(input_files: list[str | Path], config: RunConfig) -> GovernanceRun:
    """Execute the full pipeline over ``input_files`` and emit artifacts."""
    store = TextStore(config.store_dir)
    seeds = load_seeds(config.injection_seeds_path)
    ingested_at = _now()

    governed: list[Governed] = []
    inputs_meta: list[dict] = []
    mojibake_docs: dict[str, str] = {}
    contract_doc_text: str | None = None

    for i, path in enumerate(input_files):
        doc_id = f"doc_{i:03d}"
        res = ingest_file(path, document_id=doc_id, ingested_at=ingested_at, store=store)
        if res.had_mojibake:
            mojibake_docs[doc_id] = res.document.source_path
        if "minimal_data_contract" in Path(path).name:
            contract_doc_text = res.clean_text
        inputs_meta.append({
            "document_id": doc_id,
            "source_path": res.document.source_path,
            "document_type": res.document.document_type,
            "hash": res.document.hash,
            "had_mojibake": res.had_mojibake,
        })

        for seg in segment_document(res.document, res.clean_text, store):
            text = store.get(seg.text_ref)
            authority, conf = propose_authority(seg, text)
            rec = Governed(
                document=res.document,
                segment=seg,
                text=text,
                role=propose_role(seg, text),
                authority=authority,
                authority_confidence=conf,
                temporal=propose_temporal(seg, text),
                provenance=appraise_provenance(seg, source_path=res.document.source_path),
                secret_findings=scan_secrets(text),
                injection_findings=scan_injection(text, seeds),
            )
            rec.governed = _govern_one(rec, requests_injection=True)
            if rec.injectable:
                rec.governed.priority_score = round(
                    score_segment(text, config.task, seg.heading_path), 4)
                rec.priority = rec.governed.priority_score
            governed.append(rec)

    disagreements = detect_conflicts(governed, mojibake_docs)

    # --- emit artifacts ----------------------------------------------------
    out = config.output_dir
    out.mkdir(parents=True, exist_ok=True)
    artifacts: dict[str, Path] = {}

    def write(name: str, text: str) -> None:
        p = out / name
        p.write_text(text, encoding="utf-8")
        artifacts[name] = p

    write("CLEAN_CONTEXT_PACK.md", build_clean_pack(
        governed, config.task, profile=config.profile,
        temporal_attention=config.temporal_attention))
    write("NON_INJECTION_REPORT.md", build_non_injection_report(governed, disagreements))
    write("CONFLICT_MAP.md", build_conflict_map(disagreements))
    write("MINIMAL_DATA_CONTRACT_DIFF.md", build_contract_diff(contract_doc_text))

    # Authority review queue: every segment a human should look at.
    review = [r for r in governed if r.governed and r.governed.gate_result in
              (GateResult.FOREGROUND_WARN, GateResult.SOFT_WARN)]
    queue_lines = [json.dumps({
        "segment_id": r.segment.segment_id,
        "document_id": r.document.document_id,
        "heading_path": r.segment.heading_path,
        "authority_proposed": r.authority.value,
        "authority_confidence": round(r.authority_confidence, 3),
        "gate_result": r.governed.gate_result.value,
        "notes": r.governed.notes,
    }, ensure_ascii=False) for r in review]
    write("AUTHORITY_REVIEW_QUEUE.jsonl", "\n".join(queue_lines) + ("\n" if queue_lines else ""))

    # Override / outcome logs start empty for a fresh, unattended run.
    write("OVERRIDE_LOG.jsonl", "")
    write("DOWNSTREAM_OUTCOME_LOG.jsonl", "")

    write("CONTEXT_MANIFEST.json", build_manifest(
        inputs_meta, governed, disagreements, DETECTOR_NAMES,
        artifacts=sorted(artifacts.keys()) + ["CONTEXT_MANIFEST.json"],
        task=config.task, profile=config.profile,
        temporal_attention=config.temporal_attention))

    injectable = sum(1 for r in governed if r.injectable)
    summary = (
        f"{len(governed)} segments from {len(inputs_meta)} documents · "
        f"{injectable} injectable · {len(review)} for review · "
        f"{len(disagreements)} disagreements"
    )
    return GovernanceRun(config=config, artifacts=artifacts, governed=governed,
                         disagreements=disagreements, summary=summary)
