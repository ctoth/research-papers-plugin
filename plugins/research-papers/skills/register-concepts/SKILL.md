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

### local_name vs proposed_name

`local_name` is how this paper refers to the concept. `proposed_name` is what it should be called in the registry. For new concepts these are usually the same. When proposing, `pks source propose-concept` uses `--name` for the local name.

### Granularity Guidance

Concepts ARE: domain-specific measurable quantities (hazard_ratio, event_rate), methodological constructs (cox_proportional_hazards, factorial_design), clinical categories (diabetes_mellitus, peripheral_arterial_disease).

Concepts are NOT: named entities (Scotland, BMJ), specific trial names (POPADAD -- these are category values or source metadata), generic terms (data, result, study).

When in doubt: if two papers could independently measure or define the same thing, it's probably a concept.

### Definition Quality

Good: "Ratio of hazard rates between treatment and control arms, measuring relative event risk over time."

Bad: "A ratio."

## Step 4: Register Concepts One At A Time

For each concept identified in Step 3, run:

```bash
source_name=$(basename "$paper_dir")
pks source propose-concept "$source_name" \
  --name "<local_name>" \
  --definition "<definition>" \
  --form "<form>"
```

Read the output for each concept:

- If output says `Linked '<name>' -> existing '<canonical_name>' (<artifact_id>)`: this concept already exists in the registry. Note the match.
- If output says `Proposed new concept '<name>' (form: <form>)`: this is a new concept being proposed.
- If output says `Unknown form '<form>'`: the form name is wrong. Check `pks form list` and try again with a valid form.

## Step 5: Supplementary Pass (if claims.yaml exists)

If `claims.yaml` exists in the paper directory, read it and check for concept references in the following fields:

- `concept`
- `target_concept`
- `concepts[]`
- `variables[].concept`
- `parameters[].concept`

For any concepts found in `claims.yaml` that were NOT already registered in Step 4, propose them using the same command:

```bash
pks source propose-concept "$source_name" \
  --name "<local_name>" \
  --definition "<definition>" \
  --form "<form>"
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
