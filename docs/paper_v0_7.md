# Context Has Temporal Strata

## Authority Disagreement, Minimal Data Contracts, Friction Governance, Annales Historiography, and the Mobius Reflective Context Governor

**Series:** Mobius Reflective Series / Reflective Context Governor Line
**Document type:** Conceptual architecture paper and implementation-synchronized position paper
**Version:** v0.7 implementation-contract synchronized draft
**Release intent:** Zenodo-style working paper / public preprint candidate
**Companion artifact:** RCGov Minimal Data Contract v0.1
**Author of record:** Taiko Toeda
**Rights holder:** MOBIUS.LLC
**License note:** Draft paper text: CC BY-NC-SA 4.0 unless separately relicensed. Reference schemas and procedures may be released under AGPL-3.0-or-later or a separate MOBIUS.LLC license.

---

# Abstract

Long-context AI systems increasingly fail not because they lack context, but because they receive too much undifferentiated context. Durable project constraints, active sprint decisions, stale specifications, temporary tool errors, copied model hallucinations, secrets, and user preferences may all enter a context window as flat text. The model is then asked to infer authority, freshness, provenance, temporal scope, and safety from position and wording alone. This paper defines that failure mode as **contextual flattening**, with one important subtype, **temporal flattening**: the collapse of information that changes at different speeds into a single undifferentiated prompt mass.

The Mobius Reflective Context Governor (RCGov) is proposed as a semantic filtration and context-governance layer for this problem. Its robust core is not the claim that Annales historiography has already been empirically validated as an AI ordering strategy. The robust core is narrower and more defensible: (1) context should pass non-compensatory gates before it is scored or injected; (2) authority proposals must be separated from authority commitments; (3) when human authority labels have low inter-rater agreement, the system should surface disagreement rather than pretend that automatic classification has solved authority; and (4) disagreement visibility itself must be governed through friction governance so that alert fatigue does not cause users to bypass the governor.

The Annales School, especially Braudel's distinction between event-time, conjunctural time, and longue duree, is treated here as an interpretive ontology for context with different rates of change. In product terms, its strongest current role is not segment-level admissibility. Rather, it motivates pack-level placement, temporal coverage diagnostics, and experiments in attention-aware ordering. This remains an experimental bet. If attention-optimal non-temporal ordering performs as well as or better than hybrid temporal-attention placement, then Annales-derived temporal strata should be demoted from product moat to explanatory ontology and review metadata.

The v0.7 synchronization adds a minimal implementation contract. RCGov Personal should start with a reduced label space: five authority states, four temporal strata, ten segment roles, and a small set of injection decisions, gate results, and override reasons. The first product should not attempt a full ontology engine. It should implement a thin vertical slice: ingest, segment, secret and prompt-injection scan, provenance minimum gate, authority proposal, authority-disagreement surfacing, deprecated/stale visibility, clean pack generation, non-injection reporting, and reasoned override logging. DFI/ORS friction governance should initially ship as logging plus conservative cold-start heuristics, not as a fully calibrated learned risk model.

The central thesis is therefore pragmatic: before asking a model to answer, govern what it is allowed to read. RCGov is not a bigger context window. It is a cleaner intake.

**Keywords:** AI context governance; semantic filtration; long-context LLMs; RAG; prompt injection; authority disagreement; kappa-first evaluation; friction governance; override risk; Annales School; Braudel; temporal flattening; context hygiene.

---

# Resource Note and Honesty Statement

This paper is conceptual and architectural. It does not report production telemetry, human-subject deployment evidence, or benchmark superiority. It distinguishes three levels of confidence:

1. **Robust engineering core.** Secret filtering, provenance preservation, non-compensatory gates, deprecated-context separation, and authority-disagreement surfacing are implementable with existing techniques and are useful even if the temporal-ordering hypothesis fails.
2. **Implementation-contract claim.** A reduced data contract is required before implementation. The v0.7 paper, v0.4 specification, and Minimal Data Contract v0.1 are synchronized around that reduced contract.
3. **Experimental bet.** Annales-derived temporal attention may improve downstream outcomes by placing durable constraints, active state, and event-time facts into attention-aware zones. This must be tested against non-temporal attention-optimal baselines.

The paper uses historical language, but it does not ask AI researchers to accept historiography as authority. It asks only whether an old ontology of different temporal layers can be translated into a testable context-governance hypothesis.

---

# 1. Why Context Governance Exists

Modern LLM systems are often described as if larger context windows solve context. In practice, larger windows can make context pollution scalable. The problem is no longer merely whether a model has access to enough material. The problem is whether the material is safe, current, authorized, relevant, properly scoped, and placed in a way that the model can use without collapsing everything into one flat prompt mass.

A durable license clause, an active branch decision, a stale README, a temporary build log, a copied hallucination from a previous model run, and the user's latest instruction are not the same kind of context. They age at different speeds. They have different authority. Some should bind the model. Some should be reviewed. Some should be quarantined. Some should not be injected at all.

RCGov addresses this problem by treating context injection as a governance event. The relevant question is not simply "what can fit into the window?" The relevant question is: what is contextually ready to govern model behavior?

The minimal axiom is:

```text
InjectContext_t => ContextReady_t

not ContextReady_t => Action_t in {
  clean,
  quarantine,
  verify,
  ask,
  archive,
  abstain_from_injection
}
```

This axiom is deliberately paired with the broader Mobius answer-entitlement principle:

```text
CommitAnswer_t => ReflectiveReady_t
InjectContext_t => ContextReady_t
```

However, the novelty of RCGov should not be overstated as a reusable readiness slogan. The real work lies in authority, provenance, non-compensatory gates, disagreement visibility, and friction governance.

---

# 2. Why Annales, Translated for AI Engineers

The useful AI translation is simple:

> LLM context failure is often a failure to distinguish different speeds of reality.

Annales historiography is relevant because it treats events, conjunctures, and durable structures as different temporal layers rather than as equal narrative items. In AI context terms:

| Historical layer | AI context analogue | Typical risk if flattened |
|---|---|---|
| Event-time | latest user request, tool output, one-off error log | momentary noise overrides durable constraint |
| Conjunctural time | active sprint, current release, project phase, working hypothesis | temporary state becomes permanent rule |
| Longue duree / durable structure | license, safety rule, architecture, constitutional policy, project philosophy | structural constraint is buried or treated as stale merely because it is old |

The point is not that Braudel directly solves prompt engineering. The point is that historical method has long dealt with a problem familiar to systems engineers: information changes at different speeds, and systems break when layers with different rates of change are mixed without governance.

A common failure in long-context LLM workflows is temporal flattening. The model receives raw text in which an old durable rule and a recent temporary event are adjacent. Recency alone cannot solve this. Newest is not always highest authority. Oldest is not always obsolete. RCGov turns this distinction into implementation surfaces: temporal labels, pack zones, non-injection reports, and ordering ablations.

---

# 3. Robust Contributions and Experimental Bet

## 3.1 Robust contribution A: non-compensatory gates before scores

RCGov must not permit high relevance to compensate for secrets, unsafe instructions, missing provenance, or uncommitted authority. A scalar ContextReady score is not sufficient. The architecture must separate gate decisions from priority ranking.

```text
Raw Segment
  -> Non-Compensatory Gates
  -> Admitted Segment Set
  -> Priority Scoring
  -> Pack Placement
  -> Injection / Digest / Background / Quarantine / Archive
```

Safety, prompt injection, provenance minimum, severe conflict, and authority commitment are gates or limiters. They are not relevance factors.

## 3.2 Robust contribution B: authority disagreement instead of fake authority classification

In many real projects, the problem is not that the machine needs to infer the correct authority label. The problem is that the project itself lacks a stable authority baseline. Human reviewers may disagree over whether a segment is canonical, working, disputed, deprecated, or unauthorized. If inter-rater agreement is low, automatic classifier precision becomes misleading. It measures agreement with an unstable target.

RCGov therefore distinguishes:

- **authority_proposed:** a machine or reviewer suggestion;
- **authority_committed:** an explicit commitment from user, policy, manifest, repository, signature, or approved review.

When kappa is low, the system should not claim reliable authority classification. It should surface authority disagreement as governance debt.

## 3.3 Robust contribution C: friction governance

Authority disagreement surfacing can itself fail if it exhausts the user. In low-agreement personal projects, repeated warnings may create alert fatigue and induce routine override. RCGov therefore treats disagreement visibility as a governed friction channel.

The rule is:

> Disagreement visibility must itself be governed.

The stronger v0.7 rule is:

> Friction may be reduced only when downstream risk remains bounded.

This motivates Disagreement Fatigue Index (DFI), Override Risk Score (ORS), elastic alert thresholds, reasoned override logs, and cold-start anchoring.

## 3.4 Experimental contribution: temporal attention

Annales-derived temporal strata may improve context use by influencing pack placement. But this is not yet proven. The testable hypothesis is:

> Hybrid temporal-attention placement reduces context-originated downstream failures compared with pure temporal descent, random admitted segments, temporal gating alone, and non-temporal attention-optimal sandwich ordering.

If this hypothesis fails, RCGov remains useful through its robust core. The Annales component should then become explanatory ontology, review metadata, and interface language rather than product moat.

---

# 4. Minimal Implementation Contract v0.1

The v0.7 paper adopts the same reduced contract as the v0.4 specification and the companion Minimal Data Contract v0.1.

## 4.1 Authority states

```text
canonical
working
disputed
deprecated_or_unauthorized
unknown
```

These are intentionally coarse. Earlier drafts used wider taxonomies. That was useful for theory, but likely to reduce inter-rater agreement in implementation. Finer labels may be added only after kappa stabilizes.

## 4.2 Temporal strata

```text
durable
current
temporary
unknown
```

These map approximately to structural, conjunctural, and event-time context while avoiding unnecessary early granularity.

## 4.3 Segment roles

```text
constraint
goal
fact
hypothesis
preference
evidence
deprecated
conflict
secret_or_risk
noise
```

A segment may carry secondary notes, but the MVP should select a single primary role for pack construction.

## 4.4 Injection decisions

```text
inject
digest
background
quarantine
archive
requires_review
```

## 4.5 Gate results

```text
pass
soft_warn
foreground_warn
block
quarantine
```

## 4.6 Override reasons

```text
irrelevant_to_current_task
temporary_working_assumption
user_selects_segment_a
will_review_later
known_false_positive
other
```

This reduced contract is not a theoretical endpoint. It is the minimal contract needed for implementation, evaluation, and dogfooding.

---

# 5. Formal Architecture

## 5.1 Segment record

```json
{
  "segment_id": "seg_00042",
  "document_id": "doc_001",
  "text_ref": "storage://segments/seg_00042",
  "hash": "sha256:...",
  "source_path": "spec.md",
  "heading_path": ["RCGov", "Authority"],
  "role_proposed": "constraint",
  "authority_proposed": "canonical",
  "authority_committed": null,
  "temporal_stratum_proposed": "durable",
  "provenance_quality": "known_source",
  "safety_status": "pass",
  "gate_result": "foreground_warn",
  "injection_decision": "requires_review"
}
```

## 5.2 Non-compensatory gates

Minimum gates:

1. **Safety Gate:** blocks secrets, unsafe operational material, inappropriate personal data, and dangerous instructions.
2. **Prompt-Injection Gate:** quarantines instructions embedded in source documents that attempt to override system behavior.
3. **Provenance Minimum Gate:** prevents orphaned or untraceable segments from becoming high-authority injected context.
4. **Authority Commitment Gate:** prevents proposed high authority from becoming binding context without commitment.
5. **Severe Conflict Gate:** blocks or foregrounds unresolved conflicts that affect the current task.

## 5.3 Priority score for admitted segments

Only after gates are applied does RCGov rank admitted segments.

```text
PriorityScore(s_i) =
  0.45 * relevance(s_i)
+ 0.25 * task_proximity(s_i)
+ 0.15 * compression_integrity(s_i)
+ 0.15 * injection_fitness(s_i)
```

Safety, authority, severe conflict, and provenance are not factors in this score. They have already acted as gates or limiters.

## 5.4 Pack placement

Admitted segments are placed into a clean context pack according to the selected profile. The experimental hybrid temporal-attention profile places:

- durable constraints near the front;
- current task facts in attention-critical positions, often near the controlled tail or repeated summary;
- temporary event-time notes only when task-relevant;
- deprecated and do-not-use material outside the active pack, in a non-injection report.

---

# 6. Authority Agreement Protocol

Before evaluating an authority classifier, measure whether human reviewers can agree.

```text
Step 1: Prepare a small seed corpus.
Step 2: Two or more reviewers label authority_state using the reduced five-label set.
Step 3: Compute inter-rater agreement, e.g. Cohen kappa.
Step 4: If kappa >= 0.75, classifier evaluation may proceed.
Step 5: If 0.40 <= kappa < 0.75, use classifier proposals with review.
Step 6: If kappa < 0.40, activate disagreement-surfacing mode.
```

Interpretation:

| Kappa | Mode | Product behavior |
|---:|---|---|
| >= 0.75 | strong agreement | classifier can be evaluated against adjudicated labels |
| 0.60-0.74 | moderate agreement | proposals are useful but review remains visible |
| 0.40-0.59 | weak agreement | proposals become low-confidence review aids |
| < 0.40 | poor agreement | surface disagreement; do not market automatic authority classification |

Low kappa is not merely a classifier failure. It is evidence of governance debt. RCGov should display that debt in workably compressed form.

---

# 7. Friction Governance and Override Risk

## 7.1 Disagreement Fatigue Index

DFI estimates the user's alert burden.

Possible components:

```text
DFI =
  alert_density_per_session
+ repeated_overrides
+ ignored_warnings
+ unresolved_disagreement_age
+ no_reason_override_rate
```

High DFI may reduce real-time alert frequency. It may not weaken hard gates or suppress high-risk disagreement.

## 7.2 Override Risk Score

ORS estimates how often a disagreement type causes downstream failure when overridden.

```text
ORS(d_i) = P(task_failure | override of disagreement type d_i)
```

In early versions this is not a learned value. It is initialized with conservative priors and updated only when downstream outcome data exists.

## 7.3 Cold-start anchoring

For a disagreement type with insufficient samples:

```text
if sample_count(d_i) < N_min:
    ORS(d_i) = conservative_prior(disagreement_type, base_severity)
else:
    ORS(d_i) = observed_failure_rate_after_override(d_i)
```

The cold-start rule prevents DFI from suppressing unknown-risk warnings merely because the user is tired.

## 7.4 Elastic alert threshold

```text
ElasticRisk(d_i) =
  alpha * ORS(d_i)
+ beta  * ImpactScope(d_i)
+ gamma * IrreversibilityRisk(d_i)
- delta * DFI
```

Routing:

```text
if HardGate(d_i):
    block_or_require_explicit_override
elif ElasticRisk(d_i) >= foreground_threshold:
    foreground_alert
elif ElasticRisk(d_i) >= digest_threshold:
    include_in_digest
else:
    background_log
```

This creates a bounded compromise: RCGov becomes quieter when the user is fatigued, but not when silence is likely to produce downstream failure.

## 7.5 Reasoned override

Override should not be treated as defeat. It is data.

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

After a build, test, rollback, deployment, or user review event, downstream outcome can be attached to the override record.

---

# 8. Personal MVP Scope

RCGov Personal v0.1 should not attempt full ontology automation. It should implement the robust core.

## 8.1 In scope

1. ingest Markdown, text, JSON, DOCX, PDF where possible;
2. segment into traceable units;
3. detect secrets and prompt-injection residue;
4. preserve provenance;
5. propose reduced authority labels;
6. surface authority disagreement;
7. mark deprecated or stale context;
8. apply non-compensatory gates;
9. generate clean context pack;
10. generate non-injection report;
11. record reasoned overrides;
12. log downstream outcomes when available.

## 8.2 Experimental profile

Temporal attention ordering, temporal flattening diagnostics, and attention-aware placement should be implemented as an experimental profile, not as the core product claim.

## 8.3 Out of scope for Personal MVP

- organizational role separation;
- audit appeals;
- power-drift dashboards;
- learned ORS without sufficient longitudinal data;
- fine-grained authority ontology;
- fine-grained temporal ontology;
- enterprise compliance workflow.

---

# 9. Dogfooding Test 001

The first meaningful test corpus should be RCGov's own artifacts. (Repository note:
retargeted per Decision Record 3(b) to the current synchronized trio —
`paper_v0_7.md`, `spec_v0_4.md`, `minimal_data_contract_v0_1.md`.)

Expected detections:

- authority state mismatch;
- temporal stratum mismatch;
- priority-score mismatch;
- duplicated or drifting section numbering;
- mojibake or encoding issues;
- schema fields present in one document but absent in the other.

Expected outputs:

```text
CONFLICT_MAP.md
NON_INJECTION_REPORT.md
CLEAN_CONTEXT_PACK.md
AUTHORITY_REVIEW_QUEUE.jsonl
MINIMAL_DATA_CONTRACT_DIFF.md
```

This dogfooding case is valuable because it demonstrates RCGov without relying on hypothetical examples. The tool detects the exact type of context drift its own documentation produced.

---

# 10. Evaluation Plan

## 10.1 Robust core metrics

| Metric | Meaning |
|---|---|
| secret detection recall | whether secrets are kept out of injected context |
| prompt-injection detection recall | whether hostile source instructions are quarantined |
| provenance minimum violations | orphaned high-authority context admitted by mistake |
| stale/deprecated visibility | deprecated material separated from active pack |
| authority disagreement surfacing usefulness | whether low-agreement segments become reviewable rather than silently binding |
| clean pack task success | downstream performance against raw-context baseline |

## 10.2 Authority metrics

Measure kappa before classifier precision.

- inter-rater authority kappa;
- proposal precision against adjudicated labels only when kappa is adequate;
- disagreement surfacing rate;
- governance-debt compression quality.

## 10.3 Friction metrics

- alert density;
- override rate;
- no-reason override rate;
- DFI trajectory;
- downstream failures after override;
- cold-start ORS calibration drift;
- retention or continued use.

## 10.4 Temporal attention ablation

Compare:

1. raw context;
2. admitted random order;
3. pure temporal descent;
4. attention-optimal sandwich without temporal labels;
5. hybrid temporal-attention placement;
6. full RCGov profile.

If the non-temporal attention-optimal condition wins or ties hybrid temporal-attention, then Annales should be demoted to explanatory ontology and review metadata.

---

# 11. Product Strategy

## 11.1 Personal-first

Personal RCGov should be positioned as local-first semantic hygiene for developers, researchers, and writers.

Initial value:

- cleaner prompts;
- safer context packs;
- secret exclusion;
- stale-version visibility;
- provenance preservation;
- authority disagreement surfacing;
- reduced context pollution.

## 11.2 Organizational later

Organizational RCGov is a different product tier. It requires:

- role separation;
- reviewer/approver/auditor workflows;
- appeal paths;
- audit log retention;
- policy integration;
- power-drift monitoring;
- compliance reporting.

Do not burden Personal MVP with Organizational governance.

---

# 12. Limitations

RCGov is not a truth machine. It cannot automatically settle authority in domains where humans cannot agree. It cannot make raw context safe without a conservative gate layer. It cannot learn reliable ORS without longitudinal outcome data. It cannot prove that temporal-attention placement works before ablation.

The honest product claim is narrower and stronger:

> RCGov turns raw context into reviewable, gated, provenance-preserved, disagreement-aware context packs before the model is allowed to read them.

That claim is implementable now.

---

# 13. Conclusion

RCGov is semantic filtration infrastructure for the long-context era. Its robust value does not depend on proving that Annales-inspired temporal placement always wins. The robust value lies in preventing raw, unsafe, stale, unsupported, and disputed context from silently governing downstream model behavior.

The engineering instruction is clear:

> Do not build the ontology engine first. Build the contract, the gates, the disagreement surface, the override log, and the dogfooding demo.

The first product should show a simple fact: when context is polluted, contradictory, stale, or unauthorized, a model should not drink it raw.
