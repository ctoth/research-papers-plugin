---
name: ingest-new-papers
description: Process all unprocessed PDFs in papers/ through the full paper-process workflow.
argument-hint: ""
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Ingest New Papers

Find all root-level PDFs in `papers/` and process each one through `paper-process`.

## Step 1: List Unprocessed PDFs

```bash
ls papers/*.pdf 2>/dev/null
```

If none are present, report `No unprocessed papers found` and stop.

## Step 2: Process Each PDF Through Paper-Process

For each PDF found, invoke:

```text
/research-papers:paper-process papers/filename.pdf
```

If subagents are available, parallelize by paper. If subagents are unavailable, process the PDFs sequentially.

## Step 3: Completeness gate (REQUIRED — F3)

Before reporting the wave done, run the mechanical completeness gate over the
collection. It exits non-zero (2) if any paper is incomplete:

```bash
# Run from the collection root (the directory containing papers/).
uv run scripts/lint_paper_schema.py .
echo "exit=$?"   # 0 = complete, 2 = BLOCKED: repair the flagged papers and re-run
```

A non-zero exit is a **hard blocker** — repair each flagged paper (missing required
file, or `abstract.md` lacking its verbatim/interpretation sections) and re-run until
it exits 0.

## Step 4: Report

Report:

- how many PDFs were found
- which ones were sent to `paper-process`
- whether any root-level PDFs remain
