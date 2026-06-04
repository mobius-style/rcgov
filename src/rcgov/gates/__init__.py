# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""Non-compensatory gate layer (paper v0.7 §3.1 / §5.2, spec v0.4 §6).

Gates run **before** priority scoring. High relevance can never compensate for a
secret, an unsafe instruction, missing provenance, or uncommitted authority.

The gates here that are fully determined by the contract are implemented for
real (Safety, Prompt-Injection, Authority-Commitment, Provenance-Minimum). The
Severe-Conflict gate depends on disagreement detection and is left as a stub
input (``has_severe_conflict``) supplied by the caller.

``run_gates`` is a pure reducer: it folds the strongest applicable verdict and
the matching injection decision, returning the worst-case (most restrictive)
outcome. Restrictiveness order, weakest -> strongest:

    pass < soft_warn < foreground_warn < block < quarantine
"""
from __future__ import annotations

from dataclasses import dataclass

from ..contract import (
    AuthorityState,
    GateResult,
    HIGH_AUTHORITY_STATES,
    InjectionDecision,
)

__all__ = ["GateInputs", "GateOutcome", "run_gates", "RESTRICTIVENESS"]

# Strict restrictiveness ordering used to fold multiple gate verdicts.
RESTRICTIVENESS = {
    GateResult.PASS: 0,
    GateResult.SOFT_WARN: 1,
    GateResult.FOREGROUND_WARN: 2,
    GateResult.BLOCK: 3,
    GateResult.QUARANTINE: 4,
}


@dataclass(frozen=True)
class GateInputs:
    """Everything the gate layer needs about one segment."""

    has_secret: bool
    has_injection: bool
    provenance_meets_minimum: bool
    requests_injection: bool  # caller asked for inject/must_obey
    authority_proposed: AuthorityState
    authority_committed: AuthorityState | None
    has_severe_conflict: bool = False  # supplied by disagreement detection (stub)


@dataclass(frozen=True)
class GateOutcome:
    gate_result: GateResult
    injection_decision: InjectionDecision
    notes: tuple[str, ...]


def _worse(a: GateResult, b: GateResult) -> GateResult:
    return a if RESTRICTIVENESS[a] >= RESTRICTIVENESS[b] else b


def run_gates(inp: GateInputs) -> GateOutcome:
    """Fold all gate verdicts into the single most-restrictive outcome."""
    verdict = GateResult.PASS
    decision = InjectionDecision.INJECT
    notes: list[str] = []

    # 1. Safety Gate — secrets / unsafe material are quarantined outright.
    if inp.has_secret:
        verdict = _worse(verdict, GateResult.QUARANTINE)
        decision = InjectionDecision.QUARANTINE
        notes.append("safety: secret or risk material detected")

    # 2. Prompt-Injection Gate — embedded override instructions are quarantined.
    if inp.has_injection:
        verdict = _worse(verdict, GateResult.QUARANTINE)
        decision = InjectionDecision.QUARANTINE
        notes.append("prompt_injection: source instruction quarantined")

    # 3. Provenance Minimum Gate — weak provenance cannot become injected
    #    high-authority context (spec §6.3).
    if inp.requests_injection and not inp.provenance_meets_minimum:
        verdict = _worse(verdict, GateResult.FOREGROUND_WARN)
        if decision == InjectionDecision.INJECT:
            decision = InjectionDecision.REQUIRES_REVIEW
        notes.append("provenance: below minimum for injectable authority")

    # 4. Authority Commitment Gate — proposed-canonical with no commitment must
    #    be foregrounded for review (spec §6.4).
    if (
        inp.authority_proposed in HIGH_AUTHORITY_STATES
        and inp.authority_committed is None
    ):
        verdict = _worse(verdict, GateResult.FOREGROUND_WARN)
        if decision == InjectionDecision.INJECT:
            decision = InjectionDecision.REQUIRES_REVIEW
        notes.append("authority: proposed canonical without committed authority")

    # 5. Severe Conflict Gate — high-impact conflicts stay foregrounded even
    #    under high disagreement fatigue (spec §6.5). Detection is upstream.
    if inp.has_severe_conflict:
        verdict = _worse(verdict, GateResult.FOREGROUND_WARN)
        if decision == InjectionDecision.INJECT:
            decision = InjectionDecision.REQUIRES_REVIEW
        notes.append("conflict: severe unresolved conflict affecting task")

    return GateOutcome(gate_result=verdict, injection_decision=decision,
                       notes=tuple(notes))
