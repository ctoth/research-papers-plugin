---
name: write-lit-review
description: Write a standalone literature review (--mode full) or an introduction + related-work section (--mode intro) from the processed paper collection, driven by the vendored house writing guides. Cites only @keys that resolve in papers/, then runs the presence and reality gates before declaring done.
argument-hint: "--mode full|intro [topic or one-line paper description]"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Write Lit Review: $ARGUMENTS

Author one of two deliverables from the **already-processed** `papers/` collection,
following the house writing guides vendored alongside this skill:

- `--mode full` — a standalone literature review (survey / related-work paper).
- `--mode intro` — an Introduction **plus** a Related Work section for a paper.

This skill **writes**; the gates verify. The phrasing banks in the guides are
load-bearing house style — read them, do not paraphrase them. Cite **only** `@key`s
that resolve to a real, complete paper in `papers/`; the gates in Step 6 block on any
citation that is absent or not real.

## Step 0: Parse mode

```bash
case "$ARGUMENTS" in
  *"--mode full"*)  MODE=full ;;
  *"--mode intro"*) MODE=intro ;;
  *) echo "Specify --mode full or --mode intro"; exit 2 ;;
esac
```

Pick the deliverable folder (default a new `reports/<slug>/` or a path the caller
gave). It will hold the markdown draft and a self-contained `citations.bibtex`.

## Step 1: Read the relevant vendored guide (in full)

Read the whole guide before drafting — the structure, phrasing banks, and checklists
are the method:

- `--mode full` → `guides/writing_full_paper_literature_reviews.md`
  (review-type selection, the eight phases, canonical ACM/IEEE structure, the
  expected tables/figures, the top rejection trigger, tone, pre-submission checklist).
- `--mode intro` → `guides/writing_intro_paper_literature_reviews.md`
  (synthesis-not-summary, the CARS structure, the verbatim phrasing banks for the
  Introduction and the Related Work section, the intake questions, the generation
  protocols, and the per-section checklists).

These are vendored copies; never read a machine-local `odrive` path.

**How strong introductions open (exemplar dissection, summarized from the intro
guide §10).** The exemplars funnel from territory to gap to contribution on page one:
establish why the problem matters and who it excludes (Move 1), name the specific gap
in one sentence ("to our knowledge, no existing technique has…", "little has been
investigated regarding…"), then state the aim and an enumerated, refutable
contribution list with a short roadmap (Move 3). Synthesis carries grouped citations
(`[4–6]`), not a citation per clause. Reproduce that shape; read §10–§11 for the
annotated originals.

## Step 2: Intake (answer before drafting)

Run the intake questions from the guide and **do not invent** load-bearing facts:

- `--mode intro` — the intro guide §12: the topic in one sentence; the research
  question / hypothesis; the core contribution; the method/type; the headline result;
  the specific gap; the 2–5 closest prior works to differentiate; any "first to"
  claim; the length budget; whether a separate Related Work section exists; must-cite
  seminal + recent works; constraints.
- `--mode full` — the full guide §3.1 (research questions) and §1 (review type):
  the review type, the research questions, the venue family (ACM or IEEE), scope and
  inclusion/exclusion criteria, the intended taxonomy axis.

If any of the research question, contribution, or length budget is missing, **ask the
author** rather than guessing.

## Step 3: Select the relevant papers from the collection

Select candidates by tag/topic — reuse the existing registry, do not invent a new index:

```bash
sed -n '1,200p' papers/index.md           # titles + one-line descriptions + tags
test -f papers/tags.yaml && cat papers/tags.yaml   # canonical tags to match against
```

For each candidate, read its `notes.md` and `abstract.md` (the notes layer exists to
be written from). Build the working set you will synthesize. Confirm each intended
`@key` resolves to a directory via `papers/keymap.tsv` (`build_keymap.py build` to
refresh) — a key that does not resolve must not be cited.

## Step 4: Draft, citing only resolvable keys

Draft using the guide's structure and phrasing bank:

- `--mode intro` — the intro guide §13 generation protocol: Move 1 (territory) →
  Move 2 (the gap, by neutral contrast) → Move 3 (occupation: aim + enumerated
  contributions + roadmap); then structure the Related Work section per §16/§21.
- `--mode full` — the full guide §4 canonical structure and §3.7–§3.8 (taxonomy then
  synthesis). The single most common rejection trigger (§6) is **summary instead of
  synthesis**: every claim carries grouped citations, organized by idea, not a
  paper-by-paper list.

House rules: synthesis not summary; gap-framing without strawmanning; pandoc `@key`
citations only; no invented statistics or citations; remove every em-dash.

## Step 5: Assemble `citations.bibtex`

Build the deliverable's self-contained bibliography from exactly the keys you cited:

```bash
PYTHON=$(command -v python3 || command -v python)
# Option A: filter the collection BibTeX to the cited keys.
uv run scripts/export_bibtex.py --papers-dir papers/ > /tmp/all.bib
# Option B: scaffold from the draft's cited keys, then fill each entry.
"$PYTHON" scripts/lit_review.py build "<deliverable-folder>" > "<deliverable-folder>/citations.bibtex"
```

Every cited `@key` must have an entry; every entry should be cited (no orphans).

## Step 6: Gates (ALL must pass before declaring done)

Run the gates **in order**. Any non-zero exit is a hard blocker — fix and re-run.

```bash
PYTHON=$(command -v python3 || command -v python)
D="<deliverable-folder>"

# 6a. F2 presence gate: every cited key in BOTH citations.bibtex AND papers/.
uv run scripts/lit_review.py gate "$D" --papers-dir papers/ ; echo "presence=$?"

# 6b. Symmetry + word count + em-dashes.
"$PYTHON" scripts/lit_review.py verify "$D" ; echo "verify=$?"

# 6c. Faithfulness: grade each citing sentence against the cited paper's notes.
#     Invoke the verify-citations skill on the draft.

# 6d. F7 reality check: confirm every citation is a real paper (no hallucinations).
uv run scripts/verify_citations_real.py "$D/citations.bibtex" --papers-dir papers/ ; echo "real=$?"
```

- **6a `MISSING_FROM_PAPERS` / `MISSING_FROM_BIBTEX`** → add/retrieve the paper, fix
  the bibtex, or remove the citation. Do not cite what was never processed.
- **6c** → run `/research-papers:verify-citations <draft.md>` and resolve any
  `UNSUPPORTED` / `MISATTRIBUTED` verdict.
- **6d `MISMATCH` / `NOT_FOUND`** → fix the metadata, replace the citation, or remove
  it from **both** the bibliography and the document.

Declare the deliverable done only when 6a–6d all pass. Report the deliverable path and
a one-line status for each gate.

## Do NOT:

- Cite a `@key` that does not resolve to a complete paper in `papers/`.
- Invent statistics, numbers, "first to" claims, or bibtex entries.
- Paraphrase the phrasing banks, or read a machine-local guide path instead of the
  vendored `guides/`.
