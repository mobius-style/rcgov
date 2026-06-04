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

__all__ = ["PriorityComponents", "WEIGHTS", "priority_score"]

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


# --- component scorers (stubs) --------------------------------------------
def relevance(segment_text: str, task: str) -> float:
    """ME5 cosine relevance of segment to the current task. Experimental path."""
    raise NotImplementedError("relevance: ME5 'query: ' embedding cosine")


def task_proximity(segment_text: str, task: str) -> float:
    raise NotImplementedError("task_proximity: heading/section distance to task")


def compression_integrity(segment_text: str) -> float:
    raise NotImplementedError("compression_integrity: survives summarization?")


def injection_fitness(segment_text: str) -> float:
    raise NotImplementedError("injection_fitness: clean, self-contained for a pack?")
