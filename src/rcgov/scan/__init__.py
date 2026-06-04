# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""Scan stage — secret and prompt-injection detection (model-independent).

Per Decision Record 4: secret = regex + Shannon entropy; prompt-injection =
heuristic seed patterns (``config/injection_seeds.yaml``). No model dependency in
the robust core.
"""
from __future__ import annotations

from .secrets import SecretFinding, scan_secrets, shannon_entropy
from .injection import InjectionFinding, scan_injection

__all__ = [
    "SecretFinding",
    "scan_secrets",
    "shannon_entropy",
    "InjectionFinding",
    "scan_injection",
]
