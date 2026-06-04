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

## What RCGov prevents

Raw project material entering an AI system as flat, undifferentiated text:
secrets, prompt-injection residue, stale specs, deprecated rules, contradictory
notes, uncommitted authority, temporary tool errors, copied hallucinations, and
low-provenance claims.

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

Non-compensatory means **high relevance can never compensate** for a secret, an
unsafe instruction, missing provenance, or uncommitted authority. Gates run
before scoring.

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
  [`LICENSE-docs`](LICENSE-docs).

Rights holder: MOBIUS.LLC / Taiko Toeda.
