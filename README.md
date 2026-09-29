# RCGov — Mobius Reflective Context Governor

> RCGov decides what is admitted into an LLM's context, and leaves an auditable
> record of every decision.

RCGov is a **local-first semantic hygiene and context-governance** tool for LLM
systems. Instead of trying to make a bigger context window, it provides a
**cleaner intake**: raw project material is turned into reviewable, gated,
provenance-preserved, disagreement-aware context packs before a model is
allowed to drink it.

Its value is in the *determinism and the record* — the same document produces
the same admission decision, credentials and provenance are handled by stated
rules, and the manifest reports how many of those rules were actually in force.
It is **not** a security boundary against an adversary who is choosing their
phrasing; the measured numbers below say so explicitly.

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
decision log, single-digit-millisecond latency on short documents (4.2 ms
median on the study corpus, and it scales with text: the structural patterns
add roughly 10 ms per 100 KB, so a megabyte-scale document costs a fifth of a
second), and — since `244bb48` — a manifest
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
  (regex+entropy secrets, prompt-injection seed phrases and structural override
  patterns), **propose**
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

## Incident report — labelled secrets survived the rebuild (fixed in 0.2.1, 2026-09-29)

Two defects, both found by an inventory of the products that call rcgov and
confirmed by an adversarial review before release.

**1. AWS secret access keys and `sk-` API keys had no named pattern.** In
`aws_secret_access_key = …` the word `secret` is followed by `_access_key`, not
by `=`, so the assignment pattern did not match; `sk-…` keys had no pattern at
all. Both reached only the entropy backstop (`high_entropy_token`), which
`rebuild_bytes` keeps by default because it also fires on hashes, ids and
paths. A labelled secret therefore came back verbatim.

**2. A secret on a `#` line survived even when it was detected.** An excised
segment keeps its first line as a heading, and the segmenter treats every line
starting with `# ` as a heading — including `# AWS_SECRET_ACCESS_KEY=…` in a
`.env` file or a commented-out key inside a code fence. That line was copied
through, and repeated in `excluded[].heading`. This applied to every kind,
including the ones that were already detected.

Since 0.2.1: named kinds for AWS secret keys (label and value may be separated
by spaces, backticks, a table bar, a full-width colon, `=>`, or XML tags),
`sk-`/`gsk_` keys, Hugging Face, Google, GitLab, GitHub (all prefixes), Stripe,
JWTs, Slack webhooks, bearer tokens, Azure account keys, URL credentials, and
key names the old assignment pattern could not reach; prefixes are matched
after CJK text as well. `private_key_block` was widened from RSA / EC /
OPENSSH to any `BEGIN … PRIVATE KEY` header (DSA, ENCRYPTED, PGP). A heading
line that is itself flagged is replaced by the placeholder and withheld from
`excluded[].heading`. The heading line of an excised segment gets a stricter
rule than body text: any finding at all, including a bare high-entropy token,
removes the line. In the `heading` metadata a title is withheld when its line
was removed from the text or holds a confirmed kind; a title that stays in the
text — a file path, a commit hash — is shown (0.2.3; 0.2.1 and 0.2.2 hid those
too, which protected nothing and made the listing unreadable).

Independent reviews ran before release, on random strings of the right shape
(never real credentials), and each of the first five refused it:

1. The first draft let 39 of 75 secret-bearing document forms through.
2. The second ran in quadratic time on `token=token=…` (79 s for 200 KB),
   required a digit in every value and so missed letters-only `hf_` tokens,
   and removed identifiers such as `settings_production_secret_key_v2`.
3. The third was still quadratic on `eyJ-eyJ-…` (the JWT pattern, 7 s for
   200 KB) and on a page dense with tokens (the backstop's span check),
   removed `AccessKeyCredentialProvider1`, and missed a third of the short
   `sk-` keys whose body is broken by `-` or `_`.

4. The fourth found `rebuild_bytes` ten times slower than 0.2.0 under a long
   parent heading (each child re-scanned it), a flagged heading whose title
   still reached `excluded[].heading` (`# password: <7 chars>#`), and — in
   0.2.0 as well — a heading pattern that took two minutes on one 4 KB line
   (`# x<spaces>y`).

5. The fifth found that a heading flagged only by a seed from
   `config/injection_seeds.yaml` (`## from now on you will act as`) was still
   copied through, because the heading was re-scanned without the seed file.
   The record's own findings now decide.

All of these are fixed and under test. Measured on the released code, on one
machine: every adversarial shape from the reviews scans 2 MB in under 2 s and
doubles with the input. Against 0.2.0 on the same 147 shapes the scan is
slower on most — the median is about 4 times, the worst 44 times
(0.018 s → 0.79 s) — and faster on the dense ones where 0.2.0 was itself
quadratic (80 s → 1.9 s). `rebuild_bytes` end to end is about 2 times slower
than 0.2.0 on prose and up to about 4.6 times on input that is mostly
heading text, because headings are scanned again (one 2 MB heading line:
0.65 s → 2.9 s); it grows linearly wherever 0.2.0 does. Of 70 realistic value shapes × 200 random values, all
detect at 98 % or more except the limits listed below; over 32,166 local
files (179 M characters of code, configuration and prose) the new kinds fire
16 times, all on token-shaped values. These measurements are not in the
repository; the reproducers are, in `tests/test_scan.py` and
`tests/test_rebuild.py`. Of the five patterns in 0.2.0, four are byte-for-byte
unchanged; `private_key_block` is the widened one.

Forms that still survive, listed so nobody has to find them again:

- a 40-character string with no label, or with the label more than 24
  characters away, in a table's header row or a CSV header, or on the
  previous line (`Secret access key:` then the value; the snake_case and
  CamelCase labels followed by `:` are caught across the line break);
- a value that reads like words: a digits-only value, one case of letters up
  to 24 long, or camelCase — behind a vendor prefix, or behind a label that
  only the new pattern reaches (`secret_key`, `access_key`, `private_key`,
  quoted labels). Behind `token` / `password` / `secret` / `api_key` with `:`
  or `=` the 0.2.0 pattern still catches it. Real vendor tokens are not
  shaped like this; a hand-made one may be;
- a JWT with a header or payload segment shorter than 13 characters (`eyJ`
  and fewer than 10 more), and a token split by markdown emphasis;
- a value followed directly by `.` and a letter;
- a prefix glued to a preceding letter, including the `n` of an escaped `\n`
  in a JSON string;
- a YAML folded scalar, a base64-wrapped key, a passphrase written as prose;
- **passwords and symbol-bearing keys.** A value behind any label
  (`password`, `passwd`, `secret_key`, …) that is shorter than 16 characters
  behind a quoted label, or that contains characters outside
  `A–Z a–z 0–9 / + _ - ~` (Django's `SECRET_KEY`, most generated passwords),
  is caught only when the 0.2.0 assignment pattern catches it, and then often
  not over its full length;
- in a URL: a password in a single character class (all lower-case letters),
  and a token written as the user name (`https://<token>@host`);
- kinds with no pattern, such as Stripe's `whsec_`.

The long and random ones among these are still listed under `retained` as
`high_entropy_token`. The others — short passwords, passwords with symbols,
URL forms — are not listed anywhere: **rcgov is not a password scanner.**

Known false positives of the new kinds, accepted: a hex digest behind a key
label (`access_key: <sha1>`), documentation passwords in URLs
(`user:p4ssw0rd@`, `:changeme123@`), and digit-and-letter placeholders behind
a vendor prefix (`sk-1234567890abcdef…`), and some long identifiers behind a
key label — with a digit inside, or camelCase made of short words
(`private_key = Ed25519PrivateKeyParametersImplV2`, `GetCurrentKeySet`; 1.4 %
of the 4,082 identifiers of 16 or more characters in the Python standard
library). The segment is excised and listed in `excluded` with its reason.

Not changed by this release: the files written under `workdir/out/`
(`NON_INJECTION_REPORT.md`, `CLEAN_CONTEXT_PACK.md`) still print headings as
they are, flagged or not, and the work directory holds a copy of the input.
The fix covers what `rebuild_bytes` returns. Treat the work directory as
sensitive as the input. A heading is withheld from the text when its line
is flagged; a pattern that fires only on the stripped title (`# system: …`)
withholds the title in `excluded[].heading` but leaves the line in the text.
Also unchanged: input is read with universal
newlines, so "byte-for-byte" holds for LF input and CRLF comes back as LF;
and the pipeline's own cost grows faster than linearly with the number of
segments (2 MB of tiny sections takes about a minute in both versions).

What this does not change: detection is still pattern-based and English-centric
for injection; a secret with no label and no known prefix is indistinguishable
from a hash and is kept and listed, not removed; vendors' published example
keys have the shape of real ones and are removed. **Products that carry their
own copy of the rebuild step do not get fix 2 from upgrading rcgov** — they keep
the heading line themselves. Call `rebuild_bytes` instead of copying it — or,
since 0.2.2, `rebuild_records(doc, records)` if you run `rcgov.pipeline.run`
yourself to keep your own integrity checks or input wrapping. It is the one
implementation `rebuild_bytes` itself uses; importing it fails on an rcgov
older than 0.2.2, so a caller cannot fall back to the old behaviour unnoticed.

## Incident report — the Clean Context Pack is a triage, not a scrub (three downstream callers, fixed 2026-09-20)

`govern_bytes()` returns `CLEAN_CONTEXT_PACK.md`: the segments the pipeline
judged *placeable* for the task after authority and priority appraisal. Three
products in this program — `moebiusT7/gemma-4-12b-mobius-custom` (v1.0),
`moebiusT7/gemma-4-12b-mobius-custom-c1` / `gemma-4-26b-a4b-mobius-custom-c1`
(v1), and `mobius-style/mobius-governance` (≤ 0.8.2) — handed a language model
that pack as if it were *the retrieved context minus what the scanner flagged*.
It is not. Without a commitments manifest a segment of plain prose with no
provenance is routed to `requires_review` and simply does not appear, and the
pack carries no marker for it: measured 2026-09-19, an English paragraph
vanished while the caller reported the context as governed. The C1 wrappers
additionally never reached this point — their call had the wrong shape, raised
`TypeError`, and was caught into a labelled *fail-open* that passed the raw
context through. Found on the first day the wrappers were used as the author's
own daily session-record clerk.

Nothing in `govern_bytes` was wrong for what it is: a pack is what the
Streamlit MVP renders, and the paper describes it as a triage. The defect was
downstream — and the API offered no honest primitive for the scrubbing use
case, so each caller improvised one. Since 0.2.0 it does:

```python
from rcgov.service import rebuild_bytes

r = rebuild_bytes([("ctx.md", text.encode())], task="Answer the user's question.")
r.text["ctx.md"]   # the input, byte-identical except where a segment was excluded
r.excluded         # [{input, segment, heading, reason}] — placeholder left in the text
r.retained         # heuristic-only flags (high_entropy_token) kept and listed
r.admitted         # segments that reached the model unchanged
```

Every segment is kept byte-for-byte, kept with a listed heuristic flag, or
replaced by a placeholder whose reason is recorded. Spans are verified against
the run's own records and a manifest that disagrees with them raises. The model
wrappers were re-released on this design on 2026-09-19/20 (they carry a local copy
so `rcgov` stays optional there); `mobius-governance` 0.8.3 follows the same day
(advisory MG-2026-003). `tests/test_rebuild.py` pins the
triage behaviour of the pack and every branch of the rebuild.

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
