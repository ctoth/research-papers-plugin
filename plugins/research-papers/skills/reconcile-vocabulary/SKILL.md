---
name: reconcile-vocabulary
description: Normalize concept vocabulary across a paper collection. Identifies collision groups (same concept, different names), proposes canonical names, and optionally rewrites claims files.
argument-hint: "<papers-directory> [--fix] [--vocabulary <path>]"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Reconcile Vocabulary: $ARGUMENTS

Normalize concept names across all claims.yaml files in a paper collection.

## Step 1: Parse Arguments

```bash
papers_dir=""
fix_mode=false
vocab_path=""

for arg in $ARGUMENTS; do
  case "$arg" in
    --fix) fix_mode=true ;;
    --vocabulary) next_is_vocab=true ;;
    *)
      if [[ "$next_is_vocab" == "true" ]]; then
        vocab_path="$arg"
        next_is_vocab=false
      else
        papers_dir="$arg"
      fi
      ;;
  esac
done
```

## Step 2: Collect All Concept Names

Read every `claims.yaml` file under `$papers_dir`:
```bash
find "$papers_dir" -name "claims.yaml" -type f
```

For each file, extract all concept references:
- `concept:` field (parameter claims)
- `target_concept:` field (measurement claims)
- `concepts:` list items (observation claims)
- Variable `concept:` fields (equation claims)

Build a frequency table: concept_name → {count, papers[]}.

## Step 3: Load Vocabulary (if provided)

If `--vocabulary` was given, read the YAML file. Its `concepts` mapping provides known canonical names and their aliases.

## Step 4: Identify Collision Groups

Group concept names that refer to the same underlying concept:

1. **Exact vocabulary matches**: If two names both appear in the vocabulary file mapping to the same canonical name, they're the same concept.
2. **String similarity**: Use token overlap (split on underscore, compare token sets). Threshold: 0.6 similarity.
3. **Abbreviation expansion**: Use the vocabulary's `abbreviations` section to expand short forms before comparison.

For each collision group, select the canonical name:
- If the vocabulary specifies one, use it
- Otherwise, pick the most descriptive (longest) name
- List all variants as aliases

## Step 5: Report

Write a report with:
- Total unique concept names found
- Number of collision groups
- For each collision group: canonical name, all variants, which papers use which variant
- Suggested vocabulary additions (new concepts not in the vocabulary file)

## Step 6: Fix Mode (--fix)

If `--fix` was passed:
1. For each collision group, rewrite all claims.yaml files to use the canonical name
2. Preserve all other fields unchanged
3. Report which files were modified

## Output

```
Vocabulary reconciliation complete.
  Papers scanned: N
  Unique concept names: N
  Collision groups found: N
  - [canonical_name]: [variant1] (3 papers), [variant2] (1 paper)
  ...

Report written to: reports/vocabulary-reconciliation-report.md
```
