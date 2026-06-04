# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""Pack construction — Clean Context Pack + Non-Injection Report (spec §8, §12).

STATUS: stub. The default pack sections and the non-injection report sections
are fixed by the spec and provided here as templates. The experimental
temporal-attention placement (durable -> front, current -> attention tail) is an
opt-in profile that MUST be evaluated against a non-temporal attention-optimal
baseline before any product claim (paper §3.4 / §10.4).
"""
from __future__ import annotations

from ..contract import GovernedSegment

__all__ = [
    "CLEAN_PACK_SECTIONS",
    "NON_INJECTION_SECTIONS",
    "PROFILES",
    "build_clean_pack",
    "build_non_injection_report",
]

# spec §8.1
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

# spec §8.2
NON_INJECTION_SECTIONS = (
    "Quarantined Secrets and Risk Items",
    "Prompt-Injection Residue",
    "Deprecated or Unauthorized Context",
    "Authority Disagreements",
    "Severe Conflicts Requiring Review",
    "Background Material Not Injected",
)

# spec §14.3
PROFILES = ("Conservative", "Balanced", "Aggressive", "Research")


def build_clean_pack(
    segments: list[GovernedSegment],
    task: str,
    *,
    profile: str = "Balanced",
    temporal_attention: bool = False,
) -> str:
    """Render admitted, injectable segments into CLEAN_CONTEXT_PACK.md."""
    raise NotImplementedError(
        "build_clean_pack: place injectable segments into CLEAN_PACK_SECTIONS; "
        "temporal_attention is the experimental opt-in profile (spec §8.3)."
    )


def build_non_injection_report(segments: list[GovernedSegment]) -> str:
    """Render quarantined / deprecated / disputed material into the report."""
    raise NotImplementedError(
        "build_non_injection_report: group non-injected segments by "
        "NON_INJECTION_SECTIONS (spec §8.2)."
    )
