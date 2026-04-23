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
- Context assumptions do NOT validate concept names at add time — validation happens later when claims referencing the context are compiled against the master concept registry.

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

Rerun this skill if the paper's structural assumptions change (rare — usually only if you discover you misclassified the design). To revise an existing context, edit `knowledge/contexts/<ctx_name>.yaml` directly and commit — no dedicated CLI exists today for context mutation.
