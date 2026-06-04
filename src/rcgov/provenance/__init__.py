# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""Provenance appraisal (spec v0.4 §6.3).

STATUS: stub. Grades how traceable a segment's origin is. A weak grade forbids a
segment from becoming high-authority injected context (Provenance Minimum Gate).
The grade vocabulary is intentionally small for the MVP.
"""
from __future__ import annotations

from ..contract import Segment

__all__ = ["PROVENANCE_GRADES", "appraise_provenance", "meets_minimum"]

# Ordered weakest -> strongest.
PROVENANCE_GRADES = ("orphan", "weak", "known_source", "signed")
_MINIMUM = "known_source"


def appraise_provenance(segment: Segment) -> str:
    """Return a provenance grade from PROVENANCE_GRADES. TODO: real appraisal
    from source_path trust, heading_path completeness, and hash continuity."""
    raise NotImplementedError("appraise_provenance: see spec §6.3")


def meets_minimum(grade: str) -> bool:
    """Whether ``grade`` clears the provenance minimum for injectable authority."""
    return PROVENANCE_GRADES.index(grade) >= PROVENANCE_GRADES.index(_MINIMUM)
