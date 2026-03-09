---
name: process-leads
description: Extract all "New Leads" from the paper collection and process them via paper-process. Retrieves and reads papers that other papers in your collection cite but you don't have yet. Use --all to process everything, or pass a number to limit (e.g., "10" for first 10). Papers that fail retrieval are skipped and logged.
argument-hint: "[--all | N]"
disable-model-invocation: false
---

# Process Leads: $ARGUMENTS

Find papers cited as "New Leads" across the collection and retrieve+read them.

## Step 1: Extract All Leads

Use the paper_hash.py script to extract and deduplicate leads, filtering out papers already in the collection:

```bash
python3 $PLUGIN_DIR/scripts/paper_hash.py --papers-dir papers/ extract-leads
```

If `$PLUGIN_DIR` is not set, find the script by searching for it:
```bash
find ~/code -name paper_hash.py -path "*/research-papers/scripts/*" 2>/dev/null | head -1
```

## Step 2: Determine Batch Size

- If `$ARGUMENTS` is `--all`: process every lead
- If `$ARGUMENTS` is a number N: process the first N leads
- If `$ARGUMENTS` is empty: default to 10

## Step 3: Process Each Lead

For each lead, use paper_hash.py to parse the citation and extract a search query:

```bash
python3 $PLUGIN_DIR/scripts/paper_hash.py parse "<lead text>"
```

This gives you author, year, and title. Build a search query from those components for retrieval.

Then invoke the **paper-process** skill:
```
/research-papers:paper-process <search query>
```

If skill invocation is not available, follow the paper-process SKILL.md directly.

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

### Pacing

Process leads **one at a time**, sequentially. Each paper-process invocation may take several minutes (retrieval + reading + reconciliation). Do not parallelize — paper-reader may dispatch its own subagents internally.

## Step 4: Report

Write results to `./reports/process-leads-report.md`:

```markdown
# Process Leads Report

**Date:** [date]
**Leads found:** [total]
**Attempted:** [N]
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
