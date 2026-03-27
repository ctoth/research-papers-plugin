---
name: process-leads
description: >-
  Extract all "New Leads" from the paper collection and process them via
  paper-process. Retrieves and reads papers that other papers in your collection
  cite but you don't have yet. Use --all to process everything, or pass a number
  to limit (e.g., "10" for first 10). Add --parallel N to process N leads
  concurrently via subagents (default: sequential).
argument-hint: "[--all | N] [--parallel M]"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI. Subagents are optional but recommended for throughput."
---

# Process Leads: $ARGUMENTS

Find papers cited as "New Leads" across the collection and retrieve+read them.

## Execution Discipline

This skill is a checklist, not an outcome sketch.

- Follow the steps in order.
- Do not add retrieval heuristics, ranking schemes, batching logic, or alternate workflows beyond what this skill specifies.
- If you can invoke the named nested skill, do that. If you cannot, use the fallback helper below and follow its stdout literally.
- If you are blocked on a specific step, stop there and report the exact blocker instead of inventing a workaround.

## Script Paths

The command examples below use `scripts/...` paths that are relative to this skill's directory. Resolve them against the installed skill location, not the user's project root.

## Step 1: Extract All Leads

There are two lead-discovery modes. Use **both** and merge results (deduplicating by author+year).

### Mode A: Notes-based leads (existing behavior)

Extract leads from "New Leads" sections in notes.md files:

```bash
python3 scripts/paper_hash.py --papers-dir papers/ extract-leads
```

### Mode B: Citation-graph leads (new)

If `$ARGUMENTS` contains `--citations` or `--citations-from <identifier>`, also discover leads via Semantic Scholar citation graph:

```bash
uv run scripts/get_citations.py <identifier> --direction references --filter-existing --papers-dir papers/ --json
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
python3 scripts/paper_hash.py parse "<lead text>"
```

Then classify each lead:

- **Likely available:** Has a title that sounds like a journal/conference paper, year after ~1990
- **Unlikely available:** Books (keywords: "Knowledge in Flux", "The Uses of Argument", "Introduction to..."), technical reports/deliverables, dissertations, pre-1985 papers without DOIs

**Process likely-available leads first.** Defer unlikely leads to the end of the batch. If the batch limit (N) is reached before getting to unlikely leads, that's fine — they go in the "Remaining" section of the report. Don't waste retrieval attempts on leads that will almost certainly fail when there are good leads waiting.

## Step 3: Process Leads

For each lead, build a search query from the parsed author, year, and title components.

Before dispatching a lead, normalize it to one concrete intended paper. Prefer:

1. DOI
2. ACL Anthology ID/URL
3. arXiv ID/URL
4. S2 paper ID
5. exact paper title

Do not dispatch weak landing-page URLs when the title or a stronger identifier is already available. One dispatch must correspond to one intended paper.

### Always Use Subagents

**Every paper-process invocation should run as a subagent when subagent dispatch is available**, even in sequential mode. This protects the foreman's context window from the large volume of page-reading output that paper-process generates. Use the strongest available full-size model for every such worker. Never use a mini/small/flash tier model for workers that will retrieve or read papers. If subagents are unavailable, process leads yourself one at a time and keep external notes so you do not lose state.

### Subagent Prompt Template

Read the sibling paper-process SKILL.md once (`../paper-process/SKILL.md`, relative to this skill) and use it as the base prompt for all subagents. Each subagent prompt should include:

1. The paper-process SKILL.md instructions
2. The exact intended paper for that lead, plus the normalized identifier or exact title the worker should use
3. Instructions to write a per-paper report to `./reports/paper-<safe-name>.md`
4. **Instructions to SKIP reconcile (Step 7) and index.md update (Step 8)** — the foreman handles these after each agent completes
5. A reminder that any nested paper-reading delegation must stay on the strongest available full-size model and must not downgrade to a mini/small tier
6. A reminder that if retrieval resolves to a different paper than the intended lead, the worker must stop and report mismatch

**Do NOT use worktree isolation.** Paper-process writes to shared state (papers/index.md, cross-references in existing papers' notes.md via reconcile). Worktrees strand all of that with no clean merge path.

If nested skill invocation is unavailable or unreliable on this platform, do not rely on
paper-process dispatch. Instead, derive this skill's installed directory from the injected
`<path>`, then run:

```bash
python "<skill-dir>/../paper-process/scripts/emit_nested_process_fallback.py"
```

Read the FULL stdout and follow it exactly for each lead instead of opening
`paper-process/SKILL.md` piecemeal.

### Sequential Mode (default)

Process one lead at a time. Dispatch one subagent for each lead, wait for it to complete, then run reconcile + index.md update yourself (or via another strongest-available full-size subagent if you must delegate), then dispatch the next lead. If subagents are unavailable, process the lead yourself, then reconcile and update index.md before moving on. In the no-nested-skill fallback above, let the paper-process helper complete the full paper workflow and then do only any additional verification you still need before moving on.

### Parallel Mode (--parallel M)

Dispatch up to M leads concurrently using whatever subagent mechanism your platform provides.
Use the strongest available full-size model for every paper-processing worker in the wave. Do not use mini/small/flash tiers for paper retrieval or extraction.

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
