---
name: reconcile-vocabulary
description: Reconcile paper-local concept inventories across a paper collection. Identifies collision groups, proposes shared canonical names, and optionally rewrites per-paper concepts.yaml files.
argument-hint: "<papers-directory> [--fix] [--vocabulary <path>]"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Reconcile Vocabulary: $ARGUMENTS

Reconcile paper-local concept inventories across a paper collection.

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

Read every `concepts.yaml` file under `$papers_dir`:
```bash
find "$papers_dir" -name "concepts.yaml" -type f
```

For each file, extract all concept inventory entries:
- `local_name`
- `proposed_name`
- `definition`
- `form`
- optional observed units or notes

Build a frequency table: concept_name → {count, papers[], definitions[], forms[]}.

## Step 3: Load Vocabulary (if provided)

If `--vocabulary` was given, read the YAML file. Its `concepts` mapping provides known canonical names and their aliases.

## Step 4: Identify Collision Groups

Group concept inventory entries that may refer to the same underlying concept:

1. **Exact vocabulary matches**: If two names both appear in the vocabulary file mapping to the same canonical name, they're the same concept.
2. **String similarity**: Use token overlap (split on underscore, compare token sets). Threshold: 0.6 similarity.
3. **Abbreviation expansion**: Use the vocabulary's `abbreviations` section to expand short forms before comparison.
4. **Definition overlap**: If definitions clearly describe the same concept, group them even when local names differ.
5. **Form mismatch**: If names are similar but forms differ (`ratio` vs `structural`), keep them in the same report but flag them as contested rather than auto-merged.

For each collision group, select the canonical name:
- If the vocabulary specifies one, use it
- Otherwise, pick the most descriptive (longest) name
- List all variants as aliases
- Record per-paper source names so later alignment can map back to individual `concepts.yaml` files

## Step 5: Report

Write a report with:
- Total unique concept names found
- Number of collision groups
- For each collision group: canonical name, all variants, which papers use which variant
- Contested groups where definitions or forms disagree
- Suggested vocabulary additions (new concepts not in the vocabulary file)

## Step 6: Fix Mode (--fix)

If `--fix` was passed:
1. For each collision group that is not contested, rewrite the affected `concepts.yaml` files so `proposed_name` matches the selected canonical name
2. Preserve `local_name`, definitions, forms, and all non-name fields unchanged
3. Do NOT rewrite `claims.yaml` here; claim rewriting happens later when papers are re-extracted or re-ingested against the updated concept inventory
4. Report which `concepts.yaml` files were modified

## Output

```
Vocabulary reconciliation complete.
  Papers scanned: N
  Unique concept names: N
  Collision groups found: N
  Contested groups: N
  - [canonical_name]: [variant1] (3 papers), [variant2] (1 paper)
  ...

Report written to: reports/vocabulary-reconciliation-report.md
```
