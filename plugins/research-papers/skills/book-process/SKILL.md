---
name: book-process
description: Process a book as a parent folder of per-chapter papers plus the whole book. Selects the lit-review-relevant chapters, processes each as its own full paper under chapters/, processes the whole book briefly, and writes a book-level index.md chapter map. One BibTeX entry per chapter (@incollection) plus one @book.
argument-hint: "<book.pdf or papers/Author_Year_Book/> [--topic \"<lit-review topic>\"]"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Book Process: $ARGUMENTS

Process a book so each relevant chapter becomes its **own full paper** nested under
the book directory, alongside a brief whole-book paper and a chapter `index.md`. The
exported BibTeX then carries one `@incollection` per chapter plus one `@book`.

Target layout:

```
papers/Geertz_1973_Interpretation/            # whole book — document_type: book
  paper.pdf  notes.md  abstract.md  metadata.json  index.md   # index.md = chapter map
  chapters/
    Geertz_1973_ThickDescription/             # full per-chapter paper — book_chapter
      notes.md  abstract.md  citations.md  metadata.json
    Geertz_1973_DeepPlay/
      notes.md  abstract.md  citations.md  metadata.json
```

## Step 1: Resolve the book and read its TOC

Retrieve the book if given an identifier (use `paper-retriever`), then render the
front matter / table of contents. The embedded TOC drives chapter scoping
(`render_pages.resolve_chapter_range`, already used by `paper-reader --chapter`).

Choose the **book directory name = the book's cite_key** (F4: `dir == cite_key`),
e.g. `Geertz_1973_Interpretation`.

## Step 2: Select the relevant chapters

If `--topic` is given, pick the chapters relevant to that lit-review topic by reading
the TOC and chapter openings. If no topic is given, **default to all chapters**:

```bash
PYTHON=$(command -v python3 || command -v python)
# select_chapters returns all chapters when no topic is supplied; topic relevance is
# the judgment you apply while reading the TOC.
```

Each selected chapter gets a **chapter cite_key** = `LastName_Year_2-4WordTitle` of
the chapter (its own dir name; `dir == cite_key`).

## Step 3: Process each selected chapter as a full paper

For each selected chapter, scaffold its nested paper dir and run `paper-reader` scoped
to that chapter's page range, writing the full required file set
(`notes.md`, `abstract.md`, `citations.md`, `metadata.json`):

```bash
PYTHON=$(command -v python3 || command -v python)
BOOK="papers/Geertz_1973_Interpretation"

# Lay down the chapter dir + metadata skeleton (cite_key first, document_type
# book_chapter, parent_book set). Pass the chapter's bibliographic fields.
"$PYTHON" - <<'PY'
import json, sys
sys.path.insert(0, "scripts")
import book_scaffold as bs
bs.scaffold_chapter("papers/Geertz_1973_Interpretation", "Geertz_1973_ThickDescription", {
    "title": "Thick Description", "authors": ["Clifford Geertz"], "year": "1973",
    "container_title": "The Interpretation of Cultures", "publisher": "Basic Books",
    "address": "New York", "pages": "3-30",
})
PY
```

Then invoke `paper-reader` with `--chapter "<chapter title or N>"` (or
`--pages <start-end>`) so it ingests only that chapter into the chapter dir and writes
the full file set. `metadata.json` carries `document_type: book_chapter`,
`container_title`, `chapter`, `pages`, `publisher`, `address`, and the chapter
`cite_key`. The chapter dir name must equal its cite_key.

Repeat for every selected chapter.

## Step 4: Process the whole book (brief)

Process the whole book into the **parent** dir with `document_type: book`: a verbatim
`abstract.md` and a **short** whole-book `notes.md` summary (not a chapter dump —
depth lives in the per-chapter papers). `paper.pdf` stays the whole book.

## Step 5: Write the chapter index.md

Generate the book-level `index.md` (one linked row per chapter with a one-line
description):

```bash
PYTHON=$(command -v python3 || command -v python)
"$PYTHON" scripts/book_scaffold.py index "papers/Geertz_1973_Interpretation/" \
  > "papers/Geertz_1973_Interpretation/index.md"
```

## Step 6: Refresh discovery surfaces

Refresh the keymap and the collection index so the book and every chapter are
discoverable (discovery is recursive — F1):

```bash
PYTHON=$(command -v python3 || command -v python)
"$PYTHON" scripts/build_keymap.py build --papers-dir papers/ -o papers/keymap.tsv
uv run scripts/generate-paper-index.py .
```

Append a `_reader_done.tsv` line (`cite_key<TAB>dir`) for the book and for each
chapter (the chapter `dir` is its `Book/chapters/<chapter>` relative path) so the
collection counts stay consistent (the F3 `COUNT_MISMATCH` gate counts chapters).

## Step 7: Verify

Run the completeness gate; it now discovers nested chapters and must pass:

```bash
uv run scripts/lint_paper_schema.py . ; echo "exit=$?"   # 0 = complete
uv run scripts/export_bibtex.py --papers-dir papers/ | grep -E '@(book|incollection)\{'
```

The export must contain one `@book` for the book and one `@incollection` per chapter,
each keyed by its `cite_key`.

## Do NOT:

- Flatten chapters into a single paper dir, or store chapter content as notes
  fragments — each chapter is a full paper directory under `chapters/`.
- Name a chapter dir anything other than its `cite_key`.
- Duplicate every chapter's depth into the whole-book `notes.md`; keep it brief.
