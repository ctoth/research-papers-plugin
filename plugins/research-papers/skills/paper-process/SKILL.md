---
name: paper-process
description: Retrieve a paper, read it, and run the full per-paper propstore ingestion flow through nested skills. Give it a URL, DOI, or title.
argument-hint: "<url-or-doi-or-title>"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Paper Process: $ARGUMENTS

Retrieve one paper, extract the paper artifacts, and run the per-paper propstore ingestion flow.

This is a pure orchestrator. It calls nested skills. It does not inline propstore source-branch mutation commands.

## Execution Discipline

- Follow the steps in order.
- `$ARGUMENTS` names exactly one intended paper.
- If nested skill invocation works on this platform, invoke the named skill directly.
- If nested skill invocation does not work, use the fallback helper and follow its stdout literally.
- Do not substitute custom scripts, alternate workflows, or ad hoc shell sequences for the listed steps.
- If any step is blocked, stop at that step and report the exact blocker.

## Step 1: Retrieve

Invoke:

```text
/research-papers:paper-retriever $ARGUMENTS
```

When retrieval finishes, record the resulting paper path.

## Step 2: Read The Paper

Invoke:

```text
/research-papers:paper-reader <path-from-step-1>
```

When reading finishes, record the resulting paper directory.

## Step 3: Clean Up Root PDF

If the original argument was a local root-level PDF and the paper directory now contains `paper.pdf`, remove the original root-level PDF so the `papers/` root continues to mean "unprocessed PDFs only".

## Step 4: Bootstrap The Source Branch

Invoke:

```text
/research-papers:source-bootstrap <paper-directory-path>
```

## Step 5: Register Concepts

Invoke:

```text
/research-papers:register-concepts <paper-directory-path>
```

This is the notes-first concept pass.

## Step 6: Extract Claims

Invoke:

```text
/research-papers:extract-claims <paper-directory-path>
```

## Step 7: Iterate Concepts And Claims If Needed

If claim ingestion or auto-finalize feedback reports unknown concepts:

1. rerun `register-concepts`
2. rerun `extract-claims`
3. continue until the unknown-concept set is gone

Do not invent a different recovery path. The intended loop is:

- `register-concepts`
- `extract-claims`
- inspect feedback
- repeat if necessary

## Step 8: Extract Justifications

Invoke:

```text
/research-papers:extract-justifications <paper-directory-path>
```

## Step 9: Extract Stances

Invoke:

```text
/research-papers:extract-stances <paper-directory-path>
```

This is per-paper stance extraction against whatever claims already exist in the current knowledge store.

## Step 10: Promote

Invoke:

```text
/research-papers:source-promote <paper-directory-path>
```

## Step 11: Build

If this run is being used as a single-paper ingestion flow rather than a large collection batch, rebuild the sidecar:

```bash
pks build
```

If this run is part of a larger batch orchestrator that will do one final build later, defer the build there instead of rebuilding after every paper.

## Step 12: Report

Write a concise report to `reports/paper-$SAFE_NAME.md` summarizing:

- retrieval result
- reading result
- whether `source-bootstrap` succeeded
- whether `register-concepts` needed reruns
- whether `extract-claims` needed reruns
- whether `extract-justifications` succeeded
- whether `extract-stances` succeeded
- whether `source-promote` succeeded
- whether `pks build` was run or deferred

## Fallback

If direct nested skill invocation is unavailable, use this skill's helper:

```bash
uv run "<skill-dir>/scripts/emit_nested_process_fallback.py"
```

Read the FULL stdout and follow it exactly instead of opening sibling skills piecemeal.
