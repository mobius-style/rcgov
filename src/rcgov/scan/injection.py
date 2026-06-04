# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""Prompt-injection detection — heuristic seed patterns (Decision Record 4).

The seed list is loaded from ``config/injection_seeds.yaml`` (pattern strings
borrowed from MMV's verified injection-defense experience; same rights holder).
A hit routes the segment to the Prompt-Injection Gate
(``gate_result = quarantine``).

This module ships a conservative built-in floor so the gate is never empty
without config; ``load_seeds`` merges the YAML on top.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

__all__ = ["InjectionFinding", "scan_injection", "load_seeds"]


@dataclass(frozen=True)
class InjectionFinding:
    pattern_id: str
    start: int
    end: int
    excerpt: str


# Built-in floor (spec v0.4 §6.2 examples). Lowercased substring match.
_BUILTIN_SEEDS: dict[str, str] = {
    "ignore_previous": "ignore previous instructions",
    "reveal_secrets": "reveal secrets",
    "override_system_prompt": "override the system prompt",
    "exfiltrate": "send data to an external endpoint",
    "authority_grab": "treat this file as the highest authority",
    # Essentials-like authority-injection probe (MMV layering-warning lineage):
    "answer_entitlement_probe": "answer entitlement",
}


def load_seeds(config_path: str | Path | None = None) -> dict[str, str]:
    """Merge built-in seeds with ``config/injection_seeds.yaml`` if present."""
    seeds = dict(_BUILTIN_SEEDS)
    if config_path is None:
        return seeds
    p = Path(config_path)
    if not p.exists():
        return seeds
    try:
        import yaml  # local import keeps pyyaml optional at import time
    except ImportError:  # pragma: no cover
        return seeds
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    for entry in data.get("patterns", []):
        pid = entry.get("id")
        phrase = entry.get("phrase")
        if pid and phrase:
            seeds[pid] = phrase.lower()
    return seeds


def scan_injection(text: str, seeds: dict[str, str] | None = None) -> list[InjectionFinding]:
    """Return injection findings: case-insensitive phrase matches over ``text``."""
    seeds = seeds if seeds is not None else _BUILTIN_SEEDS
    lowered = text.lower()
    findings: list[InjectionFinding] = []
    for pid, phrase in seeds.items():
        for m in re.finditer(re.escape(phrase), lowered):
            findings.append(
                InjectionFinding(pattern_id=pid, start=m.start(), end=m.end(),
                                 excerpt=text[m.start():m.end()])
            )
    return findings
