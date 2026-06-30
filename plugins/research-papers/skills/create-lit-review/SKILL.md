---
name: create-lit-review
description: Produce a finished, verified lit-review deliverable from a single invocation by driving the existing /goal loop end to end — research, retrieve, process, write, verify — until every gate passes. Takes a topic and --mode full|intro. Unretrievable papers go to wanted-papers.md and are excluded from citations; the run does not halt.
argument-hint: "\"<topic>\" --mode full|intro"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Create Lit Review: $ARGUMENTS

Produce a complete, verified literature-review deliverable for a topic by **driving the
existing `/goal` command in a loop** until every stage passes. This skill does **not**
reimplement goal-loop control: it defines the goal and the ordered, idempotent pipeline
and hands them to `/goal`, which executes and re-executes until the completion criteria
are met.

- `--mode full` → a standalone literature-review paper.
- `--mode intro` → an Introduction + Related Work section for a paper.

## Goal handed to `/goal`

> A complete, verified lit review on `<topic>` in the deliverable folder: a `<mode>`
> draft plus a self-contained `citations.bibtex` in which **every** cited `@key`
> resolves to a complete, real paper in `papers/`, and all gates (F4, F3, F2,
> `lit_review verify`, `verify-citations`, F7) pass.

Each `/goal` iteration advances the pipeline; the loop ends only when all gates pass
and the deliverable exists. Every stage is **idempotent** (skips already-processed
papers via the `_reader_done.tsv` ledger) so iterations advance rather than redo work.

## Ordered pipeline (each `/goal` iteration)

1. **Research** — `/research-papers:research "<topic>"` → a candidate paper list in
   `reports/`.
2. **Retrieve** — for each candidate, `/research-papers:paper-retriever` (and
   `/research-papers:process-leads` for cited-but-missing works) → PDFs into `papers/`.
   On a retrieval failure, see **Unretrievable papers** below — do not halt.
3. **Process** — `/research-papers:process-new-papers` (parallel where subagents are
   available) → `notes.md` / `abstract.md` / `citations.md` / `metadata.json` per paper.
   For a book source, `/research-papers:book-process` (per-chapter papers).
4. **Corpus gates (block on failure)** — F3 completeness + F4 `dir == cite_key`:
   ```bash
   uv run scripts/lint_paper_schema.py . ; echo "corpus_gate=$?"   # must be 0
   ```
5. **Write** — `/research-papers:write-lit-review --mode <full|intro>` → the draft +
   `citations.bibtex`, citing only `@key`s that resolve to `papers/`.
6. **Deliverable gates (block on failure)** — in order:
   ```bash
   PYTHON=$(command -v python3 || command -v python)
   D="<deliverable-folder>"
   uv run scripts/lit_review.py gate "$D" --papers-dir papers/   ; echo "presence=$?"   # F2
   "$PYTHON" scripts/lit_review.py verify "$D"                    ; echo "verify=$?"
   # verify-citations skill for faithfulness grading on the draft
   uv run scripts/verify_citations_real.py "$D/citations.bibtex" --papers-dir papers/ ; echo "real=$?"  # F7
   ```
7. **Report** — the deliverable path and a one-line status for each gate.

## Loop completion criteria

The `/goal` loop is **done** only when, in one iteration:

- the corpus gate (step 4) exits 0,
- the write step produced a draft + `citations.bibtex`,
- and every deliverable gate (step 6) exits 0.

Any non-zero gate exit keeps the loop iterating (or halts with an actionable message
naming the failing gate and key). **No unverified deliverable is emitted.**

## Unretrievable papers (decided 2026-06-30)

When a candidate paper cannot be retrieved (paywalled / not found), **do not halt and
do not cite it**. Instead:

- Append it to a **`wanted-papers.md`** in the deliverable folder: the title,
  authors/year, and a **link** to the paper so the user can obtain it manually.
- **Exclude** it from `citations.bibtex` and from the written document until it is
  actually obtained and processed.
- Continue the pipeline with the papers that were retrieved.
- On a later re-run, once the user drops the PDF into `papers/`, the loop picks it up,
  processes it, and it becomes eligible for citation.

A `wanted-papers.md` entry never blocks the gates, because excluded papers are not
cited; the F2 presence gate only checks keys that actually appear in the draft.

## Re-running

Re-running on the same topic **resumes**: already-processed papers are skipped (the
ledger), and any newly-obtained `wanted-papers.md` PDFs are processed and become
citable. This is why every stage must stay idempotent.

## Do NOT:

- Reimplement the `/goal` loop — define the goal + steps and call `/goal`.
- Cite a paper recorded in `wanted-papers.md` (it was never retrieved/processed).
- Emit the deliverable while any gate is non-zero.
