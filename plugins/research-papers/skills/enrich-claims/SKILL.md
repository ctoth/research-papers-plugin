---
name: enrich-claims
description: Enrich existing source-branch claims by updating them through pks source propose-claim.
argument-hint: "<papers/Author_Year_Title>"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Enrich Claims: $ARGUMENTS

Improve claims that already exist on a propstore source branch. Reuse each claim's local id and call `pks source propose-claim` again with the enriched fields. Do not edit claim batch files.

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

If the source branch or claims are missing, run `paper-process` or `extract-claims` first.

## Step 1: Inspect Current Claims

Inspect the source branch's current claims and local ids using the propstore source state. If you need a filesystem view for reading only, materialize the source branch with `pks source sync` into a scratch/report directory; do not treat that materialized file as an authoring target.

Read:

- `<paper_dir>/notes.md`
- page images in `<paper_dir>/pngs/` for exact values and provenance
- current source claims for local ids and current field values

## Step 2: Enrich Through pks

For each correction or enrichment, rerun `pks source propose-claim` with the same `--id` and the full intended claim payload:

```bash
pks source propose-claim "$source_name" \
  --id claim7 \
  --type observation \
  --statement "Corrected and enriched claim statement." \
  --context "ctx_<author>_<year>_<slug>" \
  --concept-ref concept_a \
  --concept-ref concept_b \
  --condition "endpoint == 'primary_endpoint'" \
  --page 8 \
  --section "Discussion" \
  --quote-fragment "Brief supporting quote" \
  --notes "Methodological qualifier."
```

Parameter enrichment:

```bash
pks source propose-claim "$source_name" \
  --id claim8 \
  --type parameter \
  --concept hazard_ratio \
  --value 0.88 \
  --lower-bound 0.79 \
  --upper-bound 0.97 \
  --uncertainty-type "95% CI" \
  --context "ctx_<author>_<year>_<slug>" \
  --page 5
```

Rules:

- Reusing the same local claim id replaces that source-local claim.
- Include all fields that should remain on the claim; do not rely on partial update semantics.
- If `pks source propose-claim` reports missing concepts, propose those concepts first and rerun the claim command.
- Validation happens in `pks source propose-claim`; do not run file validators.

## Step 3: Add Missing Claims

If enrichment discovers important uncaptured findings, add them with new local ids through `pks source propose-claim`.

## Step 4: Report

```text
Claims enriched for: papers/[dirname]
  Claims updated: N
  New claims added: N
  Missing concepts encountered and fixed: [...]
  Validation boundary: pks source propose-claim
```
