# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""Provenance appraisal (spec v0.4 §6.3).

Grades how traceable a segment's origin is. A weak grade forbids a segment from
becoming high-authority injected context (Provenance Minimum Gate). The grade
vocabulary is intentionally small for the MVP.

MVP heuristic (no signatures yet, so ``signed`` is unreachable):
  - ``orphan``       : no source path at all;
  - ``weak``         : has a source but no heading context (can't be located);
  - ``known_source`` : has both a source path and a heading_path.
"""
from __future__ import annotations

from ..contract import Segment

__all__ = ["PROVENANCE_GRADES", "appraise_provenance", "meets_minimum"]

# Ordered weakest -> strongest.
PROVENANCE_GRADES = ("orphan", "weak", "known_source", "signed")
_MINIMUM = "known_source"


def appraise_provenance(segment: Segment, *, source_path: str | None) -> str:
    """Return a provenance grade from PROVENANCE_GRADES."""
    if not source_path:
        return "orphan"
    if not segment.heading_path:
        return "weak"
    return "known_source"


def meets_minimum(grade: str) -> bool:
    """Whether ``grade`` clears the provenance minimum for injectable authority."""
    return PROVENANCE_GRADES.index(grade) >= PROVENANCE_GRADES.index(_MINIMUM)
