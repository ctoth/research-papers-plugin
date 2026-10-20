---
name: verify-citations
description: Grade a drafted literature review against the cited papers' notes. For each cited @key, read that paper's notes.md/abstract.md and grade whether the citing sentence is faithful. Fans out one subagent per cited paper.
argument-hint: "<draft.md> [--papers-dir papers/]"
disable-model-invocation: false
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
parallel) with the paper's `notes.md` and `abstract.md`, **the path to its `pngs/`
directory**, plus the exact citing sentence(s). Each subagent grades the claim against
the source and returns a verdict.

The `pngs/` path is required, not optional. `notes.md` is itself a transcription and
can carry a wrong number; grading a citing sentence only against the notes cannot
detect that, and would grade a fabricated figure as SUPPORTED.

## Step 3: Grading rubric

Grade each citing sentence as exactly one verdict:

- **SUPPORTED** — the cited paper directly states what the sentence claims.
- **PARTIAL** — the paper supports part of the claim but the sentence overstates,
  over-scopes, or omits a material qualifier.
- **UNSUPPORTED** — the paper does not say this; no passage backs the claim.
- **MISATTRIBUTED** — the paper is about something materially different (wrong
  task, wrong direction, wrong finding), or the wrong paper is cited.
- **NUMERIC_MISMATCH** — the sentence's number disagrees with the source. Takes
  precedence over the other four: a sentence whose prose is faithful but whose figure
  is wrong is a worse error than one that merely overstates, because it reads as
  precise.

For each, return a verbatim supporting (or contradicting) snippet from the source
and a proposed wording fix.

### Numeric claims are graded against the page image (MANDATORY)

Whenever a citing sentence contains a number — effect size, p-value, CI, sample size,
percentage, threshold, accuracy — the grading subagent must:

1. Find that number in `notes.md` and note its page citation.
2. Open `pngs/page-{(N-1):03d}.png` and read the number off the page itself.
3. Grade the citing sentence against **the page image**, not against `notes.md`.

Report `NUMERIC_MISMATCH` when:

- the drafted sentence's number differs from the page, **or**
- `notes.md` and the page image disagree — flag this explicitly as a notes defect, not
  just a draft defect, since the wrong figure will otherwise stay in the collection, **or**
- the number appears in `notes.md` with no page citation, or with a citation to a page
  that does not contain it. Treat this as a suspected fabrication in the source notes
  and say so in the report.

A number that cannot be found on any page of the cited paper is `UNSUPPORTED`
regardless of how well the surrounding prose matches.

## Step 4: Report

Emit a per-claim report (key, verdict, snippet, fix) using the
`verify_citations.render_report` schema. Flag every PARTIAL / UNSUPPORTED /
MISATTRIBUTED verdict for the author to resolve. Requires the reliable
`cite_key` -> directory mapping from the keymap.
