---
name: paper-reader
description: Read scientific papers and extract implementation-focused notes. Use when you have a PDF that needs systematic extraction of equations, parameters, algorithms. Handles small papers (direct read), medium papers (image conversion), and large papers (parallel chunk readers via foreman protocol). Creates structured notes in papers/ directory.
argument-hint: [path/to/paper.pdf]
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
-> Report "Already complete" and stop

### Case B2: Missing abstract and/or citations

Determine the source to read from:
- If `pngs/` directory exists with page images -> use pngs
- Otherwise -> use the PDF directly

**Dispatch gap-filling agents** (in parallel if both missing):

#### Missing abstract.md:

```
Task(subagent_type: general-purpose, model: haiku)
prompt: "Extract the abstract from this paper and write abstract.md

## Input
Read: [paper_dir]/pngs/page-000.png (or [paper_dir]/*.pdf page 1)

## Output Format
Write to [paper_dir]/abstract.md:

# Abstract

## Original Text (Verbatim)

[Verbatim abstract text exactly as written in the paper]

---

## Our Interpretation

[2-3 sentences: What problem? Key finding? Why relevant to this project?]

---

CRITICAL: Part 1 is EXACT text. Part 2 is YOUR interpretation."
```

#### Missing citations.md:

```
Task(subagent_type: general-purpose, model: haiku)
prompt: "Extract all citations from this paper and write citations.md

## Input
Read: [paper_dir]/pngs/ - read the LAST 5-10 page images (where References typically appear)
Or if using PDF: [paper_dir]/*.pdf - navigate to References/Bibliography section

## Output Format
Write to [paper_dir]/citations.md:

# Citations

## Reference List

[List every citation from the References/Bibliography section, one per line]
[Preserve original formatting: authors, year, title, journal/venue, pages]

## Key Citations for Follow-up

[List 3-5 citations most relevant for this project's research area, with brief notes on why]

---

CRITICAL: Extract ALL citations from the references section."
```

After gap-filling agents complete:
```
Done - filled gaps in papers/[dirname]/
  - abstract.md: [created/already existed]
  - citations.md: [created/already existed]
```
-> **Stop here** (do not continue to Step 1)

---

## Step 1: Determine Paper Size

Check if PDF can be read directly:

```bash
pdfinfo "$ARGUMENTS" 2>/dev/null | grep Pages || echo "pdfinfo not available"
```

Also try direct read - Claude will error if >20MB:

**Decision tree:**
- **<=25 pages AND <20MB**: Direct PDF read (Step 2A)
- **26-100 pages OR 20MB error**: Image conversion, read sequentially (Step 2B)
- **>100 pages**: Foreman protocol with parallel chunk readers (Step 2C)

---

## Step 2A: Direct PDF Read (Small Papers <=25 pages)

1. Read the PDF directly with Read tool
2. Continue to Step 3 (Create Output)
3. After Step 5, **write abstract.md and citations.md yourself** (you already have the content - no agents needed)

---

## Step 2B: Image Conversion (Medium Papers 26-100 pages)

1. **Convert PDF to images**:
   ```bash
   magick -density 150 "$ARGUMENTS" -quality 90 "./papers/temp-page-%03d.png"
   ```

2. **Read each page image** sequentially using Read tool

3. **Keep PNGs** in place (don't delete - user may want them)

4. Continue to Step 3

---

## Step 2C: Foreman Protocol (Large Papers >100 pages)

For papers >100 pages, switch to **foreman mode**: coordinate parallel subagents, don't read directly.

### 2C.1: Read Page 0 for Metadata

Read the first page to extract author, year, title for directory naming:

```bash
magick -density 150 "$ARGUMENTS[0]" -quality 90 "./papers/temp-page-000.png"
```

Read `./papers/temp-page-000.png` to get paper metadata, then determine directory name (`Author_Year_ShortTitle`).

### 2C.2: Create Output Directory Structure

Create the output directory **before** full conversion so chunk readers can write directly there:

```bash
mkdir -p "./papers/Author_Year_ShortTitle/pngs"
mkdir -p "./papers/Author_Year_ShortTitle/chunks"
mv "$ARGUMENTS" "./papers/Author_Year_ShortTitle/"
```

### 2C.3: Convert PDF to Images (directly into output directory)

```bash
magick -density 150 "./papers/Author_Year_ShortTitle/paper.pdf" -quality 90 "./papers/Author_Year_ShortTitle/pngs/page-%03d.png"
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

Read each page image in your range using the Read tool.

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

### 2C.6: Launch Parallel Chunk Readers

Use Task tool to launch ALL chunk readers **in a single message** (parallel):

```
Task(subagent_type: general-purpose)
prompt: "@prompts/paper-chunk-reader.md

Your chunk: pages 000-039 (page-000.png through page-039.png)
Write to: ./papers/Author_Year_ShortTitle/chunks/chunk-000-039.md"
```

Repeat for each chunk range. **All Task calls in ONE message for parallelism.**

### 2C.7: Wait for All Chunks to Complete

All chunk readers must finish before synthesis.

### 2C.8: Launch Synthesis Agent

Write synthesis prompt to `./prompts/paper-synthesis.md`, then dispatch:

```markdown
# Task: Synthesize Paper Chunk Notes

## Input
Read all ./papers/Author_Year_ShortTitle/chunks/chunk-*.md files

## Output
Write synthesized notes to ./papers/Author_Year_ShortTitle/notes.md
(Chunks are already in place - no copying needed)
```

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
mv "$ARGUMENTS" "./papers/FirstAuthor_Year_ShortTitle/"
```

**Naming convention**: `LastName_Year_2-4WordTitle`
- Examples: `Mack_2021_AccessibilityResearchSurvey`, `Vanderheiden_2023_TraceTechnologyDisability`

---

## Step 3.5: Copy Page Images (Medium Papers only)

For Step 2B (medium papers), copy temp images into the paper directory:

```bash
mkdir -p "./papers/FirstAuthor_Year_ShortTitle/pngs"
cp ./papers/temp-page-*.png "./papers/FirstAuthor_Year_ShortTitle/pngs/"
```

**Note:** For large papers (Step 2C), images are written directly to the output directory - no copying needed.

### Cleanup Temp Images

```bash
rm -f ./papers/temp-page-*.png
```

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
[Sentence 1: What the paper does/presents]
[Sentence 2: Key findings/contributions]
[Sentence 3: Relevance to this project's research domain]
```

**Format**: Single paragraph, no blank lines. Each sentence flows into the next.

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

### Medium/Large Papers: Haiku Agent

Use Task tool with `model: haiku`:

```
Task(subagent_type: general-purpose, model: haiku)
prompt: "Extract the abstract from this paper and write abstract.md

## Input
Read: ./papers/FirstAuthor_Year_ShortTitle/[paper.pdf or pngs/page-000.png]
(The abstract is typically on page 1)

## Output Format
Write to ./papers/FirstAuthor_Year_ShortTitle/abstract.md:

# Abstract

## Original Text (Verbatim)

[Verbatim abstract text exactly as written in the paper, preserving paragraph breaks]

---

## Our Interpretation

[2-3 sentences explaining what this abstract tells us in plain language. What problem does the paper solve? What's the key finding? Why should we care for this project's research area?]

---

CRITICAL:
- Part 1 is the EXACT text from the paper. Do not paraphrase.
- Part 2 is YOUR interpretation in accessible language.
- The horizontal rule (---) separates them visually."
```

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

### Medium/Large Papers: Haiku Agent

Use Task tool with `model: haiku`:

```
Task(subagent_type: general-purpose, model: haiku)
prompt: "Extract all citations from this paper and write citations.md

## Input
Read: ./papers/FirstAuthor_Year_ShortTitle/[paper.pdf]
For large papers with pngs/: Read the last 3-5 page images where References/Bibliography typically appears

## Output Format
Write to ./papers/FirstAuthor_Year_ShortTitle/citations.md:

# Citations

## Reference List

[List every citation from the References/Bibliography section, one per line]
[Preserve original formatting: authors, year, title, journal/venue, pages]
[Number them if the paper numbers them]

## Key Citations for Follow-up

[List 3-5 citations that seem most relevant for this project's research area, with brief notes on why]

---

CRITICAL: Extract ALL citations from the references section, not just ones mentioned in body text."
```

**Timing**: Steps 6 and 7 can run **in parallel** with each other since they write to different files.

---

## Step 7.5: Cross-Reference Collection

After citations.md is written, check which cited papers already exist in the collection and which are new leads.

### How to Cross-Reference

1. **Extract author-year keys** from the Key Citations for Follow-up in citations.md
2. **Grep papers/CLAUDE.md** for each cited author's last name:

```bash
# For each key citation author, check if already in collection
grep -c "AuthorName" ./papers/CLAUDE.md
```

3. **Append a connections section** to notes.md:

```markdown
## Collection Cross-References

### Already in Collection
- **AuthorA_Year_ShortTitle** - cited for [reason] (our notes cover this)

### New Leads (Not Yet in Collection)
- AuthorB (Year) - "Paper title" - relevant for [reason]

### Supersedes or Recontextualizes
- [If this paper resolves, corrects, or extends a paper we already have, note it here]
```

### Backward Annotation

If the "Supersedes or Recontextualizes" section is non-empty, **append a see-also note** to the affected paper's notes.md:

```bash
echo "" >> ./papers/AffectedPaper_Dir/notes.md
echo "---" >> ./papers/AffectedPaper_Dir/notes.md
echo "" >> ./papers/AffectedPaper_Dir/notes.md
echo "**See also:** NewPaper_Dir - [relationship description]" >> ./papers/AffectedPaper_Dir/notes.md
```

Only annotate backward when there's a genuine supersedes/extends/corrects relationship - not for every citation.

---

## Step 8: Update papers/CLAUDE.md

This is the step that makes the collection work across sessions. Concatenate the description into the paper index.

```bash
echo "" >> ./papers/CLAUDE.md
echo "## FirstAuthor_Year_ShortTitle" >> ./papers/CLAUDE.md
cat ./papers/FirstAuthor_Year_ShortTitle/description.md >> ./papers/CLAUDE.md
echo "" >> ./papers/CLAUDE.md
```

**This step is NOT optional.** Without it, future sessions won't know this paper exists.

---

## Large Papers: Additional Extraction Agents

For papers using the foreman protocol (Step 2C), dispatch the abstract and citations extractors **in parallel with chunk readers** (Step 2C.6):

```
# In the same message as chunk reader dispatches, add:

Task(subagent_type: general-purpose, model: haiku)
prompt: "Extract abstract from ./papers/Author_Year_ShortTitle/pngs/page-000.png
Write to ./papers/Author_Year_ShortTitle/abstract.md
[use format from Step 6]"

Task(subagent_type: general-purpose, model: haiku)
prompt: "Extract citations from ./papers/Author_Year_ShortTitle/pngs/
Read the last 5-10 page images (where references typically are)
Write to ./papers/Author_Year_ShortTitle/citations.md
[use format from Step 7]"
```

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
- [ ] Cross-references checked (which cited papers are already in collection vs new leads)
- [ ] papers/CLAUDE.md updated (description concatenated)
- [ ] Temp images cleaned up (if medium paper path)
- [ ] Backward annotations written (if supersedes/recontextualizes existing papers)

---

## Output

**Small papers (<=25 pages)**: `papers/Author_Year_Title/notes.md` + `description.md` + `abstract.md` + `citations.md`
**Medium papers (26-100 pages)**: `papers/Author_Year_Title/notes.md` + `description.md` + `abstract.md` + `citations.md` + `pngs/`
**Large papers (>100 pages)**: `papers/Author_Year_Title/notes.md` + `description.md` + `abstract.md` + `citations.md` + `pngs/` + `chunks/`

**All sizes also produce**: Updated `papers/CLAUDE.md` entry + cross-reference annotations in notes.md

When done:
```
Done - created papers/[dirname]/
  - CLAUDE.md updated
  - Cross-refs: N papers already in collection, M new leads
  - Backward annotations: [list any existing papers annotated, or "none"]
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
- Skip the CLAUDE.md update (Step 8) - this is what makes the system work
- Skip cross-referencing (Step 7.5) - this is what turns papers into a conversation
- Leave temp images behind in papers/ root (clean up after Step 3.5)
