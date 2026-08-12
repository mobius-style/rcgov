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
| Prompt-injection | heuristic seed patterns (`config/injection_seeds.yaml`) **+ structural patterns (2026-08-12, see below)** |
| Relevance / task-proximity | `multilingual-e5-large` (experimental, opt-in) |
| DFI / ORS | **not learned** — conservative priors + logging only (`N_min = 5`) |

This keeps the spec's "implementable now" claim honest and avoids a hard model
dependency in the robust core.

### 4(a) — Structural injection patterns (2026-08-12)

**Decision:** add a second, structural detector family alongside the seed
phrases, running on every scan by default (`scan_injection(..., structural=False)`
restores the old behaviour for reproducing published results).

**Why:** the seed list is a substring matcher, so any rephrasing defeats it —
the evasion `ignore ALL previous instructions` walks past the built-in seed
`ignore previous instructions` on one inserted word. The structural patterns
match the *shape* of an override instead: an imperative verb bound to an
instruction-like object inside a short window, a role reassignment, a spoofed
turn marker. They were promoted from the integration-layer guard that shipped
with `gemma-4-12b-mobius-custom`, where they already ran as defense in depth
over this scanner.

**Measured, not assumed** (26-class authored evasion corpus,
DOI 10.5281/zenodo.21903321): seeds + provenance/authority gates withheld
13 / 26 classes, structural patterns alone 12 / 26, the union 17 / 26 — with
zero hits on benign controls, zero hits on credential-bearing documents, and
carrier retention unchanged at 26 / 26. Pinned by
`tests/test_injection_recall.py`, which was itself verified to fail on the
pre-change build before being adopted.

**What it costs, measured on real traffic** (237 project documents, ~4.5 MB):
four documents gained a structural finding. Three of them are papers that
*quote* attack strings — the standard false positive of any injection detector
run over security literature — and one is an ordinary sentence ("override with
the orphan-snapshot push above"). Only the largest of the four lost content
from its pack (9.6 KB of 1.1 MB, 0.9%), and every exclusion is named in
`NON_INJECTION_REPORT.md`, so the loss is visible rather than silent. The
secretary's gated verbs (`docs`, `handoff`, `git-history`) re-ran with zero
segments excluded and zero abstains.

Latency: unchanged on short documents (4.23 → 4.24 ms median, study corpus,
median 184 chars) but the patterns scan the whole text, costing roughly 10 ms
per 100 KB. Lowercasing once and dropping `IGNORECASE` would recover ~30% and
was rejected: `str.lower()` is not length-preserving on all of Unicode, and
this project's corpus is largely Japanese, so the saving would be bought with
an offset-desync hazard in the excerpt reporting. A literal prefilter was also
measured and rejected — the trigger words include `show`, `print`, and
`output`, so 123 of 230 real documents pass it and the saving was 5%.

**What this decision explicitly does not do:** it raises a floor. Nine classes
survive the union, including the three the same study measured at 1.000 model
compliance (chained instructions, debug-mode requests, negation tricks). Those
carry no adversarial verb, so no pattern matcher of this family reaches them at
any width — widening the regexes further trades false positives for nothing.
The README's "do not adopt this as a prompt-injection defence" language stands
and is not revisable by tuning this detector.

---

## Carried-forward notes

- Mojibake in the original drafts (e.g. a literal `â` where an em dash belongs)
  is **cleaned** when the documents are written into `docs/`. The dirty form is
  preserved only inside the test fixture.
- `pyproject.toml` declares a `rcgov` console entry point; the CLI is a stub for
  now (`src/rcgov/cli.py`).
