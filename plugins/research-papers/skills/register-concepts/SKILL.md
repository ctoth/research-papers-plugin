---
name: register-concepts
description: Register a paper-local concept inventory into a propstore source branch. The primary extraction source is notes.md; claims.yaml is supplementary when present.
argument-hint: "<papers/Author_Year_Title>"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Register Concepts: $ARGUMENTS

Register the concepts needed by one paper into its propstore source branch.

This skill is rerunnable. Its primary source is `notes.md`. If `claims.yaml` exists, use it only as a supplementary pass to catch concept references you missed on the first read.

## Step 0: Validate

```bash
paper_dir="$ARGUMENTS"
ls "$paper_dir"/notes.md 2>/dev/null || echo "MISSING: notes.md"
ls "$paper_dir"/claims.yaml 2>/dev/null || echo "OPTIONAL: claims.yaml not present"
```

If `notes.md` is missing, stop and run `paper-reader` first.

## Step 1: Check Propstore State

```bash
ls knowledge/.git 2>/dev/null
pks source --help 2>/dev/null | head -20
```

If no `knowledge/` directory exists, stop and report: `No propstore found. Run pks init first.`

## Step 2: Build The Primary Concept Inventory From Notes

Read `notes.md`, especially sections such as:

- Methods
- Results
- Study Design
- Key Contributions
- Definitions
- Terminology introduced by the authors

From `notes.md`, identify all domain concepts the paper actually uses. For each concept, write:

- `local_name`
- `proposed_name`
- a real 1-2 sentence definition
- the correct `form`

Good definitions distinguish the concept from near-neighbors and would make sense to a reader who has not seen this paper.

Good:

`Ratio of hazard rates between treatment and control arms, measuring relative event risk over time.`

Bad:

`A ratio.`

## Step 3: Supplement With Claims-Derived Stragglers When Available

If `claims.yaml` exists, run the supplementary mechanical pass:

```bash
uv run scripts/propose_concepts.py pks-batch "$paper_dir" \
  --registry-dir knowledge/concepts \
  --output "$paper_dir/concepts.auto.yaml"
```

Read `concepts.auto.yaml` and merge in only genuinely missing concepts.

Rules:

- `notes.md` remains the primary authority
- do not overwrite a real definition with an auto placeholder
- use the supplementary pass only to catch stragglers referenced in claims

## Step 4: Write concepts.yaml

Write the merged inventory to:

```bash
"$paper_dir/concepts.yaml"
```

Every entry should start with a real definition, not an auto-generated placeholder.

Verify `form` carefully:

- `ratio` for dimensionless ratios such as hazard ratio, odds ratio, and relative risk
- `rate` for event rates or incidences over time
- `score` for evaluation metrics, p-values, and similar scalar outputs
- `count` for discrete quantities such as sample size or event count
- `structural` for methods, architectures, and abstract methodological concepts
- `category` for discrete condition variables or enumerated states

## Step 5: Ingest Into Propstore

```bash
source_name=$(basename "$paper_dir")
pks source add-concepts "$source_name" --batch "$paper_dir/concepts.yaml"
```

If this fails with `unknown source branch`, stop and run the source bootstrap flow first.

## Step 6: Report

Report:

```text
Concepts registered for: papers/[dirname]
  Notes-derived concepts: N
  Claims-derived stragglers merged: N
  Exact-match links: N
  Newly proposed: N
  Total in concepts.yaml: N
```

If later `add-claim` or auto-finalize reports missing concept references, rerun this skill, add the missing concepts, and ingest again.
