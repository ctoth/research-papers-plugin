---
name: extract-claims
description: Extract propositional claims from a paper directory into the propstore source branch using pks source propose-claim.
argument-hint: "<papers/Author_Year_Title>"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Extract Claims: $ARGUMENTS

Extract high-value claims from a paper and author them directly into the paper's propstore source branch. Do not create, edit, validate, or ingest paper-directory claim batch files.

Ontology-policy reference:

- `plugins/research-papers/docs/ontology-authoring-policy.md`

## Step 0: Validate

```bash
paper_dir="$ARGUMENTS"
source_name=$(basename "$paper_dir")
ls "$paper_dir"/notes.md 2>/dev/null || echo "MISSING: notes.md"
ls knowledge/.git 2>/dev/null || echo "MISSING: knowledge/.git"
pks source finalize "$source_name" 2>&1 || true
```

- `notes.md` missing -> STOP. Run `paper-reader` first.
- `knowledge/.git` missing -> STOP. Run `source-bootstrap` or `paper-process`.
- If the source branch does not exist -> STOP. Run `source-bootstrap` first.

## Step 1: Read Source Material

Read:

- `<paper_dir>/notes.md` as the primary source.
- Page images in `<paper_dir>/pngs/` for every exact numeric value, confidence interval, p-value, sample size, page citation, or claim whose wording matters.

spot-check every extracted high-value claim against the relevant page image before proposing it.

When a claim cites page `N`, the corresponding page image is:

- `pngs/page-{(N-1):03d}.png`

Examples:

- page 1 -> `pngs/page-000.png`
- page 12 -> `pngs/page-011.png`

Do not use PDF text extraction as the basis for rereading the paper.

## Step 2: Determine Context

Every claim must have a context. Use the context created by `author-context`, conventionally:

```text
ctx_<author>_<year>_<trial_or_short_slug>
```

If no context exists for this paper, run `author-context` before extracting claims.

## Step 3: Ensure Claim Concepts Exist

Before proposing a claim, every referenced concept must be present on the source branch or master registry. Use `register-concepts` to propose missing concepts.

If `pks source propose-claim` fails with `unknown concept reference(s): ...`, do not edit a file. Propose the missing concepts with `pks source propose-concept`, then rerun the failed claim command.

## Step 4: Propose Claims Through pks

Use one `pks source propose-claim` command per claim. This command is the validation boundary and the mutation boundary. It validates source-local concepts, CEL conditions, and numeric value bounds before writing.

## Step 4A: Structured Evidence Contract

For empirical, clinical, statistical, benchmark, or otherwise quantitative papers, extract the quantitative result as structured evidence while reading the paper. Do not postpone this to collection reconciliation.

If the paper reports an endpoint-level estimate, threshold, rate, count, confidence interval, credible interval, standard error, p-value, or uncertainty bound that someone could compare against another paper, author a `parameter` or `measurement` claim for it. A prose `observation` may summarize the authors' interpretation, but it must not be the only representation of the numeric result.

Required behavior:

- For every primary outcome, endpoint, metric, or benchmark result, author at least one structured claim with `--value` and the relevant `--condition` axes.
- For every major adverse, safety, failure, cost, or risk outcome, author the structured effect, rate, or measurement claim even when the paper's headline emphasizes benefit.
- Preserve intervals with `--lower-bound` and `--upper-bound` whenever reported.
- Do not invent a scalar `--uncertainty` for a confidence interval or credible interval. If the paper reports "95% CI" or similar interval metadata, record that wording in `--quote-fragment` or `--notes` unless you also have a separate scalar uncertainty measure such as a standard error or standard deviation.
- Put comparison dimensions in CEL conditions, not only in prose: examples include `endpoint`, `comparison`, `population`, `analysis_set`, `follow_up`, `intervention`, and `comparator`.
- Extract explicit null or negative findings as claims too. A result like "no significant reduction" is not a reason to skip the endpoint.
- If no quantitative result is present in a paper that appears empirical, report that explicitly in Step 7.

Bad extraction:

```bash
pks source propose-claim "$source_name" \
  --id claim4 \
  --type observation \
  --statement "The intervention improved one outcome but worsened another." \
  --context "ctx_author_year_trial" \
  --page 5
```

Good extraction:

```bash
pks source propose-claim "$source_name" \
  --id claim4 \
  --type parameter \
  --concept effect_estimate \
  --value 1.25 \
  --lower-bound 1.05 \
  --upper-bound 1.49 \
  --context "ctx_author_year_trial" \
  --condition "endpoint == 'primary_outcome'" \
  --condition "comparison == 'intervention_vs_comparator'" \
  --condition "analysis_set == 'prespecified_analysis'" \
  --quote-fragment "effect estimate 1.25; 95% CI, 1.05 to 1.49" \
  --page 5
```

Also author the corresponding harm endpoint separately rather than folding it into the same prose statement.

Observation, mechanism, comparison, and limitation claims:

```bash
pks source propose-claim "$source_name" \
  --id claim1 \
  --type observation \
  --statement "Single declarative sentence capturing the claim." \
  --context "ctx_<author>_<year>_<slug>" \
  --concept-ref concept_a \
  --concept-ref concept_b \
  --condition "endpoint == 'primary_endpoint'" \
  --page 7 \
  --section "Results" \
  --quote-fragment "Brief supporting quote" \
  --notes "Any methodological qualifier needed to interpret the claim."
```

Parameter claims:

```bash
pks source propose-claim "$source_name" \
  --id claim2 \
  --type parameter \
  --concept hazard_ratio \
  --value 0.88 \
  --context "ctx_<author>_<year>_<slug>" \
  --condition "endpoint == 'serious_vascular_event'" \
  --page 5 \
  --section "Results" \
  --quote-fragment "Brief supporting quote"
```

Bounds and uncertainty:

```bash
pks source propose-claim "$source_name" \
  --id claim3 \
  --type parameter \
  --concept hazard_ratio \
  --value 0.88 \
  --lower-bound 0.79 \
  --upper-bound 0.97 \
  --context "ctx_<author>_<year>_<slug>" \
  --quote-fragment "hazard ratio, 0.88; 95% CI, 0.79 to 0.97" \
  --page 5
```

Use `--uncertainty` and `--uncertainty-type` only when the paper reports a scalar uncertainty measure:

```bash
pks source propose-claim "$source_name" \
  --id claim4 \
  --type parameter \
  --concept effect_estimate \
  --value 1.25 \
  --uncertainty 0.08 \
  --uncertainty-type "standard_error" \
  --context "ctx_<author>_<year>_<slug>" \
  --page 5
```

Rules:

- Use stable local ids: `claim1`, `claim2`, ...
- Reusing a local id updates that source-local claim. Do this intentionally when enriching or correcting a claim.
- For non-parameter claims, use repeated `--concept-ref` for every referenced concept.
- For parameter claims, use `--concept` for the form-bearing output concept.
- Use repeated `--condition` for CEL conditions.
- Do not create an intermediate claim batch file.
- Do not run file validators; source proposal validation happens inside `pks source propose-claim`.

## Step 5: Claim Selection

Before extracting a claim, ask: "Would someone building a system in this domain query this claim?" and "Would someone adjudicating between competing approaches query this?" If neither, skip it.

Extract:

- Architectural or clinical findings that generalize beyond one table cell.
- Design constraints and validated thresholds.
- Cross-paper findings.
- Failure modes and limitations.
- Design rationale and mechanisms.
- Comparisons against prior work.

Skip:

- Study logistics unless they are part of the claim being adjudicated.
- Benchmark metadata without interpretation.
- Implementation details without rationale.
- Repeated table cells that should instead become one synthesized observation.

## Step 6: CEL Conditions Contract

Every name on the left side of a CEL condition must be a registered concept. Category condition values are string literals; boolean conditions use `true` / `false`; structural concepts cannot appear in CEL expressions.

If a condition axis such as `endpoint`, `comparison`, `population`, or `analysis_set` is missing, propose it as a category concept first:

```bash
pks source propose-concept "$source_name" \
  --concept-name endpoint \
  --definition "Outcome or endpoint selected for a claim-specific result." \
  --form category \
  --values "primary_endpoint,all_cause_mortality,major_bleeding"
```

## Step 7: Report

```text
Claims extracted for: papers/[dirname]
  Context: [ctx_author_year_slug]
  Claims proposed: N total
  Missing concepts encountered and fixed: [...]
  Validation boundary: pks source propose-claim
```
