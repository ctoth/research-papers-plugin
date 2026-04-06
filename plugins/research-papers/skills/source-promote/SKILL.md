---
name: source-promote
description: Promote a fully prepared propstore source branch for one paper directory into master.
argument-hint: "<papers/Author_Year_Title>"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Source Promote: $ARGUMENTS

Promote one paper's source branch into master.

## Step 0: Validate

```bash
paper_dir="$ARGUMENTS"
ls knowledge/.git 2>/dev/null || echo "MISSING: knowledge/.git"
source_name=$(basename "$paper_dir")
```

If `knowledge/.git` is missing, stop and report: `No propstore found. Run pks init first.`

## Step 1: Promote

```bash
pks source promote "$source_name"
```

If promotion fails, report the exact error instead of inventing a workaround.

## Output

Report whether `pks source promote` succeeded for the source branch.
