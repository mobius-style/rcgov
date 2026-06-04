# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""Conflict / drift detection (contract §12 conflict types, paper §9 dogfooding).

Produces ``Disagreement`` objects and routes each through friction governance to
set an ``alert_route``. Implemented detectors (the genuinely doable subset):

  - encoding_mojibake     : a source file carried mojibake at ingest time;
  - section_numbering_drift: duplicate / skipped top-level section numbers;
  - schema_field_mismatch : the Segment object is described with both the
                            inline ``text`` form and the ``text_ref`` form
                            across the corpus (the exact drift Decision Record
                            3a resolved);
  - authority_state_mismatch / temporal_stratum_mismatch : segments sharing a
                            normalized heading title across documents that were
                            assigned different proposed authority / temporal.

Anything not yet detectable is left out rather than faked; the count of detectors
run is reported in the manifest so coverage is never silently overstated.
"""
from __future__ import annotations

import re
from collections import defaultdict

from .contract import Disagreement, GateResult
from .friction import elastic_risk, conservative_prior, route_alert
from .records import Governed

__all__ = ["detect_conflicts", "DETECTOR_NAMES"]

DETECTOR_NAMES = (
    "encoding_mojibake",
    "section_numbering_drift",
    "schema_field_mismatch",
    "authority_state_mismatch",
    "temporal_stratum_mismatch",
)

# Top-level sections only ("# 7. ..."). Matching ``##`` subsections would
# collapse "3", "3.1", "3.2" all to "3" and report spurious duplicates.
_SECTION_NUM = re.compile(r"^#\s+(\d+)\.")
_ROUTE_BY_SCORE = {  # impact_scope label -> numeric, for ElasticRisk
    "low": 0.3, "medium": 0.6, "high": 0.9,
}


def _normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", title.lower()).strip()


def _route(d: Disagreement) -> GateResult:
    """Assign an alert route to a disagreement via friction governance."""
    ors = conservative_prior(d.type, d.base_severity)
    risk = elastic_risk(
        ors=ors,
        impact_scope=_ROUTE_BY_SCORE.get(d.impact_scope, 0.6),
        irreversibility_risk=d.irreversibility_risk,
        dfi=0.0,  # cold start: no fatigue signal yet
    )
    routed = route_alert(risk, is_hard_gate=False)
    return (
        GateResult.FOREGROUND_WARN
        if routed == "foreground_alert"
        else GateResult.SOFT_WARN
    )


def _mk(did: str, dtype: str, segs: list[str], summary: str,
        *, base_severity: float, impact: str, irrev: float) -> Disagreement:
    d = Disagreement(
        disagreement_id=did, type=dtype, segments=segs, summary=summary,
        base_severity=base_severity, impact_scope=impact, irreversibility_risk=irrev,
    )
    d.alert_route = _route(d)
    return d


def detect_conflicts(
    records: list[Governed],
    mojibake_docs: dict[str, str],  # document_id -> source_path that was dirty
) -> list[Disagreement]:
    """Run all detectors and return routed Disagreements."""
    out: list[Disagreement] = []
    n = 0

    # 1. encoding_mojibake
    for doc_id, src in sorted(mojibake_docs.items()):
        n += 1
        out.append(_mk(
            f"dis_{n:03d}", "encoding_mojibake", [doc_id],
            f"Source file '{src}' carried mojibake at ingest; repaired on entry.",
            base_severity=0.3, impact="low", irrev=0.05,
        ))

    # 2. section_numbering_drift (per document)
    by_doc: dict[str, list[Governed]] = defaultdict(list)
    for r in records:
        by_doc[r.document.document_id].append(r)
    for doc_id, recs in sorted(by_doc.items()):
        nums: list[int] = []
        for r in recs:
            m = _SECTION_NUM.match(r.text.lstrip().splitlines()[0] if r.text.strip() else "")
            if m:
                nums.append(int(m.group(1)))
        dups = sorted({x for x in nums if nums.count(x) > 1})
        gaps = [a for a, b in zip(nums, nums[1:]) if b not in (a, a + 1) and b > a + 1]
        if dups or gaps:
            n += 1
            out.append(_mk(
                f"dis_{n:03d}", "section_numbering_drift", [doc_id],
                f"'{doc_id}' section numbering anomaly: "
                f"duplicates={dups or 'none'}, gaps_after={gaps or 'none'}.",
                base_severity=0.25, impact="low", irrev=0.05,
            ))

    # 3. schema_field_mismatch — Segment described both inline and by-reference.
    inline_text = [r for r in records if '"segment_id"' in r.text and '"text"' in r.text
                   and '"text_ref"' not in r.text]
    by_ref = [r for r in records if '"segment_id"' in r.text and '"text_ref"' in r.text]
    if inline_text and by_ref:
        n += 1
        out.append(_mk(
            f"dis_{n:03d}", "schema_field_mismatch",
            [r.segment.segment_id for r in (inline_text + by_ref)][:6],
            "Segment object defined with both inline 'text' and 'text_ref' forms "
            "across the corpus (contract drift; see Decision Record 3a).",
            base_severity=0.7, impact="high", irrev=0.4,
        ))

    # 4/5. authority / temporal mismatch across documents on the same heading.
    groups: dict[str, list[Governed]] = defaultdict(list)
    for r in records:
        if r.segment.heading_path:
            groups[_normalize_title(r.title)].append(r)
    for title, recs in sorted(groups.items()):
        docs = {r.document.document_id for r in recs}
        if len(docs) < 2 or not title:
            continue
        auths = {r.authority for r in recs}
        temps = {r.temporal for r in recs}
        if len(auths) > 1:
            n += 1
            out.append(_mk(
                f"dis_{n:03d}", "authority_state_mismatch",
                [r.segment.segment_id for r in recs],
                f"Heading '{title}' proposed different authority across documents: "
                f"{sorted(a.value for a in auths)}.",
                base_severity=0.5, impact="medium", irrev=0.2,
            ))
        if len(temps) > 1:
            n += 1
            out.append(_mk(
                f"dis_{n:03d}", "temporal_stratum_mismatch",
                [r.segment.segment_id for r in recs],
                f"Heading '{title}' proposed different temporal strata across "
                f"documents: {sorted(t.value for t in temps)}.",
                base_severity=0.4, impact="medium", irrev=0.15,
            ))

    return out
