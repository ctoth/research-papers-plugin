---
name: process-leads
description: Extract all "New Leads" from the paper collection and process them via paper-process. Retrieves and reads papers that other papers in your collection cite but you don't have yet. Use --all to process everything, or pass a number to limit (e.g., "10" for first 10). Papers that fail retrieval are skipped and logged.
argument-hint: "[--all | N]"
disable-model-invocation: false
---

# Process Leads: $ARGUMENTS

Find papers cited as "New Leads" across the collection and retrieve+read them.

## Step 1: Extract All Leads

Scan every `papers/*/notes.md` for the `### New Leads (Not Yet in Collection)` section. Collect every bullet point.

```bash
# Extract leads, skip ones already in the collection
python3 -c "
import os, re

# Build set of what we already have (lowercased directory names)
existing = set()
for d in os.listdir('papers'):
    if os.path.isdir(os.path.join('papers', d)):
        existing.add(d.lower())
        # Also index by components: 'Author', 'Year', key title words
        parts = d.split('_')
        if len(parts) >= 2:
            existing.add(parts[0].lower())  # author surname

# Also check 'Now in Collection' sections to avoid re-processing fulfilled leads
fulfilled = set()
for root, dirs, files in os.walk('papers'):
    if 'notes.md' in files:
        path = os.path.join(root, 'notes.md')
        with open(path, encoding='utf-8') as f:
            text = f.read()
        m = re.search(r'### Now in Collection.*?\n(.*?)(?:\n###|\n## |\Z)', text, re.DOTALL)
        if m:
            for line in m.group(1).strip().split('\n'):
                if '[[' in line:
                    match = re.search(r'\[\[([^\]]+)\]\]', line)
                    if match:
                        fulfilled.add(match.group(1).lower())

leads = []
seen = set()
skipped_existing = 0

for root, dirs, files in os.walk('papers'):
    if 'notes.md' in files:
        path = os.path.join(root, 'notes.md')
        with open(path, encoding='utf-8') as f:
            text = f.read()
        m = re.search(r'### New Leads \(Not Yet in Collection\)\n(.*?)(?:\n###|\n## |\Z)', text, re.DOTALL)
        if m:
            source = os.path.basename(root)
            for line in m.group(1).strip().split('\n'):
                line = line.strip()
                if line.startswith('- '):
                    entry = line[2:].strip()
                    # Deduplicate by rough key (first author + year)
                    key = re.sub(r'[^a-z0-9]', '', entry[:40].lower())
                    if key in seen:
                        continue
                    seen.add(key)

                    # Check if already in collection by matching author surname + year
                    author_match = re.match(r'\*?\*?([A-Z][a-z]+)', entry)
                    year_match = re.search(r'\((\d{4})\)', entry) or re.search(r'(\d{4})', entry)
                    if author_match and year_match:
                        author = author_match.group(1).lower()
                        year = year_match.group(1)
                        # Check if any existing dir starts with this author and contains this year
                        found = False
                        for d in os.listdir('papers'):
                            dl = d.lower()
                            if dl.startswith(author) and year in dl:
                                found = True
                                break
                        if found:
                            skipped_existing += 1
                            continue

                    leads.append((source, entry))

print(f'Total unique leads: {len(leads)}')
print(f'Skipped (already in collection): {skipped_existing}')
print('---')
for source, lead in leads:
    print(f'SOURCE: {source}')
    print(f'LEAD: {lead}')
    print()
" 2>&1
```

## Step 2: Determine Batch Size

- If `$ARGUMENTS` is `--all`: process every lead
- If `$ARGUMENTS` is a number N: process the first N leads
- If `$ARGUMENTS` is empty: default to 10

## Step 3: Process Each Lead

For each lead, extract a search query — the most useful identifier for retrieval:
- If it has a quoted title: use that title
- If it has author + year + description: use "Author Year Title-words"
- Strip annotation text after the em-dash or hyphen (the "why it's relevant" part)

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
