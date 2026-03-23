---
name: process-leads
description: Extract all "New Leads" from the paper collection and process them via paper-process. Retrieves and reads papers that other papers in your collection cite but you don't have yet. Use --all to process everything, or pass a number to limit (e.g., "10" for first 10). Add --parallel N to process N leads concurrently via subagents (default: sequential).
argument-hint: "[--all | N] [--parallel M]"
disable-model-invocation: false
---

# Process Leads: $ARGUMENTS

Find papers cited as "New Leads" across the collection and retrieve+read them.

## Step 1: Extract All Leads

There are two lead-discovery modes. Use **both** and merge results (deduplicating by author+year).

### Mode A: Notes-based leads (existing behavior)

Extract leads from "New Leads" sections in notes.md files:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/paper_hash.py --papers-dir papers/ extract-leads
```

### Mode B: Citation-graph leads (new)

If `$ARGUMENTS` contains `--citations` or `--citations-from <identifier>`, also discover leads via Semantic Scholar citation graph:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/get_citations.py <identifier> --direction references --filter-existing --papers-dir papers/ --json
```

Where `<identifier>` is an arxiv ID or DOI of a paper already in the collection. If `--citations-from` is not specified but `--citations` is, pick the most recently added paper (by directory mtime).

This gets the actual reference list from S2 rather than relying on what paper-reader chose to highlight. Merge these with Mode A leads, deduplicating by author surname + year.

## Step 2: Determine Batch Size and Parallelism

**Count (how many leads to attempt):**
- If `$ARGUMENTS` contains `--all`: no cap — process leads wave by wave until the session ends naturally (context limit, user stops you, etc.). You do NOT need to finish all leads in one session. `--all` just means "don't stop after N, keep going."
- If `$ARGUMENTS` contains a number N (not after `--parallel`): process the first N leads
- If neither: default to 10

**Parallelism (how many at once):**
- If `$ARGUMENTS` contains `--parallel M`: process M leads concurrently via subagents
- If no `--parallel` flag: process sequentially (one at a time)

## Step 2.5: Triage Leads

Before processing, sort leads by retrieval likelihood. Parse ALL leads with paper_hash.py first:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/paper_hash.py parse "<lead text>"
```

Then classify each lead:

- **Likely available:** Has a title that sounds like a journal/conference paper, year after ~1990
- **Unlikely available:** Books (keywords: "Knowledge in Flux", "The Uses of Argument", "Introduction to..."), technical reports/deliverables, dissertations, pre-1985 papers without DOIs

**Process likely-available leads first.** Defer unlikely leads to the end of the batch. If the batch limit (N) is reached before getting to unlikely leads, that's fine — they go in the "Remaining" section of the report. Don't waste retrieval attempts on leads that will almost certainly fail when there are good leads waiting.

## Step 3: Process Leads

For each lead, build a search query from the parsed author, year, and title components.

### Always Use Subagents

**Every paper-process invocation runs as a subagent**, even in sequential mode. This protects the foreman's context window from the large volume of page-reading output that paper-process generates. Without subagents, processing 3-4 papers fills the context window and forces compaction, losing earlier work.

### Subagent Prompt Template

Read the paper-process SKILL.md once (`${CLAUDE_PLUGIN_ROOT}/skills/paper-process/SKILL.md`) and use it as the base prompt for all subagents. Each subagent prompt should include:

1. The paper-process SKILL.md instructions
2. The specific search query for that lead
3. Instructions to write a per-paper report to `./reports/paper-<safe-name>.md`
4. **Instructions to SKIP reconcile (Step 7) and index.md update (Step 8)** — the foreman handles these after each agent completes

**Do NOT use worktree isolation.** Paper-process writes to shared state (papers/index.md, cross-references in existing papers' notes.md via reconcile). Worktrees strand all of that with no clean merge path.

### Sequential Mode (default)

Process one lead at a time. Dispatch a **general-purpose Agent** for each lead, wait for it to complete, then run reconcile + index.md update yourself (or via a small subagent), then dispatch the next lead.

### Parallel Mode (--parallel M)

Dispatch up to M leads concurrently using the **Agent tool**.

**Batch processing:** Process in waves of M agents. Dispatch a wave, wait for all to complete, run reconcile + update index.md for each new paper from the wave, then dispatch the next wave. The session will naturally end at some point (context limit, user intervention) — that's fine. The report captures progress so the next session can pick up where you left off.

### Handling Failures

Paper-process will fail on some leads. This is expected and fine. Common reasons:
- Books (no PDF available)
- Old papers not digitized
- Paywalled without sci-hub access
- Ambiguous title

When a lead fails retrieval:
1. Log it in the report as "SKIP: [lead] — [reason]"
2. Move to the next lead
3. Do NOT retry or try alternative sources

## Step 4: Report

Write results to `./reports/process-leads-report.md`:

```markdown
# Process Leads Report

**Date:** [date]
**Leads found:** [total]
**Attempted:** [N]
**Parallelism:** [M or "sequential"]
**Succeeded:** [count]
**Failed:** [count]

## Succeeded
| # | Lead | Paper Directory |
|---|------|----------------|
| 1 | [original lead text] | papers/Author_Year_Title/ |

## Failed
| # | Lead | Reason |
|---|------|--------|
| 1 | [original lead text] | [retrieval failed / book / etc] |

## Remaining (not attempted)
[count] leads not attempted. Run again with a higher N or --all.
```
