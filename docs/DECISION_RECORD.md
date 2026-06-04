# RCGov Repository Decision Record

**Status:** locked for the Personal MVP scaffold
**Date:** 2026-06-04
**Repository:** `mobius-style/rcgov`

This record captures the decisions made before standing up the repository. It is
the resolved constitution for the scaffold; later changes should append, not
silently overwrite.

---

## Decision 1 — RCGov / MMV code boundary

**Decision:** Independent, clean-room repository. **No** MMV code dependency
(no submodule, no monorepo).

- The only borrowed asset is the **prompt-injection seed pattern strings**,
  copied into [`config/injection_seeds.yaml`](../config/injection_seeds.yaml).
  Same rights holder (MOBIUS.LLC / Taiko Toeda), so no third-party license
  conflict with AGPL.
- The relevance path uses `intfloat/multilingual-e5-large` as a **public model**
  (HuggingFace). Using the same model as MMV does **not** create an MMV code
  dependency.

**Implication:** RCGov can be released and licensed entirely on its own terms;
the MMV public snapshot's clean boundary is preserved.

## Decision 2 — Licensing

**Decision:**

| Surface | License |
|---|---|
| Source code (`src/`, `app/`, `tests/`, `config/`, build files) | **AGPL-3.0-or-later** |
| Paper / specification text (`docs/`) | **CC BY-NC-SA 4.0** |

- **AGPL (not plain GPL):** network use triggers the source-disclosure
  obligation. A future hosted *Organizational* edition would therefore have to
  offer source **or** be sold under a separate MOBIUS.LLC commercial license
  (dual-licensing).
- **No CLA at this stage.** Commercial dual-licensing later requires either
  keeping authorship single (MOBIUS.LLC) or collecting contributor consent at
  that time.
- The CC **NonCommercial** term restricts reuse of the *paper text*; it does
  **not** restrict use, modification, or sale of the *software*.

## Decision 3 — Contract freeze (resolving in-document drift)

The three source documents already contained a `schema_field_mismatch` — exactly
the class of drift RCGov is built to detect.

**3(a) — `Segment.text` storage:** adopt **`text_ref` + `text_preview`**
(Minimal Data Contract v0.1 §4 is canonical). The inline `text` form from
spec v0.4 §4.2 is dropped. Rationale: provenance hashing and the
"do not duplicate secret text everywhere" goal both favour storage by reference.
For the MVP the store is a local SQLite / content-addressed file (`.rcgov_store/`).

**3(b) — Dogfooding Test 001 input:** **retarget** to the actual current trio
(`paper_v0_7.md`, `spec_v0_4.md`, `minimal_data_contract_v0_1.md`). The
documents' named inputs (`*_v0_6_final`, `*_v0_3_final`) are not in hand, and
drift across the three synchronized current docs is a stronger demo. The
`encoding_mojibake` check uses a **deliberately dirtied fixture**
(`tests/dogfooding/fixtures/mojibake_dirty.md`), because the ingested docs
themselves are cleaned on entry.

## Decision 4 — Detection logic policy (model-independent)

| Concern | MVP implementation |
|---|---|
| Secret detection | regex + Shannon entropy |
| Prompt-injection | heuristic seed patterns (`config/injection_seeds.yaml`) |
| Relevance / task-proximity | `multilingual-e5-large` (experimental, opt-in) |
| DFI / ORS | **not learned** — conservative priors + logging only (`N_min = 5`) |

This keeps the spec's "implementable now" claim honest and avoids a hard model
dependency in the robust core.

---

## Carried-forward notes

- Mojibake in the original drafts (e.g. a literal `â` where an em dash belongs)
  is **cleaned** when the documents are written into `docs/`. The dirty form is
  preserved only inside the test fixture.
- `pyproject.toml` declares a `rcgov` console entry point; the CLI is a stub for
  now (`src/rcgov/cli.py`).
