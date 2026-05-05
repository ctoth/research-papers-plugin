---
name: paper-reader
description: Read scientific papers and extract implementation-focused notes. Converts PDFs to page images, then reads them. Papers <=300pp are read directly by the assigned worker; papers >300pp fall back to 50-page chunks. Creates structured notes in papers/ directory.
argument-hint: "[path/to/paper.pdf]"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI. Requires shell access; subagents are optional but improve large-paper throughput."
---

# Paper Reader: $ARGUMENTS

Read a scientific paper and create comprehensive implementation-focused notes.

## Execution Discipline

This skill is a checklist, not an outcome sketch.

- Follow the steps in order.
- Do not substitute alternate text-extraction or summarization workflows for the required page-image reading flow unless this skill explicitly tells you to.
- Do not add unlisted probes or "better" preprocessing steps.
- If you are blocked on a specific step, stop there and report the exact blocker instead of inventing a workaround.
- Do not report progress from intermediate artifacts not named in this procedure.
- This skill stops at paper artifacts and collection cross-references. It does not initialize or mutate propstore source branches.
- Do not declare yourself blocked merely because this skill does not name a platform-specific image-view tool. Use the platform's local image-reading capability (for example, `Read Image` in Claude Code or `view_image` in Codex) to inspect `pngs/page-*.png`.
- Only report an image-reading blocker after you have actually attempted to inspect a local page image such as `page-000.png` and the platform refused or failed.

## Extraction Objective

The target output in this repo is a **dense paper surrogate**, not a sharpened executive summary.

- Favor **high recall over compression**.
- Preserve the paper's formal content, definitions, equations, thresholds, algorithm steps, caveats, and section-level structure.
- Do **not** collapse notes into only the "main idea" or a few elegant abstractions.
- Do **not** optimize for brevity. Optimize for faithful extraction with useful organization.
- The standard is: a later reader should rarely need to reopen the PDF except to inspect a figure in full detail.

## Subagent Model Policy

Paper extraction is high-stakes and context-heavy. If you dispatch any subagent for reading, chunk extraction, synthesis, abstract extraction, citations extraction, or end-to-end paper processing:

- Use the **strongest available full-size model** on the platform.
- **Never** use a mini, small, flash, nano, lightweight, or economy tier model for paper extraction work.
- If the platform exposes named model choices, choose the top-tier frontier model rather than a cheaper/faster variant.
- If the strongest full model is unavailable, do the work yourself instead of delegating to a weaker mini-tier worker.

## Script Paths

The command examples below use `scripts/...` paths that are relative to this skill's directory. Resolve them against the installed skill location, not the user's project root.

## Step 0: Check for Existing Paper

If the argument is a directory, use it directly. If it's a PDF file, use `paper_hash.py lookup` to find a matching paper directory:

```bash
paper_path="$ARGUMENTS"
if [ -d "$paper_path" ]; then
  paper_dir="$paper_path"
elif [ -f "$paper_path" ]; then
  HASH_SCRIPT="scripts/paper_hash.py"
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
- **No `notes.md`, but `paper.pdf` and `pngs/page-000.png` already exist?** This is a rerun/regeneration case. Do **not** rename or move files. Reuse the existing paper directory, inspect the existing page images directly, and continue to Step 1 with the existing assets.
- **No `notes.md`, `paper.pdf` exists, but `pngs/` is missing or incomplete?** Regenerate `pngs/` from the existing `paper.pdf`, then continue.
- **All files present (notes + abstract + citations)?** If the argument was a root-level PDF (i.e., NOT inside a paper directory's own folder), delete it (`rm "$paper_path"`). **NEVER delete a PDF that lives inside its own paper directory** (e.g., `papers/Author_Year/paper.pdf`). Report "Already complete," stop.
- **Missing abstract.md and/or citations.md?** Fill gaps using page images or PDF, then delete root PDF and stop. See Steps 5-6 for format.

---

## Step 1: Determine Working PDF and Reuse/Convert Assets

First determine the working PDF path:

```bash
paper_path="$ARGUMENTS"
if [ -d "$paper_path" ]; then
  paper_dir="$paper_path"
  work_pdf="$paper_dir/paper.pdf"
else
  work_pdf="$paper_path"
fi
```

If you are in a rerun/regeneration case and `"$paper_dir"/pngs/page-000.png` already exists, **reuse the existing page images**. Do not reconvert just because `notes.md` is missing.

Get page count:
```bash
pdfinfo "$work_pdf" 2>/dev/null | grep Pages || echo "pdfinfo not available"
```

If `pngs/page-000.png` does not already exist, extract page 0 first in a temp dir for metadata:

```bash
tmpdir=$(mktemp -d)
magick -density 150 "$work_pdf[0]" -quality 90 -resize '1960x1960>' "$tmpdir/page0.png"
```

Read either the existing `pngs/page-000.png` or `$tmpdir/page0.png` to extract author, year, and title. Determine directory name: `LastName_Year_2-4WordTitle` (e.g., `Mack_2021_AccessibilityResearchSurvey`).

For a new paper, set:

```bash
paper_dir="./papers/Author_Year_ShortTitle"
```

If this is a new paper, create the output directory and convert all pages:
```bash
mkdir -p "$paper_dir/pngs"
# Move source PDF into paper directory — skip if already there
if [ "$(realpath "$work_pdf")" != "$(realpath "$paper_dir/paper.pdf")" ]; then
  mv "$work_pdf" "$paper_dir/paper.pdf"  # MUST be mv, NEVER cp
fi
magick -density 150 "$paper_dir/paper.pdf" -quality 90 -resize '1960x1960>' "$paper_dir/pngs/page-%03d.png"
rm -rf "$tmpdir"
```

If this is an existing paper directory with `paper.pdf` present but missing/incomplete `pngs/`, regenerate:
```bash
mkdir -p "$paper_dir/pngs"
magick -density 150 "$paper_dir/paper.pdf" -quality 90 -resize '1960x1960>' "$paper_dir/pngs/page-%03d.png"
rm -rf "$tmpdir"
```

**CRITICAL: Use `mv`, NEVER `cp`.** The root-level PDF must be removed. A PDF left in `papers/` root is indistinguishable from an unprocessed paper.

**CRITICAL: Never write temp files to `papers/` root.** Use `mktemp -d` for temp work.

Count pages:
```bash
ls "$paper_dir"/pngs/page-*.png | wc -l
```

**Decision:**
- **≤300 pages**: Read all page images yourself (Step 2A). This is the default path. Modern long-context models hold a full academic paper in working memory without chunking.
- **>300 pages**: Chunk protocol (Step 2B). Only book-length works should reach this branch.

## Step 1.5: Prove the Page-Image Lane Works

Before long extraction, inspect `page-000.png` from the paper's `pngs/` directory using the platform's local image-reading capability (for example, `Read Image` in Claude Code or `view_image` in Codex).

- This is the intended workflow. It is **not** an OCR/text-extraction fallback.
- Do not stop just because the exact tool name is unspecified in this skill.
- Only stop if you actually attempted to inspect `page-000.png` and the platform prevented it.

Once `page-000.png` is visible, continue immediately to Step 2A or Step 2B.

---

## Step 2A: Direct Read (≤300 pages)

**CRITICAL: Read EVERY page image. No skipping, no sampling, no "reading enough to get the gist."** Read every single `page-NNN.png` file from `page-000` through the last page. If you have 34 pages, read 34 page images. Agents routinely skip pages to save tokens — this produces incomplete notes that miss equations, parameters, and key details buried in middle sections. The entire point of reading the paper is completeness. If you skip pages, the notes are worthless.

For papers with 300 pages or fewer, the assigned worker must do this reading itself in a single agent context. Do **not** dispatch additional readers, do **not** split the paper across workers, and do **not** sample pages. Every paper in this range fits comfortably in a long-context model's working memory.

Take thorough notes as you go. Continue to Step 3.

---

## Step 2B: Chunk Protocol (>300 pages)

Only book-length works reach this branch. Split into **50-page chunks**. Calculate ranges:
- Chunk 1: pages 000-049
- Chunk 2: pages 050-099
- Last chunk: whatever remains

**Chunk dispatch is the caller's responsibility, not this skill's.** A subagent invoked for a single paper cannot itself spawn parallel chunk workers (Claude Code supports only one level of delegation). If you hit this branch, stop and report the page count to your caller so they can dispatch one worker per chunk at the top level. Do **not** sample pages to stay in context; sampling produces worthless notes. Do **not** attempt to dispatch subagents from within a subagent.

### Write ONE Template Prompt

Write to `./prompts/paper-chunk-reader.md`:

```markdown
# Task: Read Paper Chunk and Extract Notes

## Context
You are reading a chunk of [PAPER TITLE] being processed in parallel.
Page images: `./papers/Author_Year_ShortTitle/pngs/page-NNN.png`

Use the strongest available full-size model for this job. Do not use any mini/small tier model.

## Your Chunk
**START_PAGE** to **END_PAGE** (inclusive)

Read each page image in your range. Be exhaustive — extract EVERY equation, parameter, algorithm step, implementation detail, limitation, criticism of prior work, and design rationale. Do not summarize away formal content or skip "minor" material. **Tag every finding with its page number** using *(p.N)* notation — downstream claim extraction depends on this.

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

If you are the **top-level caller** (not a subagent), dispatch one chunk worker per range simultaneously. Each reads its page range and writes to `chunks/chunk-START-END.md`. Use the strongest available full-size model for every chunk worker. Never use a mini/small tier worker for chunk extraction.

If you are a **subagent** invoked for this paper, you cannot dispatch further subagents. Stop, report the page count and the required chunk ranges to your caller, and let them re-dispatch flat.

Do not dispatch chunk workers until at least one local page image from this paper has been successfully inspected. If you cannot inspect even `page-000.png`, that is a concrete blocker and you should stop there.

### Synthesize

Read all `chunks/chunk-*.md` files and synthesize into `notes.md`. Merge, deduplicate, and organize into the format from Step 3. Preserve detail; synthesis should reorganize and deduplicate, not compress the paper into sparse abstractions. If you can dispatch a synthesis subagent, do so using the strongest available full-size model; otherwise do it yourself.

Continue to Step 3.

---

## Step 3: Write Notes

**Be exhaustive.** Extract every equation, every parameter, every algorithm, every stated limitation, every criticism of prior work, and every explicit design choice the authors justify. The goal is that someone implementing this paper never needs to open the PDF. More detail is better than elegant compression.

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

## Study Design (empirical papers)
- **Type:** [RCT / cohort / case-control / meta-analysis / systematic review / cross-sectional / etc.]
- **Population:** [N, demographics, inclusion/exclusion criteria] *(p.N)*
- **Intervention(s):** [what was administered, dosage, duration, route] *(p.N)*
- **Comparator(s):** [placebo, active control, standard of care] *(p.N)*
- **Primary endpoint(s):** [what was measured as the main outcome] *(p.N)*
- **Secondary endpoint(s):** [additional outcomes] *(p.N)*
- **Follow-up:** [duration, completeness, dropout rates] *(p.N)*

*Leave this section empty for non-empirical papers (pure theory, algorithms, proofs).*

## Methodology
[High-level description of approach — experimental design, computational method, analytical framework, etc.]

## Key Equations / Statistical Models

$$
[equation in LaTeX]
$$
Where: [variable definitions with units]
*(p.N)*

*Include statistical models (regression specifications, survival models, Bayesian priors) alongside mathematical equations. For clinical papers, capture the primary analysis model even if not presented in formal notation.*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|

*Capture every measurable quantity: physical constants, algorithm thresholds, dosages, sample sizes, hazard ratios, odds ratios, confidence intervals, p-value thresholds, effect sizes — whatever the paper's domain uses.*

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|

*One row per reported effect. Use for any empirical paper — clinical trials, A/B tests, benchmarks, ablation studies. Measure column: HR, OR, RR, RD, ATE, Cohen's d, accuracy, F1, BLEU, etc. Include both primary and subgroup results.*

## Methods & Implementation Details
- Study protocol / experimental setup *(p.N)*
- Statistical methods and software used *(p.N)*
- Data structures / algorithms needed *(p.N)*
- Initialization procedures / calibration *(p.N)*
- Edge cases / sensitivity analyses *(p.N)*
- Pseudo-code if provided *(p.N)*
- Adverse events / safety monitoring (clinical papers) *(p.N)*

## Figures of Interest
- **Fig N (p.X):** [What it shows]

## Results Summary
[Key findings — performance characteristics, clinical outcomes, effect magnitudes, statistical significance] *(p.N)*

## Limitations
[What authors acknowledge doesn't work] *(p.N)*

## Arguments Against Prior Work
- [What specific prior approaches does this paper criticize?] *(p.N)*
- [What failure modes or limitations of prior work does it identify?] *(p.N)*
- [What evidence does it present for the criticism?] *(p.N)*

## Design Rationale
- [What architectural choices does this paper justify?] *(p.N)*
- [What alternatives were considered and why were they rejected?] *(p.N)*
- [What properties does the chosen design preserve that alternatives don't?] *(p.N)*

## Testable Properties
- [Property 1: e.g., "Parameter X must be in [low, high]"] *(p.N)*
- [Property 2: e.g., "Increasing A must increase B"] *(p.N)*
- [Property 3: e.g., "Treatment effect HR < 1.0 for primary endpoint"] *(p.N)*
- [Property 4: e.g., "NNT for outcome Y = Z over N years"] *(p.N)*
- [Property 5: e.g., "Subgroup analysis shows effect modification by age"] *(p.N)*

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

## Step 3.5: Write metadata.json

Write `./papers/Author_Year_ShortTitle/metadata.json`.

Use this schema and fill every field you can from the paper/frontmatter:

```json
{
  "title": "Full Paper Title",
  "authors": ["Author One", "Author Two"],
  "year": "2024",
  "arxiv_id": null,
  "doi": "10.xxxx/xxxxx",
  "abstract": "Exact or near-exact abstract text",
  "url": null,
  "pdf_url": null
}
```

Rules:
- `title`, `authors`, and `year` are required.
- `authors` must be a JSON array, not a single string.
- Use `null` for unknown fields rather than omitting them.
- `doi` should be the DOI string without `https://doi.org/` when possible.
- If the paper is on arXiv, fill `arxiv_id`.

---

## Extraction Guidelines

### Parameter Table Format (MANDATORY)

| Name | Symbol | Units | Default | Range | Notes |
|------|--------|-------|---------|-------|-------|
| Fundamental frequency | F0 | Hz | 120 | 60-500 | Male speaker baseline |
| Aspirin dose | — | mg/day | 100 | 75-325 | Low-dose range |
| Hazard ratio (MACE) | HR | — | 0.89 | 0.77-1.03 | Primary composite endpoint |
| Learning rate | α | — | 0.001 | 1e-5–0.1 | Adam optimizer |

**Rules:**
- **One row per parameter.** Each row is one measurable quantity — physical constants, algorithm thresholds, dosages, effect sizes, confidence bounds.
- **Name column required.** Full descriptive name.
- **Units column required.** SI, standard domain units, or `-` for dimensionless ratios/rates.
- **Default/Range**: At least one must be populated. `X-Y` for ranges. For effect sizes, the point estimate goes in Default, the CI goes in Range.
- **Notes**: Source table/figure, conditions, caveats, subgroup.

**If a parameter varies by context**, create **one table per context** (e.g., "Modal Voice Parameters", "Breathy Voice Parameters", "Age ≥75 Subgroup", "Intention-to-Treat Analysis").

**DO NOT use matrix format** (parameters as columns, contexts as rows). The extractor expects parameters as rows.

**Measurement/data tables** use descriptive headers with units in parentheses: `F1 (Hz)`, `Duration (ms)`, `HR (95% CI)`.

### Equation Format (MANDATORY)

- One equation per `$$` block
- No prose, markdown, or headers inside `$$` blocks
- Variable definitions go in prose AFTER the equation block
- Use standard LaTeX notation

### Page Citations (MANDATORY)

**Every finding must include its page number.** You are reading page images — you know which page you are on. Tag every equation, parameter, key finding, definition, and testable property with `*(p.N)*` where N is the page number. This is not optional — downstream claim extraction depends on page provenance to produce valid claims. A finding without a page number is a finding that cannot be traced back to the source.

- Equations: `*(p.12)*` after the Where: block
- Parameters: `Page` column in the parameter table
- Key findings / contributions: `*(p.N)*` inline
- Testable properties: `*(p.N)*` at end of each bullet
- Implementation details: `*(p.N)*` at end of each bullet
- Figures: already use `(p.X)` format — keep doing this

### Extraction Targets

- **Equations / Statistical Models**: Every equation and model specification with all variables defined and units given, with page citation. Includes regression models, survival models, Bayesian specifications — not just pure math.
- **Parameters**: Every parameter, constant, threshold, dosage, effect size, and confidence interval — values, ranges, defaults, source, page
- **Effect Sizes**: Every reported effect with measure type (HR, OR, RR, RD, Cohen's d, accuracy, etc.), point estimate, CI, p-value, and population context — with page citation
- **Algorithms / Protocols**: Numbered steps with inputs, outputs, state, page citation. For clinical studies: treatment protocols, randomization procedures, endpoint adjudication criteria.
- **Testable Properties**: Bounds, monotonic relationships, invariants, clinical thresholds, NNT/NNH, subgroup interactions — with page citation

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

For chunked papers, if you can dispatch a subagent for this extraction, do so using `pngs/page-000.png` and the strongest available full-size model. Do not use a fast/mini/small model here. Otherwise, read `pngs/page-000.png` yourself and write `abstract.md`.

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

For chunked papers, if you can dispatch a subagent for this extraction, do so using the last 5-10 page images and the strongest available full-size model. Do not use a fast/mini/small model here. Otherwise, read those pages yourself and write `citations.md`.

**Steps 5 and 6 can run in parallel** since they write to different files.

---

## Step 7: Cross-Reference Collection

Invoke the **reconcile** skill on `papers/Author_Year_ShortTitle` if skill invocation is available. Otherwise, follow the reconcile skill instructions directly on that directory. This handles forward/reverse cross-referencing, reconciliation of citing papers, and backward annotations.

If nested skill invocation is unavailable or unreliable on this platform, derive this skill's
installed directory from the injected `<path>`, then run:

```bash
uv run "<skill-dir>/../reconcile/scripts/emit_nested_reconcile_fallback.py"
```

Read the FULL stdout and follow it exactly on the current paper directory instead of opening
`reconcile/SKILL.md` piecemeal.

Wait for reconcile to complete before proceeding.

---

## Step 8: Update papers/index.md

Read the paper's pretty title from its `notes.md` frontmatter first:

```bash
title=$(head -8 "papers/<Author_Year_ShortTitle>/notes.md" | grep '^title:' | sed 's/^title:[[:space:]]*//; s/^"//; s/"$//')
```

Append:
```markdown
## [<pretty title>](<Author_Year_ShortTitle>/notes.md)  (tag1, tag2, tag3)
[description.md body text — no frontmatter, no tags line]
```

The header is a **markdown link**, not plain text and not a `[[wikilink]]`. GitHub does not render wikilinks in repo files, so cross-paper references use real markdown links pointing at the target paper's `notes.md`. Display text is the pretty title from the paper's frontmatter.

**This step is NOT optional.** Without it, future sessions won't know this paper exists.

---

## Step 9: Stop At Paper Artifacts

`paper-reader` does not mutate propstore source branches. Source initialization, claim authoring, provenance on semantic assertions, and promotion are handled by later source-oriented skills.

---

## Quality Checklist

- [ ] All equations with variable definitions and page citations
- [ ] All parameters in standard table format with Page column
- [ ] Algorithm steps numbered with page citations
- [ ] Figures described with page numbers
- [ ] Key findings and testable properties have page citations
- [ ] Limitations section filled
- [ ] Testable properties extracted
- [ ] description.md written
- [ ] abstract.md written
- [ ] citations.md written
- [ ] metadata.json written
- [ ] Reconcile skill invoked
- [ ] papers/index.md updated
- [ ] Provenance stamped on notes.md
- [ ] No temp files left behind

---

## Output

All papers produce: `papers/Author_Year_Title/` containing `notes.md`, `metadata.json`, `description.md`, `abstract.md`, `citations.md`, `pngs/`, and an updated `papers/index.md` entry.

Papers >300 pages also produce `chunks/`.

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
