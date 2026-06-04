# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""Tests for the deterministic stages: gates, priority combine, friction."""
from __future__ import annotations

import pytest

from rcgov.contract import AuthorityState, GateResult, InjectionDecision
from rcgov.gates import GateInputs, run_gates
from rcgov.priority import PriorityComponents, WEIGHTS, priority_score
from rcgov.friction import (
    N_MIN,
    conservative_prior,
    ors_cold_start,
    elastic_risk,
    route_alert,
)


# --- gates: non-compensatory folding ---------------------------------------
def test_secret_forces_quarantine_regardless_of_authority():
    out = run_gates(GateInputs(
        has_secret=True, has_injection=False, provenance_meets_minimum=True,
        requests_injection=True, authority_proposed=AuthorityState.CANONICAL,
        authority_committed=AuthorityState.CANONICAL,
    ))
    assert out.gate_result == GateResult.QUARANTINE
    assert out.injection_decision == InjectionDecision.QUARANTINE


def test_clean_committed_canonical_passes():
    out = run_gates(GateInputs(
        has_secret=False, has_injection=False, provenance_meets_minimum=True,
        requests_injection=True, authority_proposed=AuthorityState.CANONICAL,
        authority_committed=AuthorityState.CANONICAL,
    ))
    assert out.gate_result == GateResult.PASS
    assert out.injection_decision == InjectionDecision.INJECT


def test_uncommitted_canonical_foregrounded():
    out = run_gates(GateInputs(
        has_secret=False, has_injection=False, provenance_meets_minimum=True,
        requests_injection=True, authority_proposed=AuthorityState.CANONICAL,
        authority_committed=None,
    ))
    assert out.gate_result == GateResult.FOREGROUND_WARN
    assert out.injection_decision == InjectionDecision.REQUIRES_REVIEW


def test_weak_provenance_blocks_injection():
    out = run_gates(GateInputs(
        has_secret=False, has_injection=False, provenance_meets_minimum=False,
        requests_injection=True, authority_proposed=AuthorityState.WORKING,
        authority_committed=None,
    ))
    assert out.gate_result == GateResult.FOREGROUND_WARN
    assert out.injection_decision == InjectionDecision.REQUIRES_REVIEW


def test_injection_beats_everything():
    out = run_gates(GateInputs(
        has_secret=False, has_injection=True, provenance_meets_minimum=True,
        requests_injection=False, authority_proposed=AuthorityState.UNKNOWN,
        authority_committed=None,
    ))
    assert out.gate_result == GateResult.QUARANTINE


# --- priority: contract formula --------------------------------------------
def test_weights_sum_to_one():
    assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9


def test_priority_all_max_is_one():
    c = PriorityComponents(1.0, 1.0, 1.0, 1.0)
    assert abs(priority_score(c) - 1.0) < 1e-9


def test_priority_formula():
    c = PriorityComponents(relevance=0.8, task_proximity=0.6,
                           compression_integrity=0.4, injection_fitness=0.2)
    expected = 0.45 * 0.8 + 0.25 * 0.6 + 0.15 * 0.4 + 0.15 * 0.2
    assert abs(priority_score(c) - expected) < 1e-9


def test_priority_component_range_validation():
    with pytest.raises(ValueError):
        PriorityComponents(1.5, 0.0, 0.0, 0.0)


# --- friction: cold-start priors -------------------------------------------
def test_cold_start_uses_prior_below_n_min():
    ors = ors_cold_start("api_version_conflict", sample_count=N_MIN - 1,
                         observed_failure_rate=0.01)
    assert ors == conservative_prior("api_version_conflict")
    assert ors > 0.01  # the observed low rate is ignored while under-sampled


def test_uses_observed_at_or_above_n_min():
    ors = ors_cold_start("api_version_conflict", sample_count=N_MIN,
                         observed_failure_rate=0.12)
    assert ors == 0.12


def test_unknown_type_leans_cautious():
    assert conservative_prior("never_seen_type") >= 0.5


def test_dfi_lowers_risk_but_hard_gate_wins():
    high = elastic_risk(ors=0.8, impact_scope=0.5, irreversibility_risk=0.5, dfi=0.0)
    tired = elastic_risk(ors=0.8, impact_scope=0.5, irreversibility_risk=0.5, dfi=1.0)
    assert tired < high  # fatigue reduces alerting
    # ...but a hard gate ignores ElasticRisk entirely.
    assert route_alert(tired, is_hard_gate=True) == "block_or_require_explicit_override"


def test_routing_thresholds():
    assert route_alert(0.9, is_hard_gate=False) == "foreground_alert"
    assert route_alert(0.4, is_hard_gate=False) == "include_in_digest"
    assert route_alert(0.1, is_hard_gate=False) == "background_log"
