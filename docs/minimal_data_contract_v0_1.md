# RCGov Minimal Data Contract

## Version 0.1 — Implementation Baseline

**Companion artifacts:**
- Context Has Temporal Strata v0.7
- Mobius Reflective Context Governor Specification v0.4

**Purpose:** single source of truth for the first RCGov Personal implementation.

---

# 1. Why This Contract Exists

The first implementation of RCGov should not use the large theoretical label spaces from earlier drafts. Wide taxonomies lower inter-rater agreement and make classifier evaluation brittle. This contract defines the reduced enums, object fields, and output files required for a Personal MVP.

This contract should be treated as canonical for implementation. The paper and specification should reference it rather than inventing separate schemas.

---

# 2. Enums

## 2.1 authority_state

```json
[
  "canonical",
  "working",
  "disputed",
  "deprecated_or_unauthorized",
  "unknown"
]
```

## 2.2 temporal_stratum

```json
[
  "durable",
  "current",
  "temporary",
  "unknown"
]
```

## 2.3 segment_role

```json
[
  "constraint",
  "goal",
  "fact",
  "hypothesis",
  "preference",
  "evidence",
  "deprecated",
  "conflict",
  "secret_or_risk",
  "noise"
]
```

## 2.4 injection_decision

```json
[
  "inject",
  "digest",
  "background",
  "quarantine",
  "archive",
  "requires_review"
]
```

## 2.5 gate_result

```json
[
  "pass",
  "soft_warn",
  "foreground_warn",
  "block",
  "quarantine"
]
```

## 2.6 override_reason

```json
[
  "irrelevant_to_current_task",
  "temporary_working_assumption",
  "user_selects_segment_a",
  "will_review_later",
  "known_false_positive",
  "other"
]
```

## 2.7 downstream_outcome_type

```json
[
  "build_success",
  "build_failure",
  "test_success",
  "test_failure",
  "runtime_error",
  "rollback",
  "manual_repair",
  "task_success",
  "task_failure",
  "unknown"
]
```

---

# 3. Document Object

```json
{
  "document_id": "doc_001",
  "source_path": "spec.md",
  "document_type": "markdown",
  "created_at": null,
  "modified_at": "2026-05-30T00:00:00Z",
  "ingested_at": "2026-05-30T10:30:00Z",
  "hash": "sha256:...",
  "raw_text_ref": "storage://raw/doc_001"
}
```

Required fields:

```text
document_id
source_path
document_type
ingested_at
hash
raw_text_ref
```

---

# 4. Segment Object

```json
{
  "segment_id": "seg_00042",
  "document_id": "doc_001",
  "heading_path": ["RCGov", "Authority"],
  "text_ref": "storage://segments/seg_00042",
  "text_preview": "v7.4.x should be treated as the active governance line.",
  "token_estimate": 18,
  "source_span": {"start": 2040, "end": 2128},
  "hash": "sha256:..."
}
```

Required fields:

```text
segment_id
document_id
text_ref
hash
```

---

# 5. Governed Segment Object

```json
{
  "segment_id": "seg_00042",
  "role_proposed": "constraint",
  "authority_proposed": "canonical",
  "authority_committed": null,
  "temporal_stratum_proposed": "durable",
  "provenance_quality": "known_source",
  "safety_status": "pass",
  "gate_result": "foreground_warn",
  "injection_decision": "requires_review",
  "priority_score": null,
  "notes": ["Proposed canonical, but no committed authority exists."]
}
```

Rules:

1. `authority_proposed` may not substitute for `authority_committed`.
2. `priority_score` is computed only after non-compensatory gates.
3. `quarantine` and `block` cannot be overridden by relevance.

---

# 6. Disagreement Object

```json
{
  "disagreement_id": "dis_001",
  "type": "api_version_conflict",
  "segments": ["seg_031", "seg_044"],
  "summary": "Two segments disagree about the active FastAPI version.",
  "task_relevance": 0.87,
  "base_severity": 0.65,
  "impact_scope": "medium",
  "irreversibility_risk": 0.20,
  "alert_route": "foreground_warn"
}
```

---

# 7. Override Object

```json
{
  "override_id": "ovr_001",
  "disagreement_id": "dis_001",
  "reason_code": "temporary_working_assumption",
  "free_text_reason": "Using the newer API baseline for this branch.",
  "timestamp": "2026-05-30T00:00:00Z",
  "downstream_outcome": null
}
```

---

# 8. Downstream Outcome Object

```json
{
  "outcome_id": "out_001",
  "override_id": "ovr_001",
  "event_type": "build_failure",
  "timestamp": "2026-05-30T00:35:00Z",
  "evidence_ref": "logs/build_001.txt",
  "severity": "medium"
}
```

---

# 9. Priority Score

Priority scoring applies only to admitted segments.

```text
PriorityScore(s_i) =
  0.45 * relevance(s_i)
+ 0.25 * task_proximity(s_i)
+ 0.15 * compression_integrity(s_i)
+ 0.15 * injection_fitness(s_i)
```

Do not score secrets, safety failures, prompt-injection residues, orphaned high-authority claims, or severe unresolved conflicts into admission.

---

# 10. Friction Governance Baseline

## 10.1 DFI

```text
DFI =
  alert_density_per_session
+ repeated_overrides
+ ignored_warnings
+ unresolved_disagreement_age
+ no_reason_override_rate
```

## 10.2 ORS cold start

```text
if sample_count(d_i) < N_min:
    ORS(d_i) = conservative_prior(disagreement_type, base_severity)
else:
    ORS(d_i) = observed_failure_rate_after_override(d_i)
```

Default:

```text
N_min = 5
```

## 10.3 ElasticRisk

```text
ElasticRisk(d_i) =
  alpha * ORS(d_i)
+ beta  * ImpactScope(d_i)
+ gamma * IrreversibilityRisk(d_i)
- delta * DFI
```

Hard gates override this calculation.

---

# 11. Output Files

```json
[
  "CLEAN_CONTEXT_PACK.md",
  "NON_INJECTION_REPORT.md",
  "AUTHORITY_REVIEW_QUEUE.jsonl",
  "OVERRIDE_LOG.jsonl",
  "DOWNSTREAM_OUTCOME_LOG.jsonl",
  "CONTEXT_MANIFEST.json"
]
```

---

# 12. Dogfooding Test Contract

> **Repository note (Decision Record 3b):** retargeted to the current trio.

Input:

```text
paper_v0_7.md
spec_v0_4.md
minimal_data_contract_v0_1.md
```

Expected conflict types:

```text
authority_state_mismatch
temporal_stratum_mismatch
priority_score_mismatch
section_numbering_drift
encoding_mojibake
schema_field_mismatch
```

Expected outputs:

```text
CONFLICT_MAP.md
NON_INJECTION_REPORT.md
CLEAN_CONTEXT_PACK.md
MINIMAL_DATA_CONTRACT_DIFF.md
```

---

# 13. Implementation Rule

Start with the reduced contract. Do not implement the full ontology first.

The first RCGov Personal product should prove four things:

1. unsafe context is excluded;
2. provenance is preserved;
3. authority disagreement is surfaced;
4. a clean context pack improves downstream AI work compared with raw context.

Everything else is secondary.
