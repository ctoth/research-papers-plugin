---
name: verify-citations
description: Grade a drafted literature review against the cited papers' notes. For each cited @key, read that paper's notes.md/abstract.md and grade whether the citing sentence is faithful. Fans out one subagent per cited paper.
argument-hint: "<draft.md> [--papers-dir papers/]"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Verify Citations: $ARGUMENTS

Grade every claim in a drafted review against what the cited papers actually say.
The notes layer exists to be written from; this is the check that catches
substantive misattribution and misreading before a draft ships.

## Step 1: Extract and resolve citations

```bash
PYTHON=$(command -v python3 || command -v python)
"$PYTHON" scripts/verify_citations.py extract "$DRAFT"
"$PYTHON" scripts/verify_citations.py resolve "$DRAFT" --papers-dir papers/
```

`resolve` maps each `@key` to its paper directory via `papers/keymap.tsv`. Any
`UNRESOLVED` key is a blocker: fix the keymap (`build_keymap.py`) or the citation
before grading.

## Step 2: Fan out one subagent per cited paper

For each cited paper, dispatch **one subagent** (one subagent per cited paper, in
parallel) with the paper's `notes.md` and `abstract.md` plus the exact citing
sentence(s). Each subagent grades the claim against the source and returns a
verdict.

## Step 3: Grading rubric

Grade each citing sentence as exactly one verdict:

- **SUPPORTED** — the cited paper directly states what the sentence claims.
- **PARTIAL** — the paper supports part of the claim but the sentence overstates,
  over-scopes, or omits a material qualifier.
- **UNSUPPORTED** — the paper does not say this; no passage backs the claim.
- **MISATTRIBUTED** — the paper is about something materially different (wrong
  task, wrong direction, wrong finding), or the wrong paper is cited.

For each, return a verbatim supporting (or contradicting) snippet from the source
and a proposed wording fix.

## Step 4: Report

Emit a per-claim report (key, verdict, snippet, fix) using the
`verify_citations.render_report` schema. Flag every PARTIAL / UNSUPPORTED /
MISATTRIBUTED verdict for the author to resolve. Requires the reliable
`cite_key` -> directory mapping from the keymap.
