---
name: paper-reader
description: Read scientific papers and extract implementation-focused notes. Converts PDFs to page images, then reads them. Papers <=50pp are read directly; papers >50pp are chunked into 50-page ranges for thorough parallel extraction. Creates structured notes in papers/ directory.
argument-hint: "[path/to/paper.pdf]"
disable-model-invocation: false
---

# Paper Reader: $ARGUMENTS

Read a scientific paper and create comprehensive implementation-focused notes.

## Step 0: Check for Existing Paper

If the argument is a directory, use it directly. If it's a PDF file, use `paper_hash.py lookup` to find a matching paper directory:

```bash
paper_path="$ARGUMENTS"
if [ -d "$paper_path" ]; then
  paper_dir="$paper_path"
elif [ -f "$paper_path" ]; then
  HASH_SCRIPT="${CLAUDE_PLUGIN_ROOT}/scripts/paper_hash.py"
  if [ -f "$HASH_SCRIPT" ]; then
    paper_dir=$(python3 "$HASH_SCRIPT" --papers-dir papers/ lookup "$(basename "$paper_path" .pdf)" 2>/dev/null)
    [ $? -ne 0 ] && paper_dir=""
    [ -n "$paper_dir" ] && paper_dir="papers/$paper_dir"
  else
    basename=$(basename "$paper_path" .pdf)
    paper_dir=$(ls -d papers/*/ 2>/dev/null | grep -i "${basename%_*}" | head -1)
  fi
fi
```

### Case A: No existing directory found
Continue to Step 1.

### Case B: Directory exists — check gaps

```bash
ls -la "$paper_dir"/*.md 2>/dev/null
ls "$paper_dir"/pngs/ 2>/dev/null | head -3
ls "$paper_dir"/*.pdf 2>/dev/null | head -1
```

- **No `notes.md`?** Incomplete — continue to Step 1.
- **All files present (notes + abstract + citations)?** Delete root PDF if argument was a root-level file (`rm "$paper_path"`), report "Already complete," stop.
- **Missing abstract.md and/or citations.md?** Fill gaps using page images or PDF, then delete root PDF and stop. See Steps 5-6 for format.

---

## Step 1: Determine Paper Size and Convert

Get page count:
```bash
pdfinfo "$ARGUMENTS" 2>/dev/null | grep Pages || echo "pdfinfo not available"
```

**Always convert to page images.** Extract page 0 first in a temp dir for metadata:

```bash
tmpdir=$(mktemp -d)
magick -density 150 "$ARGUMENTS[0]" -quality 90 -resize '1960x1960>' "$tmpdir/page0.png"
```

Read `$tmpdir/page0.png` to extract author, year, title. Determine directory name: `LastName_Year_2-4WordTitle` (e.g., `Mack_2021_AccessibilityResearchSurvey`).

Create output directory and convert all pages:
```bash
mkdir -p "./papers/Author_Year_ShortTitle/pngs"
mv "$ARGUMENTS" "./papers/Author_Year_ShortTitle/paper.pdf"  # MUST be mv, NEVER cp
magick -density 150 "./papers/Author_Year_ShortTitle/paper.pdf" -quality 90 -resize '1960x1960>' "./papers/Author_Year_ShortTitle/pngs/page-%03d.png"
rm -rf "$tmpdir"
```

**CRITICAL: Use `mv`, NEVER `cp`.** The root-level PDF must be removed. A PDF left in `papers/` root is indistinguishable from an unprocessed paper.

**CRITICAL: Never write temp files to `papers/` root.** Use `mktemp -d` for temp work.

Count pages:
```bash
ls ./papers/Author_Year_ShortTitle/pngs/page-*.png | wc -l
```

**Decision:**
- **≤50 pages**: Read all page images yourself (Step 2A)
- **>50 pages**: Chunk protocol (Step 2B)

---

## Step 2A: Direct Read (≤50 pages)

Read every page image sequentially. Take thorough notes — you have the context for it. Continue to Step 3.

---

## Step 2B: Chunk Protocol (>50 pages)

Split into **50-page chunks**. Calculate ranges:
- Chunk 1: pages 000-049
- Chunk 2: pages 050-099
- Last chunk: whatever remains

### Write ONE Template Prompt

Write to `./prompts/paper-chunk-reader.md`:

```markdown
# Task: Read Paper Chunk and Extract Notes

## Context
You are reading a chunk of [PAPER TITLE] being processed in parallel.
Page images: `./papers/Author_Year_ShortTitle/pngs/page-NNN.png`

## Your Chunk
**START_PAGE** to **END_PAGE** (inclusive)

Read each page image in your range. Be exhaustive — extract EVERY equation, parameter, algorithm step, and implementation detail. Do not summarize or skip "minor" content.

## Output Format
Write DIRECTLY to `./papers/Author_Year_ShortTitle/chunks/chunk-STARTPAGE-ENDPAGE.md`:

# Pages START-END Notes

## Chapters/Sections Covered
## Key Findings
## Equations Found (LaTeX)
## Parameters Found (table)
## Rules/Algorithms
## Figures of Interest
## Quotes Worth Preserving
## Implementation Notes

## CRITICAL: Parallel Swarm Awareness
You are running alongside other chunk readers.
- Only write to YOUR chunk file in the chunks/ directory
- NEVER use git restore/checkout/reset/clean
```

### Process All Chunks

```bash
mkdir -p "./papers/Author_Year_ShortTitle/chunks"
```

**If you can dispatch parallel subagents**, launch one per chunk simultaneously. Each reads its page range and writes to `chunks/chunk-START-END.md`.

**If parallel dispatch is not available**, process each chunk sequentially yourself.

### Synthesize

Read all `chunks/chunk-*.md` files and synthesize into `notes.md`. Merge, deduplicate, and organize into the format from Step 3. If you can dispatch a synthesis subagent, do so; otherwise do it yourself.

Continue to Step 3.

---

## Step 3: Write Notes

**Be exhaustive.** Extract every equation, every parameter, every algorithm. The goal is that someone implementing this paper never needs to open the PDF. More detail is always better.

Write to `./papers/Author_Year_ShortTitle/notes.md`:

```markdown
---
title: "[Full Paper Title]"
authors: "[All authors]"
year: [Year]
venue: "[Journal/Conference/Thesis]"
doi_url: "[If available]"
---

# [Full Paper Title]

## One-Sentence Summary
[What this paper provides for implementation - be specific]

## Problem Addressed
[What gap or issue does this paper solve?]

## Key Contributions
- [Contribution 1]
- [Contribution 2]

## Methodology
[High-level description]

## Key Equations

$$
[equation in LaTeX]
$$
Where: [variable definitions with units]

## Parameters

| Name | Symbol | Units | Default | Range | Notes |
|------|--------|-------|---------|-------|-------|

## Implementation Details
- Data structures needed
- Initialization procedures
- Edge cases
- Pseudo-code if provided

## Figures of Interest
- **Fig N (page X):** [What it shows]

## Results Summary
[Key performance characteristics]

## Limitations
[What authors acknowledge doesn't work]

## Testable Properties
- [Property 1: e.g., "Parameter X must be in [low, high]"]
- [Property 2: e.g., "Increasing A must increase B"]
- [Property 3: e.g., "Output of algorithm must satisfy constraint C"]

## Relevance to Project
[How this paper applies to the project's research domain]

## Open Questions
- [ ] [Unclear aspects]

## Related Work Worth Reading
- [Papers cited worth following]
```

### Frontmatter Schema

- Required: `title`, `year`
- Recommended: `authors`, `venue`, `doi_url`
- Optional: `pages`, `affiliation`, `affiliations`, `institution`, `publisher`, `supervisor`, `supervisors`, `funding`, `pacs`, `note`, `correction_doi`, `citation`
- Legacy aliases (do not emit in new papers): `author`, `doi`, `url`, `journal`, `type`, `paper`

---

## Extraction Guidelines

### Parameter Table Format (MANDATORY)

| Name | Symbol | Units | Default | Range | Notes |
|------|--------|-------|---------|-------|-------|
| Fundamental frequency | F0 | Hz | 120 | 60-500 | Male speaker baseline |

**Rules:**
- **One row per parameter.** Each row is one measurable quantity.
- **Name column required.** Full descriptive name.
- **Units column required.** SI or standard acoustic units. `-` for dimensionless.
- **Default/Range**: At least one must be populated. `X-Y` for ranges.
- **Notes**: Source table/figure, conditions, caveats.

**If a parameter varies by context**, create **one table per context** (e.g., "Modal Voice Parameters", "Breathy Voice Parameters").

**DO NOT use matrix format** (parameters as columns, contexts as rows). The extractor expects parameters as rows.

**Measurement/data tables** use descriptive headers with units in parentheses: `F1 (Hz)`, `Duration (ms)`.

### Equation Format (MANDATORY)

- One equation per `$$` block
- No prose, markdown, or headers inside `$$` blocks
- Variable definitions go in prose AFTER the equation block
- Use standard LaTeX notation

### Extraction Targets

- **Equations**: Every equation with all variables defined and units given
- **Parameters**: Every parameter, constant, and threshold — values, ranges, defaults, source
- **Algorithms**: Numbered steps with inputs, outputs, state
- **Testable Properties**: Bounds, monotonic relationships, invariants — these become property-based tests

---

## Step 4: Write Description

Write `./papers/Author_Year_ShortTitle/description.md`:

```markdown
---
tags: [tag1, tag2, tag3]
---
[Sentence 1: What the paper does/presents]
[Sentence 2: Key findings/contributions]
[Sentence 3: Relevance to this project's research domain]
```

Single paragraph, no blank lines between sentences. Tags: 2-5, lowercase, hyphens for multi-word, prefer existing tags from `papers/index.md`.

---

## Step 5: Write Abstract

Write `./papers/Author_Year_ShortTitle/abstract.md`:

```markdown
# Abstract

## Original Text (Verbatim)

[Exact abstract text from the paper]

---

## Our Interpretation

[2-3 sentences: What problem? Key finding? Why relevant?]
```

For chunked papers, delegate to a **haiku** subagent reading `pngs/page-000.png`.

---

## Step 6: Write Citations

Write `./papers/Author_Year_ShortTitle/citations.md`:

```markdown
# Citations

## Reference List

[Every citation from References/Bibliography, preserving original formatting]

## Key Citations for Follow-up

[3-5 most relevant citations with brief notes on why]
```

For chunked papers, delegate to a **haiku** subagent reading the last 5-10 page images.

**Steps 5 and 6 can run in parallel** since they write to different files.

---

## Step 7: Cross-Reference Collection

Invoke the **reconcile** skill on `papers/Author_Year_ShortTitle`. This handles forward/reverse cross-referencing, reconciliation of citing papers, and backward annotations.

Wait for reconcile to complete before proceeding.

---

## Step 8: Update papers/index.md

Append:
```markdown
## Author_Year_ShortTitle  (tag1, tag2, tag3)
[description.md body text — no frontmatter, no tags line]
```

**This step is NOT optional.** Without it, future sessions won't know this paper exists.

---

## Quality Checklist

- [ ] All equations with variable definitions
- [ ] All parameters in standard table format
- [ ] Algorithm steps numbered
- [ ] Figures described with page numbers
- [ ] Limitations section filled
- [ ] Testable properties extracted
- [ ] description.md written
- [ ] abstract.md written
- [ ] citations.md written
- [ ] Reconcile skill invoked
- [ ] papers/index.md updated
- [ ] No temp files left behind

---

## Output

All papers produce: `papers/Author_Year_Title/` containing `notes.md`, `description.md`, `abstract.md`, `citations.md`, `pngs/`, and an updated `papers/index.md` entry.

Papers >50 pages also produce `chunks/`.

When done:
```
Done - created papers/[dirname]/
  - index.md updated
  - Reconciliation: [summary]
```

Then provide a brief **usefulness assessment** in the conversation (not a file):

```
## Usefulness to This Project

**Rating:** [High/Medium/Low/Marginal]
**What it provides:** [concrete takeaways]
**Actionable next steps:** [what to implement or investigate]
**Skip if:** [when this paper isn't relevant]
```

---

Do NOT:
- Delete page images or chunk reports
- Output findings to conversation instead of files
- Skip index.md update (Step 8) or reconcile (Step 7)
- Write ANY temp files to `papers/` root
- Use `cp` instead of `mv` for the source PDF
