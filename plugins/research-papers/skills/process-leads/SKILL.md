---
name: process-leads
description: Extract all "New Leads" from the paper collection and process them via paper-process. Retrieves and reads papers that other papers in your collection cite but you don't have yet. Use --all to process everything, or pass a number to limit (e.g., "10" for first 10). Add --parallel N to process N leads concurrently via subagents (default: sequential).
argument-hint: "[--all | N] [--parallel M]"
disable-model-invocation: false
---

# Process Leads: $ARGUMENTS

Find papers cited as "New Leads" across the collection and retrieve+read them.

## Step 1: Extract All Leads

Use the paper_hash.py script to extract and deduplicate leads, filtering out papers already in the collection:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/paper_hash.py --papers-dir papers/ extract-leads
```

## Step 2: Determine Batch Size and Parallelism

**Count (how many leads to attempt):**
- If `$ARGUMENTS` contains `--all`: process every lead
- If `$ARGUMENTS` contains a number N (not after `--parallel`): process the first N leads
- If neither: default to 10

**Parallelism (how many at once):**
- If `$ARGUMENTS` contains `--parallel M`: process M leads concurrently via subagents
- If no `--parallel` flag: process sequentially (one at a time)

## Step 3: Process Leads

For each lead, use paper_hash.py to parse the citation and extract a search query:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/paper_hash.py parse "<lead text>"
```

This gives you author, year, and title. Build a search query from those components for retrieval.

### Sequential Mode (default)

Process one lead at a time. For each lead, invoke **paper-process**:
```
/research-papers:paper-process <search query>
```

If skill invocation is not available, follow the paper-process SKILL.md directly.

### Parallel Mode (--parallel M)

Dispatch up to M leads concurrently using the **Agent tool**. Each agent is independent and gets its own lead to process.

**Important:** Parse ALL leads with paper_hash.py BEFORE dispatching agents. The parsing step is fast and should be done in the main conversation to build the full work list.

**Do NOT use worktree isolation.** Paper-process writes to shared state (papers/index.md, cross-references in existing papers' notes.md via reconcile). Worktrees strand all of that with no clean merge path.

Instead, split the work: agents do retrieval + reading (the slow part), the foreman does shared-state writes (the fast part that needs consistency).

**For each agent, the prompt should include:**
1. The paper-process SKILL.md instructions (read from `${CLAUDE_PLUGIN_ROOT}/skills/paper-process/SKILL.md`)
2. The specific search query for that lead
3. Instructions to write a per-paper report to `./reports/paper-<safe-name>.md`
4. **Instructions to SKIP Steps 7.5 (reconcile) and 8 (index.md update)** — the foreman handles these after each wave

**Batch processing:** If there are more leads than the parallel limit M, process in waves — dispatch M agents, wait for all to complete, then dispatch the next M.

**After each wave completes**, the foreman dispatches a single subagent (NOT in a worktree) to run reconcile and update index.md for each new paper from the wave, sequentially. Wait for this subagent to finish before dispatching the next wave. This keeps shared-state writes sequential, consistent, and avoids burning the foreman's context on reconcile output.

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
