# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""Priority scoring for *admitted* segments (paper §5.3, spec §7, contract §9).

The combine formula is fully implemented (it is fixed by the contract). The four
component scorers are stubs — ``relevance`` and ``task_proximity`` are the
experimental ME5 path (Decision Record 4), ``compression_integrity`` and
``injection_fitness`` are heuristic.

CRITICAL: scoring applies ONLY to admitted segments. Safety, authority, severe
conflict, and provenance are gates/limiters and are NOT factors here.
"""
from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "PriorityComponents", "WEIGHTS", "priority_score", "score_segment",
    "relevance", "task_proximity", "compression_integrity", "injection_fitness",
]

# Contract-fixed weights (contract §9). Sum = 1.0.
WEIGHTS = {
    "relevance": 0.45,
    "task_proximity": 0.25,
    "compression_integrity": 0.15,
    "injection_fitness": 0.15,
}


@dataclass(frozen=True)
class PriorityComponents:
    """The four component scores, each expected in [0, 1]."""

    relevance: float
    task_proximity: float
    compression_integrity: float
    injection_fitness: float

    def __post_init__(self) -> None:
        for name in WEIGHTS:
            v = getattr(self, name)
            if not (0.0 <= v <= 1.0):
                raise ValueError(f"priority component {name}={v} outside [0, 1]")


def priority_score(c: PriorityComponents) -> float:
    """Weighted combination — the contract formula, exactly."""
    return (
        WEIGHTS["relevance"] * c.relevance
        + WEIGHTS["task_proximity"] * c.task_proximity
        + WEIGHTS["compression_integrity"] * c.compression_integrity
        + WEIGHTS["injection_fitness"] * c.injection_fitness
    )


# --- component scorers ------------------------------------------------------
# Model-independent lexical implementations (Decision Record 4). The ME5
# embedding path is an experimental *upgrade* of ``relevance`` / ``task_proximity``,
# enabled via the ``embed`` extra; the robust core runs without it.

def relevance(segment_text: str, task: str) -> float:
    """Relevance of a segment to the current task — lexical TF cosine.

    Upgrade path: replace with ME5 'query: ' embedding cosine (``embed`` extra).
    """
    from ..textutils import cosine

    return cosine(segment_text, task) if task.strip() else 0.5


def task_proximity(segment_text: str, task: str, heading_path: list[str] | None = None) -> float:
    """How close the segment's heading context sits to the task vocabulary."""
    from ..textutils import jaccard

    heading = " ".join(heading_path or [])
    if not task.strip():
        return 0.5
    return jaccard(heading or segment_text, task)


def compression_integrity(segment_text: str) -> float:
    """Heuristic: mid-length, prose-heavy segments survive summarization best.

    Very short fragments and very long dumps both score lower.
    """
    n = len(segment_text)
    if n < 40:
        return 0.3
    if n > 4000:
        return 0.5
    return 1.0


def injection_fitness(segment_text: str) -> float:
    """Heuristic: penalize segments dominated by code fences / tables, which are
    awkward to splice cleanly into a prose context pack."""
    lines = segment_text.splitlines() or [""]
    noisy = sum(1 for ln in lines if ln.lstrip().startswith(("```", "|", "    ")))
    return max(0.0, 1.0 - noisy / max(1, len(lines)))


def score_segment(segment_text: str, task: str, heading_path: list[str] | None = None) -> float:
    """Convenience: compute all components and combine them."""
    return priority_score(PriorityComponents(
        relevance=relevance(segment_text, task),
        task_proximity=task_proximity(segment_text, task, heading_path),
        compression_integrity=compression_integrity(segment_text),
        injection_fitness=injection_fitness(segment_text),
    ))
