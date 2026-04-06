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

## Step 3: Report

Report:

- how many PDFs were found
- which ones were sent to `paper-process`
- whether any root-level PDFs remain
