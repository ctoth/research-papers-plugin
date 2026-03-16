---
name: lint-paper
description: Check paper directories for completeness, format compliance, and index consistency. Run on a single paper or --all for the entire collection.
argument-hint: "<papers/Author_Year_Title> or --all"
disable-model-invocation: false
---

# Lint Paper: $ARGUMENTS

Audit paper directories for completeness and format compliance. No AI needed — just file checks and grep.

## Step 0: Determine Mode

```bash
if [[ "$ARGUMENTS" == "--all" ]]; then
  ls -d papers/*/ | grep -v "papers/tagged" | sort
else
  paper_dir="$ARGUMENTS"
fi
```

## Step 1: Check Each Paper

For each paper directory, run all checks and collect results.

### Required Files

| File | Status |
|------|--------|
| `notes.md` | REQUIRED — run paper-reader if missing |
| `description.md` | REQUIRED — run paper-reader if missing |
| `abstract.md` | recommended |
| `citations.md` | recommended |
| `paper.pdf` or `pngs/` | at least one should exist |

### Format Checks

1. **Notes metadata**: Does `notes.md` have YAML frontmatter with at least `title:` and `year:`?
   ```bash
   head -8 "$paper_dir/notes.md" | grep -E "^title:|^year:"
   ```
   Missing → report as `NOTES_METADATA_MISSING`

2. **Tags**: Does `description.md` have YAML frontmatter with a `tags:` field?
   ```bash
   head -5 "$paper_dir/description.md" | grep "tags:"
   ```
   Missing → report as `UNTAGGED`

3. **Wikilinks**: Are cross-references in `notes.md` using `[[wikilinks]]`?
   ```bash
   # Check for old-style bold refs in cross-reference sections
   grep -c '\*\*[A-Z][A-Za-z0-9_]*_[0-9]\{4\}' "$paper_dir/notes.md"
   ```
   Found → report as `LEGACY_BOLD_REFS`

4. **Frontmatter validity**:
   - If `notes.md` has `---` delimiters, is the YAML valid?
   - If `description.md` has `---` delimiters, is the YAML valid?
   - Check that `---` appears on lines 1 and 3+ (not empty frontmatter)
   - Check that `title:` is present in `notes.md`
   - Check that `tags:` value is a list, not empty in `description.md`

5. **Cross-references section**: Does `notes.md` have `## Collection Cross-References`?
   ```bash
   grep -c "## Collection Cross-References" "$paper_dir/notes.md"
   ```
   Missing → report as `NOT_RECONCILED`

### Index Checks

6. **In index**: Is the paper listed in `papers/index.md`?
   ```bash
   grep -c "## $(basename $paper_dir)" papers/index.md
   ```
   Missing → report as `NOT_INDEXED`

7. **Index description matches**: Does the description in `index.md` match `description.md`?
   Only check if both exist — flag `INDEX_STALE` if they differ.

### Source Checks

8. **Orphan PDF**: Is there a PDF in `papers/` root with a name matching this paper?
   ```bash
   ls papers/*.pdf 2>/dev/null
   ```
   Any root-level PDFs → report as `ORPHAN_PDF` (should have been moved by paper-reader)

## Step 2: Report

### Single Paper Mode

```
Lint: papers/Author_Year_Title/
  ✓ notes.md
  ✓ description.md
  ✓ abstract.md
  ✗ citations.md — MISSING
  ✓ paper.pdf
  ✗ notes metadata — NOTES_METADATA_MISSING
  ✗ tags — UNTAGGED
  ✓ wikilinks
  ✗ cross-references — NOT_RECONCILED
  ✓ indexed
```

### --all Mode

Group by status:

```
Lint: N papers checked

Complete (M papers):
  - Paper1, Paper2, ...

Issues found:

  MISSING notes.md (need paper-reader):
    - Paper3

  MISSING description.md (need paper-reader):
    - Paper4

  NOTES_METADATA_MISSING (need migrate_notes_frontmatter.py or re-run paper-reader):
    - Paper4a

  UNTAGGED (need tag-papers):
    - Paper5, Paper6, Paper7, ...

  NOT_RECONCILED (need reconcile):
    - Paper8, Paper9

  LEGACY_BOLD_REFS (need migrate-format.py):
    - Paper10

  NOT_INDEXED (need generate-paper-index.py):
    - Paper11

  ORPHAN_PDF (unprocessed PDFs in papers/ root):
    - somefile.pdf
```

Then a summary line:
```
Summary: M complete, N issues across K papers
```

## Do NOT:

- Modify any files (this is read-only audit)
- Read PDF content or page images
- Use AI/LLM features (this is pure file/grep checks)
