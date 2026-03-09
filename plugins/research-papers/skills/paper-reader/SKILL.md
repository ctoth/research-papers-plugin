---
name: paper-reader
description: Read scientific papers and extract implementation-focused notes. Use when you have a PDF that needs systematic extraction of equations, parameters, algorithms. Handles small papers (direct read), medium papers (image conversion), and large papers (parallel chunk readers via foreman protocol). Creates structured notes in papers/ directory.
argument-hint: "[path/to/paper.pdf]"
disable-model-invocation: false
---

# Paper Reader: $ARGUMENTS

Read a scientific paper and create comprehensive implementation-focused notes.

## Step 0: Check for Existing Paper

First, check if this paper has already been processed:

```bash
# Extract directory name from path (handles both new PDFs and existing directories)
paper_path="$ARGUMENTS"
if [ -d "$paper_path" ]; then
  paper_dir="$paper_path"
elif [ -f "$paper_path" ]; then
  # Check if a matching directory already exists in papers/
  basename=$(basename "$paper_path" .pdf)
  # Look for directories containing this basename
  existing=$(ls -d papers/*/ 2>/dev/null | grep -i "${basename%_*}" | head -1)
  paper_dir="$existing"
fi
```

**Decision tree:**

### Case A: No existing directory found
-> Continue to Step 1 (normal processing flow)

### Case B: Directory exists - check what's missing

```bash
ls -la "$paper_dir"/*.md 2>/dev/null
ls "$paper_dir"/pngs/ 2>/dev/null | head -3  # Check if pngs exist
ls "$paper_dir"/*.pdf 2>/dev/null | head -1   # Check for PDF
```

Determine gaps:
- Has `notes.md`? If no -> this is incomplete, continue to Step 1
- Has `abstract.md`?
- Has `citations.md`?

### Case B1: All files present (notes + abstract + citations)

If the original argument was a root-level PDF (e.g. `papers/something.pdf`), delete it — the processed copy lives inside the paper directory. The root PDF is a duplicate at this point:

```bash
# Only delete if it's a root-level PDF file (not a directory reference)
if [ -f "$paper_path" ]; then
  rm "$paper_path"
fi
```

-> Report "Already complete — deleted duplicate root PDF" and stop

### Case B2: Missing abstract and/or citations

Determine the source to read from:
- If `pngs/` directory exists with page images -> use pngs
- Otherwise -> use the PDF directly

**Fill the gaps** (in parallel if both missing and you can dispatch subagents):

#### Missing abstract.md:

If you can dispatch a subagent (use a fast/cheap model if available), delegate this:

> Extract the abstract from this paper and write abstract.md.
> Read: [paper_dir]/pngs/page-000.png (or [paper_dir]/*.pdf page 1).
> Write to [paper_dir]/abstract.md with two sections:
> 1. "Original Text (Verbatim)" — exact abstract text from the paper
> 2. "Our Interpretation" — 2-3 sentences: What problem? Key finding? Why relevant?
> Part 1 is EXACT text. Part 2 is YOUR interpretation.

Otherwise, do this yourself: read the first page and write abstract.md following the format above.

#### Missing citations.md:

If you can dispatch a subagent (use a fast/cheap model if available), delegate this:

> Extract all citations from this paper and write citations.md.
> Read: the LAST 5-10 page images from [paper_dir]/pngs/ (where References typically appear),
> or if using PDF: navigate to the References/Bibliography section.
> Write to [paper_dir]/citations.md with two sections:
> 1. "Reference List" — every citation, preserving original formatting
> 2. "Key Citations for Follow-up" — 3-5 most relevant for this project
> Extract ALL citations from the references section.

Otherwise, do this yourself: read the references pages and write citations.md following the format above.

After gap-filling completes, clean up the root PDF if the argument was a root-level file:

```bash
if [ -f "$paper_path" ]; then
  rm "$paper_path"
fi
```

```
Done - filled gaps in papers/[dirname]/
  - abstract.md: [created/already existed]
  - citations.md: [created/already existed]
  - root PDF: [deleted/was already a directory reference]
```
-> **Stop here** (do not continue to Step 1)

---

## Step 1: Determine Paper Size

Check if PDF can be read directly:

```bash
pdfinfo "$ARGUMENTS" 2>/dev/null | grep Pages || echo "pdfinfo not available"
```

Also try direct read - most agents will error on files >20MB:

**Decision tree:**
- **<=25 pages AND <20MB**: Direct PDF read (Step 2A)
- **26-100 pages OR 20MB error**: Image conversion, read sequentially (Step 2B)
- **>100 pages**: Foreman protocol with parallel chunk readers (Step 2C)

---

## Step 2A: Direct PDF Read (Small Papers <=25 pages)

1. Read the PDF directly
2. Continue to Step 3 (Create Output)
3. After Step 5, **write abstract.md and citations.md yourself** (you already have the content - no agents needed)

---

## Step 2B: Image Conversion (Medium Papers 26-100 pages)

1. **Convert page 0 only** to extract metadata for directory naming.
   **CRITICAL: Never write temp files to `papers/` root.** Use a system temp directory:
   ```bash
   tmpdir=$(mktemp -d)
   magick -density 150 "$ARGUMENTS[0]" -quality 90 -resize '1960x1960>' "$tmpdir/page0.png"
   ```

2. **Read the temp page image** (`$tmpdir/page0.png`) to extract author, year, title. Determine directory name (`Author_Year_ShortTitle`).

3. **Create output directory** and convert all pages directly there:
   ```bash
   mkdir -p "./papers/Author_Year_ShortTitle/pngs"
   mv "$ARGUMENTS" "./papers/Author_Year_ShortTitle/paper.pdf"  # MUST be mv, NEVER cp
   magick -density 150 "./papers/Author_Year_ShortTitle/paper.pdf" -quality 90 -resize '1960x1960>' "./papers/Author_Year_ShortTitle/pngs/page-%03d.png"
   rm -rf "$tmpdir"
   ```

4. **Read each page image** sequentially from the paper's `pngs/` directory

5. Continue to Step 4 (Write Notes) — **skip Steps 3 and 3.5** (directory already created, no temp images to copy)

---

## Step 2C: Foreman Protocol (Large Papers >100 pages)

For papers >100 pages, split into chunks and process each one. If you can dispatch parallel subagents, do so for maximum speed. Otherwise, process chunks sequentially.

### 2C.1: Read Page 0 for Metadata

Read the first page to extract author, year, title for directory naming:

**CRITICAL: Never write temp files to `papers/` root.** Use a system temp directory:
```bash
tmpdir=$(mktemp -d)
magick -density 150 "$ARGUMENTS[0]" -quality 90 -resize '1960x1960>' "$tmpdir/page0.png"
```

Read `$tmpdir/page0.png` to get paper metadata, then determine directory name (`Author_Year_ShortTitle`). Clean up: `rm -rf "$tmpdir"`

### 2C.2: Create Output Directory Structure

Create the output directory **before** full conversion so chunk readers can write directly there:

```bash
mkdir -p "./papers/Author_Year_ShortTitle/pngs"
mkdir -p "./papers/Author_Year_ShortTitle/chunks"
mv "$ARGUMENTS" "./papers/Author_Year_ShortTitle/paper.pdf"  # MUST be mv, NEVER cp
```

### 2C.3: Convert PDF to Images (directly into output directory)

```bash
magick -density 150 "./papers/Author_Year_ShortTitle/paper.pdf" -quality 90 -resize '1960x1960>' "./papers/Author_Year_ShortTitle/pngs/page-%03d.png"
```

### 2C.4: Count Pages and Calculate Chunks

```bash
ls ./papers/Author_Year_ShortTitle/pngs/page-*.png | wc -l
```

Use **40-page chunks**. Calculate ranges:
- Chunk 1: 000-039
- Chunk 2: 040-079
- ...
- Last chunk: whatever remains

### 2C.5: Write ONE Template Prompt

Write to `./prompts/paper-chunk-reader.md` (customize for this paper):

```markdown
# Task: Read Paper Chunk and Extract Notes

## Context
You are reading a chunk of [PAPER TITLE] being processed in parallel.
Page images: `./papers/Author_Year_ShortTitle/pngs/page-NNN.png`

## Your Chunk
**START_PAGE** to **END_PAGE** (inclusive)

Read each page image in your range.

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

### 2C.6: Process All Chunks

**If you can dispatch parallel subagents**, launch one per chunk simultaneously. Each subagent reads its page range and writes to `./papers/Author_Year_ShortTitle/chunks/chunk-START-END.md`. Use the prompt template from 2C.5, customizing the page range for each chunk. Launch all chunk readers at once for parallelism.

**If parallel dispatch is not available**, process each chunk sequentially: for each chunk range, read the pages and write the chunk file yourself following the same prompt template.

### 2C.7: Wait for All Chunks to Complete

All chunk readers must finish before synthesis.

### 2C.8: Synthesize Chunk Notes

Read all `./papers/Author_Year_ShortTitle/chunks/chunk-*.md` files and synthesize them into `./papers/Author_Year_ShortTitle/notes.md`.

If you can dispatch a subagent for synthesis, do so. Otherwise, do it yourself. The synthesis should merge findings across chunks, deduplicate, and organize into the notes.md format from Step 4.

### 2C.9: Done

Everything is already in place:
- `./papers/Author_Year_ShortTitle/paper.pdf` - original PDF
- `./papers/Author_Year_ShortTitle/pngs/` - page images
- `./papers/Author_Year_ShortTitle/chunks/` - chunk reports
- `./papers/Author_Year_ShortTitle/notes.md` - synthesized notes

---

## Step 3: Create Output Directory

Extract author/year/title from paper content:

```bash
mkdir -p "./papers/FirstAuthor_Year_ShortTitle"
mv "$ARGUMENTS" "./papers/FirstAuthor_Year_ShortTitle/paper.pdf"
```

**CRITICAL: Use `mv`, NEVER `cp`.** The root-level PDF must be removed. If it stays behind, there is no way to distinguish "unprocessed PDF" from "already processed, agent left a copy." The `mv` is the signal that processing is complete. Using `cp` breaks the entire workflow.

**Naming convention**: `LastName_Year_2-4WordTitle`
- Examples: `Mack_2021_AccessibilityResearchSurvey`, `Vanderheiden_2023_TraceTechnologyDisability`

---

## Step 3.5: Copy Page Images (SKIP for Medium Papers)

**Medium papers (Step 2B):** Images are already in `./papers/Author_Year_ShortTitle/pngs/` — no copying or cleanup needed. Skip this step entirely.

**Large papers (Step 2C):** Images are written directly to the output directory — no copying needed. Skip this step entirely.

**This step only applies if a PDF was placed in papers/ root and manually converted there.** In normal flow, all image conversion targets the paper's own `pngs/` subdirectory.

---

## Step 4: Write Notes

Write to `./papers/FirstAuthor_Year_ShortTitle/notes.md`:

```markdown
# [Full Paper Title]

**Authors:** [All authors]
**Year:** [Year]
**Venue:** [Journal/Conference/Thesis]
**DOI/URL:** [If available]

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
Where: [variable definitions]

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
[Invariants, bounds, and monotonic relationships from the paper that could be checked programmatically.
Think: if we implemented this, what must always be true?]

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

---

## Extraction Guidelines

### Equations
- LaTeX math blocks: `$inline$` or `$$block$$`
- Define ALL variables with units
- Include equation numbers from paper

### Parameters
- Extract EVERY parameter, constant, threshold
- Include values, ranges, defaults
- Note source (measured, derived, arbitrary)

### Algorithms
- Numbered steps, clear sequencing
- Note inputs, outputs, state

### Testable Properties
- Extract bounds/ranges: "Parameter X is always in [low, high]"
- Extract monotonic relationships: "Increasing A causes B to increase/decrease"
- Extract invariants: "X + Y must equal Z", "Output must satisfy constraint C"
- These become property-based tests for any implementation derived from the paper

---

## Step 5: Write Description

After writing notes.md, write a three-sentence `description.md` in the same directory:

```markdown
---
tags: [tag1, tag2, tag3]
---
[Sentence 1: What the paper does/presents]
[Sentence 2: Key findings/contributions]
[Sentence 3: Relevance to this project's research domain]
```

**Format**: YAML frontmatter with tags, then a single paragraph (no blank lines between sentences).

**Tagging guidelines:**
- 2-5 tags per paper
- Use lowercase, hyphens for multi-word (`voice-quality`, not `Voice Quality`)
- Prefer existing tags when they fit — check `papers/index.md` for tags already in use
- Mix specificity levels: one broad (`acoustics`), one or two narrow (`glottal-source`, `lf-model`)
- Tags describe **what the paper is about**, not what project it's for

---

## Step 6: Write Abstract

**For small papers (Step 2A):** Write abstract.md directly - you already read the paper.

**For medium/large papers (Steps 2B/2C):** Dispatch a **haiku** agent.

### Small Papers: Write Directly

Write to `./papers/FirstAuthor_Year_ShortTitle/abstract.md`:

```markdown
# Abstract

## Original Text (Verbatim)

[Copy the exact abstract text from the paper]

---

## Our Interpretation

[2-3 sentences: What problem? Key finding? Why relevant to this project?]
```

### Medium/Large Papers: Delegate Extraction

If you can dispatch a subagent for this extraction (use a fast/cheap model if available), delegate it:

> Read `./papers/FirstAuthor_Year_ShortTitle/[paper.pdf or pngs/page-000.png]` (abstract is typically on page 1).
> Write to `./papers/FirstAuthor_Year_ShortTitle/abstract.md` with two sections:
> 1. "Original Text (Verbatim)" — exact abstract text, preserving paragraph breaks
> 2. "Our Interpretation" — 2-3 sentences in plain language: What problem? Key finding? Why care?
> Part 1 is EXACT text. Part 2 is YOUR interpretation.

Otherwise, do this yourself.

---

## Step 7: Write Citations

**For small papers (Step 2A):** Write citations.md directly - you already read the paper.

**For medium/large papers (Steps 2B/2C):** Dispatch a **haiku** agent.

### Small Papers: Write Directly

Write to `./papers/FirstAuthor_Year_ShortTitle/citations.md`:

```markdown
# Citations

## Reference List

[List every citation from the References/Bibliography section]
[Preserve original formatting: authors, year, title, journal/venue, pages]
[Number them if the paper numbers them]

## Key Citations for Follow-up

[List 3-5 citations most relevant for this project, with brief notes on why]
```

### Medium/Large Papers: Delegate Extraction

If you can dispatch a subagent for this extraction (use a fast/cheap model if available), delegate it:

> Read `./papers/FirstAuthor_Year_ShortTitle/[paper.pdf]`.
> For large papers with pngs/: read the last 3-5 page images where References/Bibliography typically appears.
> Write to `./papers/FirstAuthor_Year_ShortTitle/citations.md` with two sections:
> 1. "Reference List" — every citation, preserving original formatting, numbered if the paper numbers them
> 2. "Key Citations for Follow-up" — 3-5 most relevant for this project
> Extract ALL citations from the references section, not just ones mentioned in body text.

Otherwise, do this yourself.

**Timing**: Steps 6 and 7 can run **in parallel** with each other since they write to different files.

---

## Step 7.5: Cross-Reference Collection

After citations.md is written, invoke the **reconcile** skill to handle all cross-referencing:

Invoke the **reconcile** skill on `papers/FirstAuthor_Year_ShortTitle`.
If skill invocation is available (e.g., `/research-papers:reconcile`), use it.
Otherwise, follow the reconcile SKILL.md instructions directly.

This handles:
- Forward cross-referencing (which cited papers are already in the collection)
- Reverse citation search (which collection papers cite this one)
- Reconciliation of citing papers (updating leads, correcting descriptions, documenting tensions)
- Backward annotations (see-also notes on superseded/extended papers)

Wait for reconcile to complete before proceeding to Step 8.

---

## Step 8: Update papers/index.md

This is the step that makes the collection work across sessions. Append the paper's heading and description to the index.

```bash
{
  echo ""
  echo "## FirstAuthor_Year_ShortTitle  (tag1, tag2, tag3)"
  cat ./papers/FirstAuthor_Year_ShortTitle/description.md | grep -v "^---" | grep -v "^tags:" | sed '/^$/d'
  echo ""
} >> ./papers/index.md
```

Or use your editing tools to append. The format is:

```markdown
## FirstAuthor_Year_ShortTitle  (tag1, tag2, tag3)
[description.md body text — no frontmatter, no tags line]
```

**This step is NOT optional.** Without it, future sessions won't know this paper exists.

**Note:** `index.md` is NOT auto-loaded into agent context — it's a searchable reference that agents grep when they need to find papers. This keeps session startup fast even with large collections.

---

## Large Papers: Additional Extraction Agents

For papers using the large paper protocol (Step 2C), extract abstract and citations **in parallel with chunk processing** if possible:

- **Abstract**: Read `./papers/Author_Year_ShortTitle/pngs/page-000.png`, write `abstract.md` (format from Step 6)
- **Citations**: Read the last 5-10 page images from `pngs/`, write `citations.md` (format from Step 7)

If you can dispatch subagents (use a fast/cheap model if available), launch these alongside the chunk readers. Otherwise, do them after chunk processing completes.

---

## Quality Checklist

- [ ] All equations with variable definitions
- [ ] All parameters in table format
- [ ] Algorithm steps numbered
- [ ] Figures described with page numbers
- [ ] Limitations section filled
- [ ] Testable properties extracted (bounds, monotonic relationships, invariants)
- [ ] Open questions capture unknowns
- [ ] description.md written (3 sentences, single paragraph)
- [ ] abstract.md written (verbatim + interpretation)
- [ ] citations.md written (full reference list + key citations)
- [ ] Reconcile skill invoked (forward + reverse cross-references, reconciliation)
- [ ] papers/index.md updated (dirname appended)
- [ ] Temp images cleaned up (if medium paper path)

---

## Output

**Small papers (<=25 pages)**: `papers/Author_Year_Title/notes.md` + `description.md` + `abstract.md` + `citations.md`
**Medium papers (26-100 pages)**: `papers/Author_Year_Title/notes.md` + `description.md` + `abstract.md` + `citations.md` + `pngs/`
**Large papers (>100 pages)**: `papers/Author_Year_Title/notes.md` + `description.md` + `abstract.md` + `citations.md` + `pngs/` + `chunks/`

**All sizes also produce**: Updated `papers/index.md` entry + cross-reference annotations in notes.md

When done:
```
Done - created papers/[dirname]/
  - index.md updated
  - Reconciliation: [summary from reconcile skill output]
```

Then provide a brief **usefulness assessment** to the user:

```
## Usefulness to This Project

**Rating:** [High/Medium/Low/Marginal]

**What it provides:**
- [Concrete takeaway 1]
- [Concrete takeaway 2]

**Actionable next steps:**
- [Specific thing to implement or investigate]

**Skip if:**
- [Conditions where this paper isn't relevant]
```

This assessment goes in the conversation (not a file) so the user knows whether to dig deeper.

---

Do NOT:
- Delete page images in paper directories (user may want them)
- Delete chunk reports (preserve for reference)
- Output findings to conversation
- Skip the index.md update (Step 8) - this is what makes the system work
- Skip the reconcile skill invocation (Step 7.5) - this is what turns papers into a conversation
- Write ANY temp files to `papers/` root — use `mktemp -d` for temp work, paper's own `pngs/` for final images
- Leave temp images behind anywhere (clean up after conversion)
