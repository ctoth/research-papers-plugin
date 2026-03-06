---
name: paper-process
description: Retrieve a paper and extract implementation-focused notes. Combines paper-retriever and paper-reader into one step. Give it a URL, DOI, or title.
argument-hint: "<url-or-doi-or-title>"
disable-model-invocation: false
---

# Paper Process: $ARGUMENTS

Download a scientific paper and extract structured notes in one shot.

## Step 1: Retrieve the Paper

Invoke the **paper-retriever** skill with: `$ARGUMENTS`

If skill invocation is available (e.g., `/research-papers:paper-retriever`), use it. Otherwise, follow the paper-retriever SKILL.md instructions directly.

When retrieval completes, note the output path (e.g., `papers/Author_Year_ShortTitle/paper.pdf`).

## Step 2: Read and Extract Notes

Invoke the **paper-reader** skill with the path from Step 1.

If skill invocation is available (e.g., `/research-papers:paper-reader`), use it. Otherwise, follow the paper-reader SKILL.md instructions directly.

Follow all instructions through to completion (notes.md, description.md, abstract.md, citations.md, AGENTS.md update).

## Step 3: Clean Up Source PDF

If the original argument was a local file path (e.g., `papers/somefile.pdf` in the root of `papers/`), and the paper directory now contains `paper.pdf`, **delete the original root-level PDF**:

```bash
# Only if the source was a local file and the paper dir copy exists
rm "./papers/somefile.pdf"
```

This keeps the `papers/` root clean — any PDF still in the root is unprocessed. Do NOT delete if the source was a URL (nothing to clean up) or if the paper directory doesn't have `paper.pdf` yet (something went wrong).

## Step 4: Report

When both skills have completed, write a summary to `./reports/paper-$SAFE_NAME.md` where $SAFE_NAME is derived from the paper directory name. Include:

- Paper directory path
- Whether retrieval succeeded (and source: arxiv/sci-hub/etc.)
- Whether reading succeeded
- Usefulness rating for this project

## Error Handling

- If retrieval fails: report failure and stop. Do not proceed to reading.
- If reading fails: report what was retrieved but note the reading failure.
