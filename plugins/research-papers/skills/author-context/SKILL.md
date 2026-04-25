---
name: author-context
description: Create a propstore context for one paper with CEL assumptions, parameters, and perspective. Every claim extracted from the paper will reference this context. Required before extract-claims if the paper does not already have one.
argument-hint: "<papers/Author_Year_Title>"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Author Context: $ARGUMENTS

Create the per-paper context that carries the paper's structural assumptions (population, intervention, follow-up, design). Every claim this paper extracts will reference the context by name. Promote fails on contextless claims, so this must happen before extract-claims.

Ontology-policy reference:

- `plugins/research-papers/docs/ontology-authoring-policy.md`

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

Apply this decision rule before writing any assumption:

- If the fact holds for essentially every claim in the paper, it belongs in context.
- If the fact varies across claims within the paper, it belongs in claim-level `conditions[]`, not in context.

Typical context material:

- trial-wide intervention identity, dose, formulation, and schedule
- comparator identity
- trial design and adjudication regime
- cohort-wide eligibility facts
- follow-up regime

Typical condition material that should stay out of context:

- endpoint selectors
- subgroup selectors
- ITT vs per-protocol selectors
- arm-specific reported slices

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
Error: context '<ctx_name>': assumption[N] = '<expr>': Undefined concept: '<concept_name>'
```

The LHS name is not in the master concept registry. Before retrying, register it. Pick a form that matches how the assumption uses the name:

- `== true` / `== false` on the RHS → `--form boolean`
- `== '<string>'` on the RHS → `--form category --values "<a,b,c>"` (leave extensible, i.e. omit `--closed`, unless your domain demands closure)
- integer `>= N` / `<= N` → `--form count`
- non-integer numeric, or a dimensional quantity (mass, time, etc.) → whichever quantity form fits. Check `pks form list` for the available set.

```bash
pks concept add \
  --domain <your_domain> \
  --name <concept_name> \
  --form <boolean|category|count|...> \
  [--values "<v1,v2,...>"]    # category only
  --definition "<one-sentence definition in domain terms>"
```

`pks concept add` auto-commits. Retry the context add afterward.

### CEL parse error on dotted notation

```
Error: context '<ctx_name>': assumption[N] = '<prefix>.<field> == <value>': Parse error: Unexpected character at position M: '.<field> == <value>'
```

Propstore's CEL grammar does not accept dotted paths on concept references — LHS names must be flat registered concepts. Pick a flat name (drop the prefix, or replace `.` with `_` to preserve grouping intent), register it, and rewrite the assumption:

```
# Before (rejected)
- <prefix>.<field> == <value>

# After (flat name registered, assumption rewritten)
- <field> == <value>          # or <prefix>_<field> == <value> if disambiguation matters
```

If you're authoring a group of related markers, use a consistent flat-naming convention and register all of them before retrying — don't interleave partial fixes.

### Structural concept in CEL

```
Error: context '<ctx_name>': assumption[N] = '<expr>': Structural concept '<concept_name>' cannot appear in CEL expressions
```

The concept exists but is declared `physical_dimension_form: structural`. CEL forbids structural concepts on its boundaries — structural is for decorative/referential roles, not truth-valued ones. Two recoveries, in order of preference:

1. **Use a different concept.** Often a boolean or category sibling says the same thing. Run `pks concept list` and `pks concept show <nearby_name>` to look for one. Rewrite the assumption against that sibling.
2. **Flip the form, if the structural classification is wrong.** Run `pks concept show <concept_name>` and confirm the original form declaration was the mistake (usually: a boolean-shaped fact was authored as structural during early ingest). Then edit `knowledge/concepts/<concept_name>.yaml`:
   - Change `physical_dimension_form: structural` to the correct form (usually `boolean`).
   - The concept YAML carries a `version_id: sha256:...` content hash. Changing the form invalidates it. Run `pks build`; the mismatch error prints the expected new hash. Paste it back into the YAML.
   - Commit both lines (the form edit and the hash update) in one commit.

When committing any YAML inside a propstore-backed `knowledge/` repository: always run `git diff --cached --stat` after `git add` and before `git commit`. The propstore git backend shares the index with user git and can leave unrelated mutations staged; a blind commit can pick them up. Verify the staged set matches your intent every time.

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
