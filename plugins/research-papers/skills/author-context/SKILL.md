---
name: author-context
description: Create a propstore context for one paper with CEL assumptions, parameters, and perspective. Every claim extracted from the paper will reference this context. Required before extract-claims if the paper does not already have one.
argument-hint: "<papers/Author_Year_Title>"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Author Context: $ARGUMENTS

Create the per-paper context that carries the paper's structural assumptions (population, intervention, follow-up, design). Every claim this paper extracts will reference the context by name. Promote fails on contextless claims, so this must happen before extract-claims.

## What A Context Is

A context is a first-class `ist(c, p)` qualifier (McCarthy, lifted-axioms style). It says "these propositions hold within these structural assumptions." Claim-level `conditions[]` handle finer axes like endpoint or ITT-vs-per-protocol; context handles the trial's BIG structural commitments — who was studied, with what intervention, for how long, under which design.

Assumptions are CEL expressions. Parameters are named scalar bindings. Perspective names whose view this context represents (e.g., `authors_primary_analysis` vs. `per_protocol_analysis`).

## Step 0: Validate Inputs

```bash
paper_dir="$ARGUMENTS"
ls "$paper_dir"/notes.md 2>/dev/null || echo "MISSING: notes.md"
ls "$paper_dir"/metadata.json 2>/dev/null || echo "MISSING: metadata.json"
ls knowledge/.git 2>/dev/null || echo "MISSING: knowledge/.git"
```

If any are missing, stop and report.

## Step 1: Derive The Context Name

Convention: `ctx_<author>_<year>_<trial-slug>`. Use lowercase snake_case.

- `ctx_ikeda_2014_jppp` (Japanese Primary Prevention Project)
- `ctx_bowman_2018_ascend` (A Study of Cardiovascular Events in Diabetes)
- `ctx_wolfe_2025_aspree_xt` (ASPREE extended follow-up)

If the paper has no canonical trial acronym, use a short descriptive slug.

## Step 2: Extract Structural Assumptions

Read `notes.md`. Identify the paper's trial design facts that apply to EVERY claim the paper makes:

- **Population** — cohort definition: age range, region, risk factors, inclusion/exclusion.
- **Intervention** — specific drug, dose, form, frequency.
- **Comparator** — placebo, no treatment, other active agent.
- **Study type** — primary prevention vs secondary, RCT vs observational, blinded vs open-label, parallel vs crossover.
- **Follow-up** — median, maximum, scheduled length.
- **Sample size** — enrolled, analyzed, per-arm.
- **Adjudication** — blinded outcome committee, endpoint definitions source.

From these, derive:
- **CEL assumptions**: boolean or equality CEL expressions over registered concepts (e.g., `primary_prevention == true`, `blinded_outcome_adjudication == true`, `open_label == true`). Any concept name on the LHS must be a registered concept in master OR will be registered during the paper's register-concepts step.
- **Parameters**: KEY=VALUE scalar bindings that are constant across all paper claims (e.g., `trial_name=JPPP`, `sample_size=14464`, `followup_median_yr=5.02`, `age_range_min_yr=60`).
- **Perspective**: the analysis viewpoint name — usually `authors_primary_analysis` for the paper's headline results. Use a different perspective name (e.g., `per_protocol_analysis`, `subgroup_analysis_<name>`) if you're authoring a separate context for an alternative analysis.

## Step 3: Author The Context

```bash
pks context add \
  --name <ctx_name> \
  --description "<one-sentence description of the trial: design, cohort, intervention, comparator, duration>" \
  --assumption "<CEL assumption 1>" \
  --assumption "<CEL assumption 2>" \
  [--assumption "<...>" ...] \
  --parameter "trial_name=<acronym>" \
  --parameter "sample_size=<int>" \
  --parameter "followup_median_yr=<float>" \
  [--parameter "<KEY=VALUE>" ...] \
  --perspective authors_primary_analysis
```

Notes:
- `--description` is required; make it a single informative sentence.
- Each `--assumption` is one CEL expression. Repeat the flag for multiple.
- Each `--parameter` is one `KEY=VALUE` string. Repeat the flag for multiple.
- **Propstore >= 0.2.2 validates every assumption's CEL against the master concept registry at `pks context add` time.** The add is rejected if any LHS name is undefined, dotted, or references a structural-form concept. Errors name the exact assumption index and the offending expression. See "If the add is rejected" below for recovery.

## Step 3.5: If the add is rejected

`pks context add` will refuse the add and print the line it tripped on. Three failure modes; each has a specific recovery.

### Undefined concept

```
Error: context 'ctx_foo': assumption[2] = 'double_blind == true': Undefined concept: 'double_blind'
```

The LHS name is not in the master concept registry. Before retrying, register it. For design-marker booleans (`double_blind`, `placebo_controlled`, `open_label`, `free_of_cvd_at_baseline`, etc.) the pattern is:

```bash
pks concept add \
  --domain clinical_trial \
  --name double_blind \
  --form boolean \
  --definition "Trial design where both participants and investigators are unaware of treatment assignment."
```

For a category concept (e.g. `comparator == 'placebo'`):

```bash
pks concept add \
  --domain clinical_trial \
  --name comparator \
  --form category \
  --values "placebo,no_aspirin,no_treatment,active_comparator" \
  --definition "Arm used as the reference in the trial's primary comparison."
```

For a count (pooled trial counts, pooled N, person-years): `--form count`. For dose/duration/age: use the matching quantity form (see `pks form list` — `mass`, `time`, `dimensionless`, etc.). Leave category value sets extensible (omit `--closed`) unless the domain demands closure.

Once registered, retry the context add. Concept adds auto-commit; no `git add` needed.

### CEL parse error on dotted notation

```
Error: context 'ctx_foo': assumption[0] = 'population.age_ge_70 == true': Parse error: Unexpected character at position 10: '.age_ge_70 == true'
```

CEL in propstore doesn't take dotted paths on concept references. Flatten the name — replace the dot with an underscore (or just drop the prefix) — and register that flat concept. `population.age_ge_70` becomes `age_ge_70` (or `population_age_ge_70` if disambiguation matters). Then register `age_ge_70` as boolean (or whatever form matches) and rewrite the assumption to the flat form before retrying the add.

If you're authoring a batch of related assumptions (e.g. all the `design.*` markers for a trial), use a consistent flat-naming convention — `design_randomized`, `design_double_blind`, etc. — or register them all bare if the domain space allows.

### Structural concept in CEL

```
Error: context 'ctx_foo': assumption[3] = 'enteric_coated_formulation == true': Structural concept 'enteric_coated_formulation' cannot appear in CEL expressions
```

The concept exists but its `physical_dimension_form` is `structural`, which propstore's CEL grammar forbids (structural is for decorative/referential concepts, not truth-valued ones). Two recoveries:

1. **Use a different concept.** Often there's a boolean sibling (`enteric_coated_formulation` is structural → use `aspirin_formulation == 'enteric_coated'` if `aspirin_formulation` is a category concept instead).
2. **If the concept genuinely SHOULD be boolean** (the misclassification is in the concept, not your assumption), the concept's YAML needs a form flip: `physical_dimension_form: structural` → `physical_dimension_form: boolean`. There is no CLI for this today — edit `knowledge/concepts/<name>.yaml` directly. You must also update the `version_id: sha256:...` line to match the new content hash (run `pks build` after editing; it prints the expected hash in the mismatch error and you paste that back). See `feedback_propstore_git_backend.md` in project memory for git-discipline when committing concept YAMLs.

Pick option 1 first. Only do option 2 if you checked `pks concept show <name>` and concluded the original form declaration was wrong.

## Step 4: Verify

```bash
pks context list | grep <ctx_name>
cat knowledge/contexts/<ctx_name>.yaml
```

Confirm the file exists and the assumptions/parameters/perspective look right.

## Output

```
Context authored: <ctx_name>
  Description: <...>
  Assumptions: N
  Parameters: M
  Perspective: <name>
  File: knowledge/contexts/<ctx_name>.yaml
```

## When To Rerun

Rerun this skill if the paper's structural assumptions change (rare — usually only if you discover you misclassified the design). To revise an existing context, edit `knowledge/contexts/<ctx_name>.yaml` directly and commit — `pks context` has `add`, `list`, `search`, `show`, `remove` but no in-place `update` for the assumptions/parameters block today. Use `pks context remove` + re-add for wholesale replacement; hand-edit for a targeted assumption fix (and remember to update `version_id` if the concept YAMLs carry content hashes).

To revise the lifting-rule block of an existing context, use the `pks context lifting` subcommands (`add`, `update`, `remove`) — no hand-editing required.
