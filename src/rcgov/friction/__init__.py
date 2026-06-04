# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""Friction governance — DFI / ORS / elastic alert routing (paper §7, spec §10).

Per Decision Record 4, ORS is **not learned** in the MVP: it is a conservative
prior plus logging until enough downstream-outcome samples exist (``N_min = 5``).

Design principle (spec §10.1-§10.2):
    Disagreement visibility must itself be governed.
    Friction may be reduced only when downstream risk remains bounded.

Hard gates always win: ElasticRisk never relaxes a block/quarantine.
"""
from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "N_MIN",
    "ElasticWeights",
    "conservative_prior",
    "ors_cold_start",
    "elastic_risk",
    "route_alert",
]

N_MIN = 5  # contract §10.2 default

# Conservative priors by disagreement type. Unknown types fall back to a high
# default so an unseen, untyped disagreement is never quietly suppressed.
_PRIORS: dict[str, float] = {
    "api_version_conflict": 0.55,
    "license_conflict": 0.70,
    "hard_constraint_conflict": 0.80,
    "destructive_direction": 0.90,
    "stale_security_instruction": 0.85,
    "authority_uncommitted": 0.50,
}
_DEFAULT_PRIOR = 0.65  # unknown type: lean cautious


@dataclass(frozen=True)
class ElasticWeights:
    """Coefficients for the ElasticRisk combination (spec §10.6)."""

    alpha: float = 1.0  # ORS
    beta: float = 0.5   # impact scope
    gamma: float = 0.7  # irreversibility
    delta: float = 0.3  # DFI (reduces alerting when the user is fatigued)


def conservative_prior(disagreement_type: str, base_severity: float = 0.0) -> float:
    """Prior ORS for a type with too few samples. Blends a type prior with the
    observed base_severity, biased toward caution (the higher of the two)."""
    prior = _PRIORS.get(disagreement_type, _DEFAULT_PRIOR)
    return max(prior, base_severity)


def ors_cold_start(
    disagreement_type: str,
    sample_count: int,
    observed_failure_rate: float | None,
    base_severity: float = 0.0,
) -> float:
    """Cold-start ORS rule (spec §10.5): use the conservative prior until
    ``sample_count >= N_MIN``, then trust the observed failure rate."""
    if sample_count < N_MIN or observed_failure_rate is None:
        return conservative_prior(disagreement_type, base_severity)
    return observed_failure_rate


def elastic_risk(
    ors: float,
    impact_scope: float,
    irreversibility_risk: float,
    dfi: float,
    weights: ElasticWeights | None = None,
) -> float:
    """ElasticRisk(d_i) (spec §10.6). DFI lowers the score (quieter when tired),
    but routing keeps hard gates above this calculation."""
    w = weights or ElasticWeights()
    return (
        w.alpha * ors
        + w.beta * impact_scope
        + w.gamma * irreversibility_risk
        - w.delta * dfi
    )


def route_alert(
    risk: float,
    *,
    is_hard_gate: bool,
    foreground_threshold: float = 0.6,
    digest_threshold: float = 0.3,
) -> str:
    """Route a disagreement to an alert channel (spec §10.6).

    Returns one of: ``block_or_require_explicit_override``, ``foreground_alert``,
    ``include_in_digest``, ``background_log``.
    """
    if is_hard_gate:
        return "block_or_require_explicit_override"
    if risk >= foreground_threshold:
        return "foreground_alert"
    if risk >= digest_threshold:
        return "include_in_digest"
    return "background_log"
