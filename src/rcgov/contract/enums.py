# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) MOBIUS.LLC / Taiko Toeda
"""RCGov reduced enums — strict mirror of Minimal Data Contract v0.1 (§2).

These value sets are the *canonical* label space for the Personal MVP. They are
deliberately coarse: wider taxonomies lower inter-rater agreement and make
classifier evaluation brittle (paper v0.7 §4.1, contract v0.1 §1). Finer labels
may only be added after kappa stabilizes.

Each enum's members and their *order* track the contract document exactly, so a
drift check (Dogfooding Test 001 -> ``schema_field_mismatch``) can compare this
module against ``docs/minimal_data_contract_v0_1.md`` directly.
"""
from __future__ import annotations

from enum import Enum

__all__ = [
    "AuthorityState",
    "TemporalStratum",
    "SegmentRole",
    "InjectionDecision",
    "GateResult",
    "OverrideReason",
    "DownstreamOutcomeType",
]


class _ContractEnum(str, Enum):
    """Base: string-valued enum whose ``value`` is the contract wire string.

    Subclassing ``str`` keeps JSON serialization trivial (``json.dumps`` emits
    the raw contract string) while still giving us a closed, validated set.
    """

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return self.value

    @classmethod
    def values(cls) -> list[str]:
        """Contract value strings, in contract order."""
        return [m.value for m in cls]

    @classmethod
    def coerce(cls, raw: "str | _ContractEnum"):
        """Validate ``raw`` against the closed set, returning the enum member.

        Raises ``ValueError`` with the allowed set on an unknown value — the
        contract is non-negotiable, so we fail loudly rather than guess.
        """
        if isinstance(raw, cls):
            return raw
        try:
            return cls(raw)
        except ValueError as exc:
            raise ValueError(
                f"{cls.__name__}: {raw!r} is not in the contract set "
                f"{cls.values()}"
            ) from exc


class AuthorityState(_ContractEnum):
    """Contract v0.1 §2.1 — how binding a segment's authority is."""

    CANONICAL = "canonical"  # currently binding or approved
    WORKING = "working"  # active but provisional
    DISPUTED = "disputed"  # competing authority claims exist
    DEPRECATED_OR_UNAUTHORIZED = "deprecated_or_unauthorized"  # revoked / not allowed to bind
    UNKNOWN = "unknown"  # authority cannot yet be determined


class TemporalStratum(_ContractEnum):
    """Contract v0.1 §2.2 — Annales-derived rate-of-change layer."""

    DURABLE = "durable"  # long-lived rule, policy, architecture, license
    CURRENT = "current"  # active project state, current version, sprint decision
    TEMPORARY = "temporary"  # short-lived event, log, one-off tool result
    UNKNOWN = "unknown"  # temporal role unclear


class SegmentRole(_ContractEnum):
    """Contract v0.1 §2.3 — single primary role for pack construction."""

    CONSTRAINT = "constraint"
    GOAL = "goal"
    FACT = "fact"
    HYPOTHESIS = "hypothesis"
    PREFERENCE = "preference"
    EVIDENCE = "evidence"
    DEPRECATED = "deprecated"
    CONFLICT = "conflict"
    SECRET_OR_RISK = "secret_or_risk"
    NOISE = "noise"


class InjectionDecision(_ContractEnum):
    """Contract v0.1 §2.4 — what happens to a governed segment."""

    INJECT = "inject"
    DIGEST = "digest"
    BACKGROUND = "background"
    QUARANTINE = "quarantine"
    ARCHIVE = "archive"
    REQUIRES_REVIEW = "requires_review"


class GateResult(_ContractEnum):
    """Contract v0.1 §2.5 — non-compensatory gate verdict."""

    PASS = "pass"
    SOFT_WARN = "soft_warn"
    FOREGROUND_WARN = "foreground_warn"
    BLOCK = "block"
    QUARANTINE = "quarantine"


class OverrideReason(_ContractEnum):
    """Contract v0.1 §2.6 — reasoned override reason codes."""

    IRRELEVANT_TO_CURRENT_TASK = "irrelevant_to_current_task"
    TEMPORARY_WORKING_ASSUMPTION = "temporary_working_assumption"
    USER_SELECTS_SEGMENT_A = "user_selects_segment_a"
    WILL_REVIEW_LATER = "will_review_later"
    KNOWN_FALSE_POSITIVE = "known_false_positive"
    OTHER = "other"


class DownstreamOutcomeType(_ContractEnum):
    """Contract v0.1 §2.7 — outcome attached to an override after the fact."""

    BUILD_SUCCESS = "build_success"
    BUILD_FAILURE = "build_failure"
    TEST_SUCCESS = "test_success"
    TEST_FAILURE = "test_failure"
    RUNTIME_ERROR = "runtime_error"
    ROLLBACK = "rollback"
    MANUAL_REPAIR = "manual_repair"
    TASK_SUCCESS = "task_success"
    TASK_FAILURE = "task_failure"
    UNKNOWN = "unknown"


# --- Gate semantics --------------------------------------------------------
# Hard gate results cannot be overridden by relevance (contract v0.1 §5, rule 3).
HARD_GATE_RESULTS = frozenset({GateResult.BLOCK, GateResult.QUARANTINE})

# Authority states considered "high authority" for the Authority Commitment Gate
# (spec v0.4 §6.4): a proposed-canonical with no commitment must be foregrounded.
HIGH_AUTHORITY_STATES = frozenset({AuthorityState.CANONICAL})
