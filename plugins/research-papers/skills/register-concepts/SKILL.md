---
name: register-concepts
description: Register a paper-local concept inventory into a propstore source branch. The primary extraction source is notes.md; claims.yaml is supplementary when present.
argument-hint: "<papers/Author_Year_Title>"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Register Concepts: $ARGUMENTS

Register the concepts needed by one paper into its propstore source branch using per-concept `pks source propose-concept` commands.

This skill is rerunnable. Its primary source is `notes.md`. If `claims.yaml` exists, use it only as a supplementary pass to catch concept references you missed on the first read.

Ontology-policy reference:

- `plugins/research-papers/docs/ontology-authoring-policy.md`

## Step 0: Validate

```bash
paper_dir="$ARGUMENTS"
ls "$paper_dir"/notes.md 2>/dev/null || echo "MISSING: notes.md"
ls knowledge/.git 2>/dev/null || echo "MISSING: knowledge/.git"
ls "$paper_dir"/claims.yaml 2>/dev/null || echo "OPTIONAL: claims.yaml not present"
```

If `notes.md` is missing, stop and run `paper-reader` first.
If `knowledge/.git` is missing, stop and report: `No propstore found. Run pks init first.`

## Step 1: Check Propstore State

Verify the source branch exists for this paper:

```bash
source_name=$(basename "$paper_dir")
pks source finalize "$source_name" 2>&1 || true
```

If the output indicates the source branch does not exist, stop and tell the user to run `source-bootstrap` first.

## Step 2: Discover Available Forms

Run `pks form list` and read the output. These are the only valid form values you may assign to concepts. Do NOT hardcode any form list -- use whatever `pks form list` returns.

```bash
pks form list
```

## Step 3: Build Concept Inventory From Notes

Read `notes.md`, especially sections such as:

- Methods
- Results
- Study Design
- Key Contributions
- Definitions
- Terminology introduced by the authors

From `notes.md`, identify all domain concepts the paper actually uses. For each concept, determine:

- `local_name`: how this paper refers to the concept (snake_case identifier)
- `definition`: 1-2 sentence definition that distinguishes it from near-neighbors
- `form`: chosen from the `pks form list` output in Step 2
- `values` (category concepts only): comma-separated list of known values this paper uses for the concept

### local_name vs proposed_name

`local_name` is how this paper refers to the concept. `proposed_name` is what it should be called in the registry. For new concepts these are usually the same. When proposing, `pks source propose-concept` uses `--name` for the local name.

### Granularity Guidance

Concepts ARE: domain-specific measurable quantities (hazard_ratio, event_rate), methodological constructs (cox_proportional_hazards, factorial_design), clinical categories (diabetes_mellitus, peripheral_arterial_disease), **conditioning axes** (endpoint, comparison, intervention — dimensions along which parameter values vary).

Concepts are NOT: named entities (Scotland, BMJ), specific trial names (POPADAD -- these are category values or source metadata), generic terms (data, result, study).

When in doubt: if two papers could independently measure or define the same thing, it's probably a concept.

### Compound-Unit Decomposition

When a quantity has a compound unit (mg/day, events/patient-year, dollars/hour), ask: **are the components independently variable?** If yes, they are separate concepts, not one concept with a compound unit.

Example: "aspirin 100 mg daily" is two independent facts — the dose (100 mg, form: mass) and the frequency (once daily, form: category). Another paper might use the same dose at a different frequency, or a different dose at the same frequency. Baking both into one concept with unit `mg/day` collapses two dimensions into one and prevents independent querying.

**Test:** If Paper A reports "100 mg daily" and Paper B reports "100 mg twice daily," can you tell them apart? If the concept is `aspirin_dose` with unit `mg/day`, Paper A is 100 mg/day and Paper B is 200 mg/day — you've lost the fact that both use the same tablet. With separate concepts (`aspirin_dose` = 100 mg, `dosing_frequency` = once_daily vs twice_daily), both dimensions are preserved.

**Rule:** When you see a compound unit, split it into its independently-variable components. Each component gets its own concept with its own form. The relationship between them is expressed through CEL conditions, not through compound units.

### Conditioning-Axis Concepts

Claims use CEL conditions like `endpoint == 'composite_primary'` or `comparison == 'aspirin_vs_placebo'`. **Every name on the LHS of a CEL condition must be a registered concept.** The propstore CEL checker validates condition names against the concept registry — unregistered names cause hard validation errors.

This means you must register conditioning axes as concepts, not just measurement targets. Common conditioning-axis concepts include:

- `endpoint` (category) — which outcome is being measured
- `comparison` (category) — which groups are being compared
- `intervention` (category) — which treatment arm
- `population` (category) — which subgroup or cohort
- `confidence_level` (ratio) — confidence level for interval estimates

These are real domain concepts: multiple papers will condition their parameters on the same axes. Register them with appropriate forms (usually `category` for string-valued axes, `ratio` or other quantity forms for numeric axes).

When proposing conditioning-axis concepts, include `--values` with the values this paper actually uses:

- `endpoint` with `--values composite_primary,fatal_or_nonfatal_mi,stroke,gi_bleeding`
- `comparison` with `--values aspirin_vs_placebo`
- `population` with `--values intention_to_treat,per_protocol`

The value set is extensible by default — listing only this paper's values is correct. Other papers will add theirs when they propose the same concept and get linked.

### Classification Rules

Before proposing a concept or category value, classify it using the ontology policy.

- If it is a paper-wide structural commitment, put it in the paper context instead of proposing it only to support claim conditions.
- If it is the left-hand side of CEL and multiple claims vary along it, it is a conditioning-axis concept.
- If it is a reusable outcome, intervention, population, or methodological construct, it is usually a first-class concept even if a claim also selects it through an axis.
- If it is only a selector like `primary_endpoint` or `per_protocol`, it is usually a category value on an axis, not the concept itself.
- If it fuses independently variable dimensions, decompose it instead of registering the fused label as the only representation.

Examples:

- `all_cause_mortality`, `major_bleeding`, `nonfatal_myocardial_infarction` -> usually first-class concepts
- `primary_endpoint`, `secondary_endpoint`, `safety_endpoint` -> usually category values on `endpoint`
- `intention_to_treat` -> usually a first-class methodological concept; may also appear as a selected `population` value for specific claims
- `aspirin_vs_placebo` -> decompose by default; keep as one comparison value only if the paper truly treats it as an indivisible named contrast

### Picking A Form For Numeric Quantities

`pks form list` is the authoritative current set — always consult it before choosing. Common picks for numeric quantities:

- `score` — bounded score-like quantity (kappa, IoU, F1, accuracy, BLEU).
- `ratio` — proportion or rate-of-occurrence (event_rate, hazard_ratio).
- `dimensionless` (if `pks form list` includes it) — unbounded dimensionless quantity (effect size, log-odds, z-score, Cohen's d).
- `probability` (if `pks form list` includes it) — [0,1] probabilities, p-values.
- `correlation` (if `pks form list` includes it) — [-1,1] correlations (Pearson r, Spearman rho).
- Dimensional quantities (`mass`, `time`, `pressure`, `length`, `acceleration`, etc.) — use the matching named form.

Do not invent a form name. `dimensionless` as a bare form may not yet exist in your propstore — check `pks form list` and fall back to the closest available form (often `score` for bounded quantities, `ratio` for proportions) if a more specific one isn't registered.

### Definition Quality

Good: "Ratio of hazard rates between treatment and control arms, measuring relative event risk over time."

Bad: "A ratio."

## Step 4: Register Concepts One At A Time

For each concept identified in Step 3, run:

```bash
source_name=$(basename "$paper_dir")
pks source propose-concept "$source_name" \
  --concept-name "<local_name>" \
  --definition "<definition>" \
  --form "<form>" \
  --values "<val1>,<val2>,<val3>"   # category concepts only; omit for non-category
```

For non-category concepts (ratio, count, time, mass, etc.), omit `--values` entirely. Using `--values` with a non-category form will produce an error.

Read the output for each concept:

- If output says `Linked '<name>' -> existing '<canonical_name>' (<artifact_id>)`: this concept already exists in the registry. Note the match. Any `--values` provided will be added to the existing concept's value set.
- If output says `Proposed new concept '<name>' (form: <form>)`: this is a new concept being proposed, with values stored in `form_parameters.values`.
- If output says `Unknown form '<form>'`: the form name is wrong. Check `pks form list` and try again with a valid form.

## Step 5: Supplementary Pass (if claims.yaml exists)

If `claims.yaml` exists in the paper directory, read it and check for concept references in the following fields:

- `concept` (parameter claims — the source-side authoring field)
- `target_concept`
- `concepts[]`
- `variables[].concept`
- `parameters[].concept`
- `conditions[]` — extract every LHS name from CEL expressions (e.g., `endpoint` from `endpoint == 'composite_primary'`). These names must be registered concepts.

Schema note:

- Parameter claims are authored with top-level `concept:` — that's the field on `SourceClaimDocument`, the schema `pks source add-claim` validates against. The master-side `ClaimDocument` carries the resolved value as `output_concept_id` after promotion; that's an internal artifact and not something you author.

For any concepts found in `claims.yaml` that were NOT already registered in Step 4, propose them using the same command:

```bash
pks source propose-concept "$source_name" \
  --concept-name "<local_name>" \
  --definition "<definition>" \
  --form "<form>" \
  --values "<val1>,<val2>"   # category concepts only; omit for non-category
```

## Step 6: Report

```text
Concepts registered for: papers/[dirname]
  From notes: N
  From claims supplementary pass: N
  Linked to existing: N
  Newly proposed: N
  Total: N
```
