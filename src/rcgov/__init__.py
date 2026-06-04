# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""RCGov — Mobius Reflective Context Governor.

Local-first semantic hygiene and context governance for LLM systems. Governs
context intake before a model is allowed to read it.

Robust core first; the Annales-derived temporal-attention placement is an opt-in
experimental profile, not a core claim. See ``docs/spec_v0_4.md``.
"""
from __future__ import annotations

__version__ = "0.1.0"

# The axiom this whole package serves (paper v0.7 §1):
#     InjectContext_t => ContextReady_t
READINESS_AXIOM = "InjectContext_t => ContextReady_t"

__all__ = ["__version__", "READINESS_AXIOM"]
