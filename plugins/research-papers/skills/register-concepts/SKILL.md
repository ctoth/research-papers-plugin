---
name: register-concepts
description: Register concepts needed by a paper into a propstore source branch. Runs propose_concepts.py to extract concept inventory from claims, then enriches definitions via notes.md, and calls pks source add-concepts.
argument-hint: "<papers/Author_Year_Title>"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Register Concepts: $ARGUMENTS

Register all concepts needed by a paper into its propstore source branch. This must run after extract-claims (needs claims.yaml) and after `pks source init` has created the source branch.

## Step 0: Validate

```bash
paper_dir="$ARGUMENTS"
ls "$paper_dir"/notes.md 2>/dev/null || echo "MISSING: notes.md"
ls "$paper_dir"/claims.yaml 2>/dev/null || echo "MISSING: claims.yaml"
```

If `notes.md` is missing → STOP, run paper-reader first.
If `claims.yaml` is missing → STOP, run extract-claims first.

## Step 1: Check Propstore State

```bash
ls knowledge/.git 2>/dev/null
pks source --help 2>/dev/null | head -20
```

If no `knowledge/` directory exists → STOP. Report: "No propstore found. Run `pks init` first."

## Step 2: Mechanical Concept Extraction

Run the concept proposer to extract all concept names from this paper's claims.yaml:

```bash
uv run scripts/propose_concepts.py pks-batch "$paper_dir" \
  --registry-dir knowledge/concepts \
  --output "$paper_dir/concepts.yaml"
```

Read the output `concepts.yaml`. It will have entries like:
```yaml
concepts:
  - local_name: "hazard_ratio"
    proposed_name: "hazard_ratio"
    definition: "Auto-proposed from 5 claim(s)."
    form: "structural"
```

## Step 3: Enrich Definitions

The auto-generated definitions are placeholders. For each concept in `concepts.yaml`:

1. Read the paper's `notes.md` to find how this concept is described
2. Replace the placeholder definition with a 1-2 sentence definition that:
   - Distinguishes this concept from near-neighbors
   - Would make sense to someone unfamiliar with this specific paper
   - Is specific enough to match against similar concepts in other papers

Good: "Ratio of hazard rates between treatment and control arms, measuring the relative risk of an event occurring in the intervention group."
Bad: "A ratio."

3. Verify the `form` is correct:
   - `ratio` for dimensionless ratios (hazard ratio, odds ratio, rate ratio, relative risk)
   - `rate` for event rates (events per person-year, incidence rate)
   - `score` for evaluation metrics, p-values, absolute risk differences
   - `count` for discrete quantities (person-years, sample size)
   - `structural` for methods, architectures, abstract concepts
   - `category` for condition variables with enumerated values

4. Write the enriched `concepts.yaml` back to disk.

## Step 4: Ingest into Propstore

```bash
source_name=$(basename "$paper_dir")
pks source add-concepts "$source_name" --batch "$paper_dir/concepts.yaml"
```

If this fails with "unknown source branch", the source branch hasn't been initialized. Run:
```bash
# See paper-process skill for full init sequence
pks source init "$source_name" --kind academic_paper --origin-type doi --origin-value "<doi>"
```

## Step 5: Report Alignment

After add-concepts, check which concepts exact-matched existing canonical names vs which remain newly proposed:

```
Concepts registered for: papers/[dirname]
  Exact-match links: N (list names)
  Newly proposed: N (list names)
  Total in concepts.yaml: N
```

Newly proposed concepts will need alignment decisions after all papers are finalized.
