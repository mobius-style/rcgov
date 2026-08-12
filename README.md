# RCGov — Mobius Reflective Context Governor

> RCGov cleans and governs AI context **before** the model reads it.

RCGov is a **local-first semantic hygiene and context-governance** tool for LLM
systems. Instead of trying to make a bigger context window, it provides a
**cleaner intake**: raw project material is turned into reviewable, gated,
provenance-preserved, disagreement-aware context packs before a model is
allowed to drink it.

The governing axiom is the context-side companion to Mobius answer entitlement:

```text
CommitAnswer_t  => ReflectiveReady_t      # answer only when justified
InjectContext_t => ContextReady_t         # inject only what is fit to govern
```

## What RCGov is built to catch

Raw project material entering an AI system as flat, undifferentiated text:
secrets, prompt-injection residue, stale specs, deprecated rules, contradictory
notes, uncommitted authority, temporary tool errors, copied hallucinations, and
low-provenance claims.

### And what it does not catch

The gates are non-compensatory and run before scoring, which is a real,
checkable ordering property. Their strength against any given item is
nevertheless exactly the recall of the scanner that flags it — **and that recall
is now measured, on our own component, and it is low for prompt injection.**

| against a 26-class authored evasion corpus | classes withheld |
|---|---:|
| the injection seed matcher alone | **9 / 26** |
| the structural pattern matcher alone | **12 / 26** |
| the full pipeline as shipped today (both, plus the provenance/authority gate) | **17 / 26** |
| planted credentials, 8 pattern classes | 24 / 24 |

Read the first row as the honest one: **a substring seed list is a detection
floor, not a defence** — one inserted word defeats a literal match. The measured
study ran against seeds alone, at 13 / 26 for the whole pipeline; the structural
matcher was added afterwards in response to that result and lifts the pipeline
to 17 / 26 with no false positives on the benign or credential-bearing controls
(`tests/test_injection_recall.py` pins both numbers).

**A third of the corpus still reaches the model, and it is the worse third.**
The nine surviving classes include the three the same study measured at 1.000
model compliance — chained instructions, debug-mode requests, and negation
tricks. Those are phrased as ordinary requests and carry no adversarial verb, so
pattern matching of this kind will not reach them at any width. There is also an
exploratory and unflattering result — on the classes the pipeline misses,
handing the model a governed pack was associated with *higher* injection
compliance than handing it the raw document (one artifact, p = 0.0117
unadjusted, does not survive multiplicity correction, mechanism unidentified).
Full method, limits and data:
**[DOI 10.5281/zenodo.21903321](https://doi.org/10.5281/zenodo.21903321)** ·
[artifacts](https://github.com/mobius-style/guardrail-silent-degradation).

The corpus was authored to probe evasion shapes, so it is adversarial by
construction and not a sample of real traffic; the number is a floor on a
hostile distribution, not an expected field rate. We have not measured a field
rate, and we have not benchmarked RCGov against dedicated guardrail products.

Concretely, these pass through:

- secrets with no recognizable format or entropy signature (a short password, an
  internal identifier that is sensitive only in context);
- prompt injections that carry no imperative override at all — a request framed
  as a hypothetical, a debug-mode ask, or a chained continuation reads like
  ordinary text to both detector families;
- stale or superseded text that carries no status marker to detect it by;
- anything the low-confidence authority/temporal heuristics rank wrongly. These
  are surfaced for review rather than trusted, by design.

RCGov bounds *what is admitted into context under a stated policy*, and logs
every decision so the boundary is auditable. It is not a guarantee that
unwanted material cannot reach the model. Treat a clean pack as "no gate fired",
not as "nothing bad is present".

**If you are evaluating RCGov, evaluate it for these**: deterministic
pre-generation removal, credential and provenance handling, an auditable
decision log, roughly 4 ms of added latency, and — since `244bb48` — a manifest
that reports how many rules were actually in force, so a degraded install is
distinguishable from a healthy one. **Do not adopt it as a prompt-injection
defence.** For that, compose it with a different mechanism class; a seed list
is one layer of a defence in depth, and on its own it is the weakest one we
measure.

## Status

**Pre-alpha / Personal MVP.** The full governance pipeline runs end-to-end:
`rcgov govern` ingests files and emits every contract artifact. Implemented:

- the **data contract** layer (`src/rcgov/contract/`), strictly conformant to
  *Minimal Data Contract v0.1*;
- **ingest** (encoding repair + content-addressed store), **segment**
  (markdown heading-aware, provenance-preserving), **scan**
  (regex+entropy secrets, imperative prompt-injection seeds), **propose**
  (transparent low-confidence keyword heuristics), **provenance**, the
  **non-compensatory gate** layer, **priority** (lexical TF-cosine), **conflict
  detection** (drift detectors routed via friction governance), and **pack**
  rendering;
- the canonical **papers** under `docs/`.

Model-independent by design (Decision Record 4): the ME5 embedding path is an
opt-in *upgrade* of relevance scoring, not a dependency. Authority/temporal
proposals are deliberately low-confidence and surfaced for review — RCGov's
thesis is to surface disagreement, not to trust automatic authority
classification.

## Architecture (robust core first)

```text
Input Files
  -> Ingest
  -> Segment
  -> Secret / Prompt-Injection Scan
  -> Role / Authority / Temporal Proposal
  -> Provenance Appraisal
  -> Non-Compensatory Gates          # safety, injection, provenance, authority-commitment, severe-conflict
  -> Priority Ranking                # admitted segments only
  -> Pack Placement
  -> Clean Context Pack + Non-Injection Report + Override/Outcome logs
```

Non-compensatory means **high relevance can never compensate** for a *detected*
secret, unsafe instruction, missing provenance, or uncommitted authority. Gates
run before scoring — that ordering is the invariant. Detection is what bounds
it: an item the scanner does not flag is never offered to a gate at all.

### Three levels of confidence (honesty statement)

1. **Robust engineering core** — gates, provenance, secret exclusion,
   deprecated-context separation, authority-disagreement surfacing. Implementable
   now, useful even if the temporal hypothesis fails.
2. **Implementation contract** — the reduced label space in
   `src/rcgov/contract/`. Required before implementation.
3. **Experimental bet** — Annales-derived *temporal-attention* pack placement.
   Shipped as an opt-in profile, **not** a core product claim. If a non-temporal
   attention-optimal baseline ties or wins the ablation, temporal strata are
   demoted to explanatory ontology.

## Quick start (scaffold)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest                      # tests should be green

# Dogfooding: govern RCGov's own documentation into a clean pack
rcgov govern docs/paper_v0_7.md docs/spec_v0_4.md docs/minimal_data_contract_v0_1.md \
  --task "Audit RCGov's own docs for drift" --out out
ls out/   # CLEAN_CONTEXT_PACK.md, NON_INJECTION_REPORT.md, CONFLICT_MAP.md, …
```

The dogfooding run quarantines the one section of the spec that lists prompt-
injection example phrases (§6.2) — RCGov declines to inject its own injection
examples — and confirms the code enums are in sync with the contract document.

### Streamlit MVP

A local UI over the same pipeline (spec §14). Upload files, describe the task,
optionally attach a commitment manifest, and read the artifacts in-page:

```bash
pip install -e ".[ui]"
PYTHONPATH=src streamlit run app/streamlit_app.py
```

The app logic lives in the streamlit-free `rcgov.service` layer and is covered
by unit tests; the app itself is smoke-tested with Streamlit's `AppTest` harness.

## Authority commitment

A *proposed* authority label never binds on its own (contract §5 rule 1). In an
unattended run, a segment proposed **canonical but uncommitted** is foregrounded
for review rather than injected — so the clean pack stays empty of canonical
material until a baseline is committed. That commitment is the user's
"smallest anchor set" (Authority Stabilization Mode, spec §11), declared in a
small manifest:

```yaml
# config/commitments.yaml
commitments:
  - source_match: "minimal_data_contract"   # this doc is the binding baseline
    authority: canonical
    commitment_source: repository_manifest
  - heading_match: "License"
    authority: canonical
    commitment_source: signed_policy
```

Committed segments satisfy the Authority Commitment Gate and flow into the
pack's *Active Canonical / Committed Context*, tagged with their commitment
source. When canonical material is proposed but nothing is committed, the
manifest surfaces an Authority Stabilization recommendation instead of silently
injecting or silently dropping it.

## Design decisions

See [`docs/DECISION_RECORD.md`](docs/DECISION_RECORD.md) for the locked choices
(MMV boundary, licensing, contract freeze, detection policy).

## Relationship to MOBIUS MMV

RCGov is a **clean-room sibling** of MOBIUS MMV, sharing only the Mobius
answer-entitlement philosophy. It carries **no MMV code dependency**. The only
borrowed asset is a seed list of prompt-injection patterns
(`config/injection_seeds.yaml`), authored by the same rights holder.

## License

- **Source code** (`src/`, `app/`, `tests/`, `config/`, build files):
  **AGPL-3.0-or-later** — see [`LICENSE`](LICENSE).
- **Paper / specification text** (`docs/`): **CC BY-NC-SA 4.0** — see
  [`docs/LICENSE-CC-BY-NC-SA.txt`](docs/LICENSE-CC-BY-NC-SA.txt).

Rights holder: MOBIUS.LLC / Taiko Toeda.

### Commercial license

If your organization cannot meet AGPL's source-disclosure obligations, a
commercial license is available from MOBIUS LLC (sole rights holder):
**USD 500 per month, per company — cancel anytime, no minimum term.**
Annual invoicing available at USD 5,000/year.

It is a license grant, not a service: no service is performed, no data of
yours is accessed, and nothing you run depends on our availability.

**Before you buy, read what this does not do.** RCGov's injection scanning
withholds 17 of 26 classes on our own published evaluation corpus
([DOI 10.5281/zenodo.21903321](https://doi.org/10.5281/zenodo.21903321)), and
the nine it misses are the ones models obeyed most often; it is a floor, not a
prompt-injection defence, and the same report documents a configuration defect
of ours that silently reduced it further until `244bb48`.
Buy it for deterministic pre-generation filtering, credential and provenance
handling, an auditable decision log, and coverage self-attestation — not for
injection protection.

Contact: **info@mobius.style** — licensing questions are not handled in Issues.

## Citation

Two companion records document the theory and the evaluation:

> Toeda, T. (2026). *Context Has Temporal Strata — Authority Disagreement,
> Minimal Data Contracts, Friction Governance, Annales Historiography, and the
> Mobius Reflective Context Governor.* MOBIUS LLC. DOI:
> [10.5281/zenodo.21231386](https://doi.org/10.5281/zenodo.21231386).

> Toeda, T. (2026). *Reflective Context Governance Reduces Context-Borne LLM
> Failures — A Controlled N=120 RAW-vs-CLEAN Evaluation.* MOBIUS LLC. DOI:
> [10.5281/zenodo.21231388](https://doi.org/10.5281/zenodo.21231388).
>
> Read with its stated scope: the benchmark is synthetic and templated, its
> metrics are keyword-based, and it covers four Groq-hosted models. It is
> evidence for this MVP on this benchmark — not a universal guarantee.

See `CITATION.cff` for machine-readable metadata.

## Related — the Möbius program

Part of the [MOBIUS](https://github.com/mobius-style) program — local-first, AGPL:

- [mmv](https://github.com/mobius-style/mmv) — answer-entitlement runtime: decides *whether* answering is warranted
- [rqa](https://github.com/mobius-style/rqa) — reflective questioning adapter: deepens *the question* when it is not
- [rcgov](https://github.com/mobius-style/rcgov) — reflective context governor: governs *what a model may read*
- [infinity](https://github.com/mobius-style/infinity) — composite capstone (MMV × RQA) with an OpenAI-compatible API
- [tokyo-insight](https://github.com/mobius-style/tokyo-insight) — on-demand civic-RAG engine for 東京都議会 deliberation records (engine + facts only)

## Incident report — silent ruleset degradation (fixed in 244bb48)

Between the first tagged release and commit
[`244bb48`](https://github.com/mobius-style/rcgov/commit/244bb48), the extended
prompt-injection ruleset was addressed by a working-directory-relative path and
was not packaged into the wheel. Any installation running outside a source
checkout therefore used only the five built-in seeds, while
`NON_INJECTION_REPORT.md` still read `Prompt-Injection Residue: _(none)_`.

The defect, its measured cost, and an adverse residual effect on the attacks
the guardrail misses are reported in full:
**DOI [10.5281/zenodo.21903321](https://doi.org/10.5281/zenodo.21903321)** ·
artifacts at
[mobius-style/guardrail-silent-degradation](https://github.com/mobius-style/guardrail-silent-degradation).

Since the fix, `CONTEXT_MANIFEST.json` carries a `ruleset` block reporting
active versus built-in rule counts, so a degraded run is distinguishable from a
healthy one without reading the code.
