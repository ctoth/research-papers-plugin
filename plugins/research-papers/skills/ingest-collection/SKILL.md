---
name: ingest-collection
description: Rebuild a knowledge store from a paper collection by running paper-process per paper, then doing one final build and optional stance backfill.
argument-hint: "<papers-directory> [--knowledge-dir <path>]"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Ingest Collection: $ARGUMENTS

Ingest a paper collection into a propstore knowledge store using incremental per-paper processing.

The default path is:

1. ensure the knowledge store exists
2. run `paper-process` for each paper
3. optionally do one enrichment pass such as `extract-stances`
4. run one final `pks build`

## Step 0: Parse And Validate

```bash
papers_dir="$ARGUMENTS"
knowledge_dir="${papers_dir}/../knowledge"
ls "$papers_dir"/*/notes.md | head -20
```

List candidate paper directories and stop if none are present.

## Step 1: Ensure The Knowledge Store Exists

```bash
if [ ! -d "$knowledge_dir/.git" ]; then
  pks init "$knowledge_dir"
fi
```

If the knowledge store already exists, reuse it.
If it does not exist yet, initialize it before processing papers.

## Step 2: Run Paper-Process For Each Paper

For each paper directory, invoke:

```text
/research-papers:paper-process <paper_dir>
```

If subagents are available, run one worker per paper in parallel. If subagents are unavailable, process the papers sequentially.

Each paper is expected to:

- bootstrap its own source branch
- register concepts
- extract claims
- iterate concept and claim repair if needed
- extract justifications
- extract-stances for that paper
- promote itself

There is no collection-wide promote gate before paper-level progress is allowed.

### Parallel Write Recovery

Workers may call `pks` against the same knowledge store concurrently. Treat stale branch-head / compare-and-swap errors as retryable coordination failures, not paper failures.

Retry these exact step failures after a short randomized backoff:

- `StaleHeadError`
- `head mismatch`
- `head changed`
- clean git-store CAS errors that say the expected branch head no longer matches the actual branch head

Retry rule:

1. Re-read the current store state before retrying.
2. If the intended artifact already exists with compatible content, count the step as succeeded.
3. If the intended artifact exists with incompatible content, stop that paper and report the semantic conflict.
4. Otherwise retry the same skill step. Do not delete, reset, or hand-edit artifacts as part of retry.
5. After 5 failed retries of the same step, stop that paper and report the exact last error.

This retry policy applies especially to master-branch steps such as context authoring, predicate authoring, rule authoring, source promotion, and build. Source-branch proposal commands may already retry internally; still report any final stale-head failure with the exact command and paper.

## Step 3: Optional Enrichment Pass

Optional cleanup is allowed after the first full pass.

Examples:

- rerun `extract-stances --all` to backfill cross-paper links that became visible only after later papers were promoted
- review concept inventories or run downstream cleanup that is not a hard gate

This step is optional. Do not treat it as a required second promotion ceremony.

## Step 4: Final Build

After the paper-process wave is complete, run one final build:

```bash
pks build
```

Then verify the resulting store:

```bash
pks world status
```

## Step 5: Report

Write `reports/ingest-collection-report.md` summarizing:

- papers processed
- papers that failed
- whether optional enrichment was run
- whether `extract-stances` backfill was run
- final `pks build` result
- final `pks world status` result

## Error Recovery

- If one paper fails, report the exact paper and error, then decide whether to stop or continue with the remaining papers.
- If optional backfill introduces issues, report that explicitly; it is not the primary ingestion path.
- If the final `pks build` fails, report the exact error and stop there.
