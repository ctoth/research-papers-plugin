---
name: extract-justifications
description: Extract intra-paper justification structure and author it through pks source propose-justification.
argument-hint: "<papers/Author_Year_Title>"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Extract Justifications: $ARGUMENTS

Extract the intra-paper argumentative structure: which already-authored source claims serve together as premises for which conclusions. Author justifications directly through `pks source propose-justification`; do not create or ingest justification batch files.

## What Justifications Are

A justification is a directed hyperedge: a set of premise claims that together support or attack a conclusion claim through a typed inference rule. Stances are inter-claim edges across papers; justifications are intra-paper reasoning structure.

Rule kinds:

- `empirical_support`
- `causal_explanation`
- `methodological_inference`
- `statistical_inference`
- `definition_application`
- `scope_limitation`
- `comparison_based_inference`
- `reported_claim`
- `supports`
- `explains`

## Step 0: Validate

```bash
paper_dir="$ARGUMENTS"
source_name=$(basename "$paper_dir")
ls "$paper_dir"/notes.md 2>/dev/null || echo "MISSING: notes.md"
ls knowledge/.git 2>/dev/null || echo "MISSING: knowledge/.git"
pks source finalize "$source_name" 2>&1 || true
```

- `notes.md` missing -> STOP. Run `paper-reader` first.
- Source branch missing -> STOP. Run `source-bootstrap`, `register-concepts`, and `extract-claims` first.

## Step 1: Read Source Material

Read:

- `<paper_dir>/notes.md` for the paper's stated reasoning.
- The already-authored source claims for this source branch. Use local claim ids such as `claim1` when referencing conclusions and premises.
- Page images for provenance when exact wording or page numbers matter.

Do not fabricate reasoning links. If the paper states a result without connecting it to another claim, leave it isolated.

## Step 2: Propose Justifications Through pks

Use one command per inferential step:

```bash
pks source propose-justification "$source_name" \
  --id just1 \
  --conclusion claim12 \
  --premises claim3,claim8 \
  --rule-kind statistical_inference \
  --rule-strength defeasible \
  --page 14 \
  --section "Results" \
  --quote-fragment "Brief supporting quote"
```

Attack-target structure, when the paper explicitly gives rebuttal/undercut/undermine reasoning:

```bash
pks source propose-justification "$source_name" \
  --id just2 \
  --conclusion claim18 \
  --premises claim16,claim17 \
  --rule-kind comparison_based_inference \
  --attack-target-claim claim12 \
  --attack-target-justification-id just1 \
  --attack-target-premise-index 0 \
  --page 21
```

Rules:

- `--conclusion` must be a local claim id already authored on this source.
- `--premises` is a comma-separated list of local claim ids from this source.
- Do not include the conclusion in its own premise list.
- Use one inferential step per justification; chains get multiple justifications.
- Reusing a justification id updates that source-local justification.
- `pks source propose-justification` resolves local claim ids and rejects unresolved references before writing.
- Use `--rule-strength strict` only for definitional or mathematical entailment. Use `defeasible` for empirical or methodological support.
- Attack-target fields are optional. Use them only when the paper identifies the target claim, target justification, or target premise being attacked.

## Step 3: Report

```text
Justifications extracted for: papers/[dirname]
  Justifications proposed: N total
  Rule kinds used: [...]
  Validation boundary: pks source propose-justification
```
