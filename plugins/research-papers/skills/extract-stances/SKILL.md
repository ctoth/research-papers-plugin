---
name: extract-stances
description: Extract inter-claim stances and author them through pks source propose-stance.
argument-hint: "<papers/Author_Year_Title> [--cluster paper1,paper2,...] or --all"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Extract Stances: $ARGUMENTS

Extract argumentative relationships between already-authored claims and write them directly to propstore with `pks source propose-stance`. Do not create or ingest stance batch files.

## Stance Types

- `supports` — corroborating evidence.
- `explains` — mechanistic or causal explanation.
- `rebuts` — direct conflict with the target conclusion.
- `undermines` — attacks a premise or evidence quality.
- `undercuts` — attacks the inference or methodology.
- `supersedes` — replaces the target because it is newer, larger, longer, or corrects an error.

## Step 0: Determine Mode

Parse `$ARGUMENTS`:

```bash
if [[ "$ARGUMENTS" == "--all" ]]; then
  ls -d papers/*/ | grep -v "papers/pngs\|papers/tagged" | sort
else
  paper_dir="$ARGUMENTS"
  source_name=$(basename "$paper_dir")
fi
```

For `--all`, process each paper source one at a time. Do not run concurrent stance writes against the same source.

## Step 1: Load Claim Context

Read:

- The target paper's `notes.md`, especially discussion, collection cross-references, open questions, and cited-prior-work passages.
- Other papers' `notes.md` where a proposed target relationship depends on cross-paper evidence.
- Current source-branch claim ids. Local source claims are referenced as `claim7`; cross-source targets are referenced as `OtherPaperDir:claim7`.

Do not stance claims in the same paper when the relation is really an intra-paper inference; use `extract-justifications` for that.

### Cross-source boundary

When extracting stances for one source, the current source is the only mutable source.

- Do not run `pks source finalize`, `pks source promote`, `pks source propose-*`, or any other mutation command for another paper source.
- Do not "fix up" another paper so a target claim becomes available.
- If a cross-source target is not already resolvable by `pks source propose-stance`, skip that stance and report it as unavailable.
- It is acceptable to read another paper's notes and already-promoted claim artifacts to choose a target.
- It is acceptable to finalize the current source only if the local claims must be resolvable before writing stances.

## Step 2: Propose Stances Through pks

Use one command per stance:

```bash
pks source propose-stance "$source_name" \
  --source-claim claim3 \
  --target OtherPaper_2024_RelatedFinding:claim11 \
  --type supports \
  --strength strong \
  --note "Independent replication of a comparable null result."
```

Rules:

- `--source-claim` is a local claim id from the current source.
- `--target` is either a local claim id or `PaperDirName:claimID` for another source.
- `--type` must be one of the stance types above.
- Always include `--note` with the textual or structural reason for the stance.
- `pks source propose-stance` resolves local source claims and rejects unresolved local references before writing.

## Step 3: Report

```text
Stances extracted for: papers/[dirname]
  Stances proposed: N total
  supports: X
  rebuts: X
  undercuts: X
  undermines: X
  explains: X
  supersedes: X
  Cross-paper links: N
  Validation boundary: pks source propose-stance
```
