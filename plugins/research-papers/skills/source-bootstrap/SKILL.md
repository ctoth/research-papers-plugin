---
name: source-bootstrap
description: Initialize a propstore source branch for an extracted paper directory and write notes plus metadata into that source branch.
argument-hint: "<papers/Author_Year_Title>"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Source Bootstrap: $ARGUMENTS

Initialize the propstore source branch for one extracted paper directory.

## Step 0: Validate Inputs

```bash
paper_dir="$ARGUMENTS"
ls "$paper_dir"/paper.pdf 2>/dev/null || echo "MISSING: paper.pdf"
ls "$paper_dir"/notes.md 2>/dev/null || echo "MISSING: notes.md"
ls "$paper_dir"/metadata.json 2>/dev/null || echo "MISSING: metadata.json"
ls knowledge/.git 2>/dev/null || echo "MISSING: knowledge/.git"
```

If `paper.pdf`, `notes.md`, or `metadata.json` is missing, stop and report the missing artifact.
If `knowledge/.git` is missing, stop and report: `No propstore found. Run pks init first.`

## Step 1: Derive Source Identity

```bash
source_name=$(basename "$paper_dir")
```

Read `metadata.json` and pick the strongest available origin in this order:

1. DOI → `--origin-type doi`, value is the bare DOI (e.g. `10.1145/1142351.1142399`)
2. local file path → `--origin-type file`, value is the path
3. anything else (arXiv ID, URL, CEUR-WS link, etc.) → `--origin-type manual`, value is the canonical URL or identifier

The CLI's `SourceOriginType` enum accepts only `doi | file | manual`. arXiv IDs and bare URLs route through `manual`.

## Step 2: Initialize The Source Branch

```bash
pks source init "$source_name" \
  --kind academic_paper \
  --origin-type <doi|file|manual> \
  --origin-value "<value>" \
  --content-file "$paper_dir/paper.pdf"
```

## Step 3: Write Notes And Metadata

```bash
pks source write-notes "$source_name" --file "$paper_dir/notes.md"
pks source write-metadata "$source_name" --file "$paper_dir/metadata.json"
```

## Output

Report the source name and whether `pks source init`, `pks source write-notes`, and `pks source write-metadata` succeeded.
