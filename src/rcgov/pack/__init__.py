# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""Pack construction — Clean Context Pack, Non-Injection Report, and the
dogfooding artifacts CONFLICT_MAP / MINIMAL_DATA_CONTRACT_DIFF / manifest
(spec §8, §12; contract §11).

The default pack sections and report sections are fixed by the spec. The
experimental temporal-attention placement (durable -> front, current ->
attention tail) is an opt-in profile that MUST be evaluated against a
non-temporal attention-optimal baseline before any product claim
(paper §3.4 / §10.4); when enabled it only reorders within the constraint band.
"""
from __future__ import annotations

import json

from ..contract import (
    AuthorityState,
    Disagreement,
    GateResult,
    InjectionDecision,
    SegmentRole,
)
from ..contract import enums as _enums
from ..records import Governed

__all__ = [
    "CLEAN_PACK_SECTIONS",
    "NON_INJECTION_SECTIONS",
    "PROFILES",
    "build_clean_pack",
    "build_non_injection_report",
    "build_conflict_map",
    "build_contract_diff",
    "build_manifest",
]

CLEAN_PACK_SECTIONS = (
    "Current Task",
    "Non-Negotiable Constraints",
    "Active Canonical / Committed Context",
    "Working Context",
    "Relevant Evidence",
    "User Preferences",
    "Open Questions",
    "Review Notes",
)

NON_INJECTION_SECTIONS = (
    "Quarantined Secrets and Risk Items",
    "Prompt-Injection Residue",
    "Deprecated or Unauthorized Context",
    "Authority Disagreements",
    "Severe Conflicts Requiring Review",
    "Background Material Not Injected",
)

PROFILES = ("Conservative", "Balanced", "Aggressive", "Research")

_ALL_ENUMS = (
    _enums.AuthorityState, _enums.TemporalStratum, _enums.SegmentRole,
    _enums.InjectionDecision, _enums.GateResult, _enums.OverrideReason,
    _enums.DownstreamOutcomeType,
)


def _section_for(rec: Governed) -> str:
    """Map an injectable segment to its clean-pack section."""
    if rec.role == SegmentRole.CONSTRAINT:
        return "Non-Negotiable Constraints"
    if rec.authority == AuthorityState.CANONICAL:
        return "Active Canonical / Committed Context"
    if rec.role == SegmentRole.PREFERENCE:
        return "User Preferences"
    if rec.role == SegmentRole.HYPOTHESIS:
        return "Open Questions"
    if rec.role in (SegmentRole.EVIDENCE, SegmentRole.FACT):
        return "Relevant Evidence"
    return "Working Context"


def build_clean_pack(
    governed: list[Governed],
    task: str,
    *,
    profile: str = "Balanced",
    temporal_attention: bool = False,
) -> str:
    """Render admitted, injectable segments into CLEAN_CONTEXT_PACK.md."""
    buckets: dict[str, list[Governed]] = {s: [] for s in CLEAN_PACK_SECTIONS}
    for rec in governed:
        if rec.injectable:
            buckets[_section_for(rec)].append(rec)

    lines: list[str] = ["# Clean Context Pack", ""]
    lines.append(f"<!-- profile={profile} temporal_attention={temporal_attention} -->")
    lines.append("")

    for section in CLEAN_PACK_SECTIONS:
        lines.append(f"## {section}")
        if section == "Current Task":
            lines.append("")
            lines.append(task.strip() or "_(no task described)_")
            lines.append("")
            continue
        recs = buckets[section]
        # Highest priority first; temporal-attention nudges durable to the top.
        recs.sort(key=lambda r: (r.priority or 0.0), reverse=True)
        if temporal_attention:
            from ..contract import TemporalStratum

            recs.sort(key=lambda r: r.temporal != TemporalStratum.DURABLE)
        if not recs:
            lines.append("")
            lines.append("_(none)_")
            lines.append("")
            continue
        lines.append("")
        for r in recs:
            crumb = " › ".join(r.segment.heading_path) or "(preamble)"
            lines.append(f"### {crumb}")
            lines.append(
                f"<!-- {r.document.document_id} · authority={r.authority.value} · "
                f"temporal={r.temporal.value} · priority={r.priority:.3f} -->"
            )
            lines.append(r.text.strip())
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_non_injection_report(
    governed: list[Governed],
    disagreements: list[Disagreement],
) -> str:
    """Render quarantined / deprecated / disputed material into the report."""
    secrets = [r for r in governed if r.secret_findings]
    injections = [r for r in governed if r.injection_findings]
    deprecated = [r for r in governed
                  if r.authority == AuthorityState.DEPRECATED_OR_UNAUTHORIZED]
    auth_dis = [d for d in disagreements if d.type == "authority_state_mismatch"]
    severe = [d for d in disagreements if d.alert_route == GateResult.FOREGROUND_WARN]
    background = [
        r for r in governed
        if r.governed is not None
        and r.governed.injection_decision in (
            InjectionDecision.BACKGROUND, InjectionDecision.DIGEST,
            InjectionDecision.ARCHIVE, InjectionDecision.REQUIRES_REVIEW,
        )
        and not r.secret_findings and not r.injection_findings
    ]

    def crumb(r: Governed) -> str:
        return " › ".join(r.segment.heading_path) or "(preamble)"

    lines = ["# Non-Injection Report", ""]

    lines += ["## Quarantined Secrets and Risk Items", ""]
    if secrets:
        for r in secrets:
            kinds = ", ".join(sorted({f.kind for f in r.secret_findings}))
            lines.append(f"- `{r.segment.segment_id}` ({crumb(r)}): {kinds}")
    else:
        lines.append("_(none)_")
    lines.append("")

    lines += ["## Prompt-Injection Residue", ""]
    if injections:
        for r in injections:
            pats = ", ".join(sorted({f.pattern_id for f in r.injection_findings}))
            lines.append(f"- `{r.segment.segment_id}` ({crumb(r)}): {pats}")
    else:
        lines.append("_(none)_")
    lines.append("")

    lines += ["## Deprecated or Unauthorized Context", ""]
    if deprecated:
        for r in deprecated:
            lines.append(f"- `{r.segment.segment_id}` ({crumb(r)})")
    else:
        lines.append("_(none)_")
    lines.append("")

    lines += ["## Authority Disagreements", ""]
    if auth_dis:
        for d in auth_dis:
            lines.append(f"- `{d.disagreement_id}`: {d.summary}")
    else:
        lines.append("_(none)_")
    lines.append("")

    lines += ["## Severe Conflicts Requiring Review", ""]
    if severe:
        for d in severe:
            lines.append(f"- `{d.disagreement_id}` ({d.type}): {d.summary}")
    else:
        lines.append("_(none)_")
    lines.append("")

    lines += ["## Background Material Not Injected", ""]
    if background:
        for r in background:
            dec = r.governed.injection_decision.value
            lines.append(f"- `{r.segment.segment_id}` ({crumb(r)}): {dec}")
    else:
        lines.append("_(none)_")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_conflict_map(disagreements: list[Disagreement]) -> str:
    """Render CONFLICT_MAP.md — one row per detected disagreement."""
    lines = ["# Conflict Map", ""]
    if not disagreements:
        lines.append("_No conflicts detected by the active detectors._")
        return "\n".join(lines) + "\n"
    lines += ["| id | type | route | segments | summary |",
              "|---|---|---|---|---|"]
    for d in disagreements:
        route = d.alert_route.value if d.alert_route else "—"
        segs = ", ".join(d.segments[:4]) + ("…" if len(d.segments) > 4 else "")
        summary = d.summary.replace("|", "\\|")
        lines.append(f"| {d.disagreement_id} | {d.type} | {route} | {segs} | {summary} |")
    lines.append("")
    return "\n".join(lines) + "\n"


def build_contract_diff(contract_doc_text: str | None) -> str:
    """Render MINIMAL_DATA_CONTRACT_DIFF.md — code enums vs the contract doc."""
    lines = ["# Minimal Data Contract Diff", "",
             "Code-side enum value sets vs the canonical contract document.", ""]
    if contract_doc_text is None:
        lines.append("_Contract document was not among the inputs; diff skipped._")
        return "\n".join(lines) + "\n"
    in_sync = True
    for enum_cls in _ALL_ENUMS:
        missing = [v for v in enum_cls.values() if v not in contract_doc_text]
        status = "✅ in sync" if not missing else f"⚠️ missing in doc: {missing}"
        if missing:
            in_sync = False
        lines.append(f"- **{enum_cls.__name__}** ({len(enum_cls.values())} values): {status}")
    lines.append("")
    lines.append("**Result:** " + ("all enums in sync with the contract document."
                                    if in_sync else "drift detected — see above."))
    lines.append("")
    return "\n".join(lines) + "\n"


def build_manifest(
    inputs: list[dict],
    governed: list[Governed],
    disagreements: list[Disagreement],
    detectors_run: tuple[str, ...],
    artifacts: list[str],
    *,
    task: str,
    profile: str,
    temporal_attention: bool,
) -> str:
    """Render CONTEXT_MANIFEST.json."""
    quarantined = sum(1 for r in governed
                      if r.governed and r.governed.gate_result in
                      (GateResult.BLOCK, GateResult.QUARANTINE))
    manifest = {
        "rcgov_version": __import__("rcgov").__version__,
        "contract_version": __import__("rcgov.contract", fromlist=["CONTRACT_VERSION"]).CONTRACT_VERSION,
        "task": task,
        "profile": profile,
        "temporal_attention": temporal_attention,
        "inputs": inputs,
        "counts": {
            "documents": len({r.document.document_id for r in governed}),
            "segments": len(governed),
            "injectable": sum(1 for r in governed if r.injectable),
            "quarantined": quarantined,
            "disagreements": len(disagreements),
        },
        "detectors_run": list(detectors_run),
        "artifacts": artifacts,
    }
    return json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
