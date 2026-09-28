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
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from .contract import OUTPUT_FILES
from .pipeline import RunConfig, run

__all__ = ["GovernResult", "govern_bytes", "ARTIFACT_ORDER",
           "RebuildResult", "rebuild_bytes", "RETAIN_KINDS", "EXCLUDED_PLACEHOLDER"]

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

    The ``CLEAN_CONTEXT_PACK.md`` artifact is a **triage** of the input by
    authority and priority — what the pipeline judged placeable for ``task`` —
    **not a scrubbed copy of what you passed in**. Without commitments, a
    segment of plain prose with no provenance is typically routed to
    ``requires_review`` and does not appear in the pack at all, and nothing in
    the pack tells you it is missing. Callers who want "the same text minus
    what the scanner flagged" must use :func:`rebuild_bytes`. Three downstream
    products handed a model this pack as if it were the governed text; see the
    README incident report (2026-09-20).
    """
    root, paths = _materialize(inputs, workdir)

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


def _materialize(inputs: list[tuple[str, bytes]], workdir: str | Path | None) -> tuple[Path, list[str]]:
    root = Path(workdir) if workdir is not None else Path(tempfile.mkdtemp(prefix="rcgov_"))
    in_dir = root / "inputs"
    in_dir.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    for name, data in inputs:
        safe = Path(name).name or "upload"
        p = in_dir / safe
        p.write_bytes(data)
        paths.append(str(p))
    return root, paths


# Secret kinds that are heuristic signals rather than confirmed secrets. They
# are kept in the rebuilt text and listed, never excised: ``high_entropy_token``
# fires on ids, hashes and paths, and excising it deletes most of any real
# document (measured on 347 session records, 2026-09-19: 1,508 flags, 0
# confirmed secrets).
RETAIN_KINDS: frozenset[str] = frozenset({"high_entropy_token"})
EXCLUDED_PLACEHOLDER = "_[segment excluded by RCGov — see excluded]_\n"
REDACTED_HEADING = "[heading withheld by RCGov]"
_HEADING_RE = re.compile(r"^#{1,6}\s+\S")


def _line_is_flagged(line: str, cache: dict[str, bool] | None = None) -> bool:
    """True when a single line carries any secret finding or a built-in
    injection pattern. A segment's first line is kept as its heading when the
    segment is excised — but ``# AWS_SECRET_ACCESS_KEY=...`` in a .env file, a
    commented key in a code fence, or a heading that quotes a key is also a
    "heading". Until 0.2.1 such a line was copied through verbatim and
    repeated in ``excluded[].heading``.

    Headings are metadata, so the rule is strict: any finding at all,
    including the kinds that are kept in body text, counts. ``cache`` lives
    for one ``rebuild_bytes`` call: a heading is looked at once per descendant
    segment, and a long parent heading over many children made the rebuild ten
    times slower."""
    from .scan import scan_injection, scan_secrets
    if cache is not None and line in cache:
        return cache[line]
    flagged = bool(scan_secrets(line)) or bool(scan_injection(line))
    if cache is not None:
        cache[line] = flagged
    return flagged


def _first_line_is_flagged(rec, cache: dict[str, bool]) -> bool:
    """The record's own findings decide first: they come from the run's
    configured patterns (the injection seeds file), which a re-scan of the
    line does not know. The line scan is the second opinion."""
    first = rec.text.splitlines()[0] if rec.text else ""
    for f in list(rec.secret_findings or []) + list(rec.injection_findings or []):
        if f.start <= len(first):
            return True
    return _line_is_flagged(first, cache)


def _safe_heading_path(path, withheld: set[str], cache: dict[str, bool]) -> str:
    return " / ".join(
        REDACTED_HEADING if (str(h) in withheld or _line_is_flagged(str(h), cache))
        else str(h)
        for h in (path or ())
    )


def _withheld_titles(records, cache: dict[str, bool]) -> set[str]:
    """Titles whose own heading line is flagged. The title is the line with its
    markers stripped, and the stripped form can fall under a pattern's minimum
    length while the raw line does not — so the raw line decides."""
    out: set[str] = set()
    for rec in records:
        path = rec.segment.heading_path
        if not path or not rec.text:
            continue
        first = rec.text.splitlines()[0]
        if _HEADING_RE.match(first) and _first_line_is_flagged(rec, cache):
            out.add(str(path[-1]))
    return out


@dataclass
class RebuildResult:
    """Each input rebuilt segment by segment from the governance records."""

    text: dict[str, str]                 # input name -> rebuilt text
    excluded: list[dict] = field(default_factory=list)   # {input, segment, heading, reason}
    retained: list[dict] = field(default_factory=list)   # heuristic-only flags, kept
    admitted: int = 0
    segments: int = 0
    summary: str = ""
    manifest: dict = field(default_factory=dict)
    workdir: Path | None = None

    def joined(self, sep: str = "\n\n") -> str:
        return sep.join(self.text[k] for k in self.text)


def _hard_gated(rec) -> bool:
    """A block or quarantine gate — the two results the pack itself refuses to place."""
    gr = rec.governed.gate_result if rec.governed is not None else None
    return str(getattr(gr, "value", gr)) in ("block", "quarantine")


def _classify(rec, retain_kinds: frozenset[str]) -> tuple[str, str]:
    """``exclude`` | ``retain`` | ``keep``, decided from structured findings only."""
    secret_kinds = list(dict.fromkeys(f.kind for f in (rec.secret_findings or [])))
    injection = list(dict.fromkeys(f.pattern_id for f in (rec.injection_findings or [])))
    confirmed = [k for k in secret_kinds if k not in retain_kinds]
    if confirmed or injection:
        return "exclude", ", ".join(confirmed + injection)
    if secret_kinds:
        return "retain", ", ".join(secret_kinds)
    if _hard_gated(rec):
        notes = rec.governed.notes
        reason = ("; ".join(map(str, notes)) if isinstance(notes, (list, tuple)) else str(notes)) if notes else "quarantined"
        return "exclude", reason
    return "keep", ""


def rebuild_bytes(
    inputs: list[tuple[str, bytes]],
    task: str,
    *,
    profile: str = "Balanced",
    retain_kinds: frozenset[str] = RETAIN_KINDS,
    placeholder: str = EXCLUDED_PLACEHOLDER,
    workdir: str | Path | None = None,
) -> RebuildResult:
    """Return every input **rebuilt segment by segment** from the governance run.

    This is the call for "let the model read this text, minus what the scanner
    flagged". Kept segments are copied byte-for-byte from the input; segments
    with a confirmed secret kind, an injection pattern, or a quarantine gate are
    replaced by ``placeholder`` (a leading heading line is preserved unless the
    heading line itself is flagged) and listed
    in ``excluded`` with their reason; heuristic-only kinds in ``retain_kinds``
    are kept and listed in ``retained``. Every span is verified against the
    record's own text before it is trusted; a mismatch, or a manifest that
    disagrees with the records, raises rather than guesses. Nothing leaves
    silently — which is the property :func:`govern_bytes`' Clean Context Pack
    does not offer (it is a triage, and omits without a trace).
    """
    root, paths = _materialize(inputs, workdir)
    cfg = RunConfig(task=task, profile=profile, output_dir=root / "out",
                    store_dir=root / "store", commitments_path=None)
    result = run(paths, cfg)
    records = list(result.governed or [])
    manifest_path = cfg.output_dir / "CONTEXT_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    counts = manifest.get("counts") or {}
    if counts.get("segments") != len(records):
        raise RuntimeError(f"manifest reports {counts.get('segments')} segments, records carry {len(records)}")

    by_doc: dict[str, list] = {}
    for r in records:
        by_doc.setdefault(r.segment.document_id, []).append(r)
    out = RebuildResult(text={}, summary=(result.summary or "").strip(), manifest=manifest,
                        workdir=root, segments=len(records))
    for entry in manifest.get("inputs") or []:
        src = Path(entry["source_path"])
        name = src.name
        doc = src.read_text(encoding="utf-8")
        recs = sorted(by_doc.get(entry["document_id"], []), key=lambda r: r.segment.source_span.start)
        pieces, cursor, n = [], 0, len(doc)
        cache: dict[str, bool] = {}
        withheld = _withheld_titles(recs, cache)
        for rec in recs:
            sp = rec.segment.source_span
            s, e = sp.start, sp.end
            if not (0 <= cursor <= s <= e <= n) or doc[s:e] != rec.text:
                raise RuntimeError(f"span verification failed for {rec.segment.segment_id} [{s}:{e}] of {n}")
            klass, reason = _classify(rec, retain_kinds)
            item = {"input": name, "segment": rec.segment.segment_id,
                    "heading": _safe_heading_path(rec.segment.heading_path, withheld, cache),
                    "reason": reason}
            pieces.append(doc[cursor:s])
            if klass == "exclude":
                first = rec.text.splitlines()[0] if rec.text else ""
                keep_heading = bool(_HEADING_RE.match(first)) and not _first_line_is_flagged(rec, cache)
                pieces.append((first + "\n\n" + placeholder) if keep_heading else placeholder)
                out.excluded.append(item)
            else:
                pieces.append(doc[s:e]); out.admitted += 1
                if klass == "retain":
                    out.retained.append(item)
            cursor = e
        pieces.append(doc[cursor:])
        out.text[name] = "".join(pieces)
    return out
