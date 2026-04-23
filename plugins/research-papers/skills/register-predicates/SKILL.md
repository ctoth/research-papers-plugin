---
name: register-predicates
description: Author the DeLP/Datalog predicate declarations a paper's rules will use. Per-paper predicates file in knowledge/predicates/. Required before author-rules if the paper's rules reference predicates not yet declared.
argument-hint: "<papers/Author_Year_Title>"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Register Predicates: $ARGUMENTS

Declare the DeLP predicates a paper's rules will use. Predicates carry a name, arity, per-argument sort, optional description, and optional `derived_from` grounding DSL.

Use `pks predicate add` (propstore >= 0.2.0). The CLI handles YAML authoring, schema validation, and git commit uniformly. Do NOT hand-author YAML or run `git commit` yourself.

## Theoretical Background

DeLP (Garcia & Simari 2004) and the Diller/Borg/Bex 2025 grounding work require every rule atom to reference a declared predicate. The declaration fixes arity and per-position sort, which the grounder uses to enumerate well-typed Herbrand substitutions. Arity 0 is admitted as propositional facts; arity 1 (`bird/1`) is the canonical defeasible-reasoning example.

## Step 0: Validate

```bash
paper_dir="$ARGUMENTS"
ls "$paper_dir"/notes.md 2>/dev/null || echo "MISSING: notes.md"
ls knowledge/.git 2>/dev/null || echo "MISSING: knowledge/.git"
```

## Step 1: Derive Predicate Set From Notes

Read `notes.md`. Identify the paper's causal, mechanistic, or clinical predicates — the atomic predicates the paper's stated reasoning steps turn on. Examples for RCT papers:

- Cohort predicates: `<paper>_like_cohort/1` — "the subject belongs to a cohort like this paper's."
- Effect predicates: `intervention_reduces_endpoint/1`, `intervention_increases_endpoint/1`, `intervention_has_net_benefit/1`.
- Indication predicates: `intervention_indicated_for_<use_case>/1`.

Arity selection: most clinical-paper predicates are unary (parameterized by cohort). Binary may appear for relations (`supersedes/2`). Arity 0 is for global propositional facts.

Prefer DESCRIPTIVE predicate names over abstract ones. `aspirin_reduces_nonfatal_mi/1` beats `reduces/3`.

## Step 2: Choose arg_types

`arg_types` is a tuple of sort names, one per position. For cohort-style unary predicates, use `entity` (the propstore seed concept for generic entities). For domain-specific sorts, use a concept name that exists in the registry.

## Step 3: Register Predicates Via CLI

Use the file stem `<author>_<year>` (e.g., `ikeda_2014`). The first `pks predicate add` call creates `knowledge/predicates/<stem>.yaml`; subsequent calls append to it. Duplicate predicate ids inside the same file are rejected.

```bash
cd knowledge  # or pass -C to each pks call

pks predicate add \
  --file ikeda_2014 \
  --id aspirin_reduces_nonfatal_mi \
  --arity 1 \
  --arg-type entity \
  --description "Aspirin reduces the rate of non-fatal myocardial infarction in this cohort."

pks predicate add \
  --file ikeda_2014 \
  --id jppp_like_cohort \
  --arity 1 \
  --arg-type entity \
  --description "Subject belongs to a cohort comparable to the JPPP trial."
```

Optional flags:

- `--derived-from <dsl-string>` — how propstore should materialize ground atoms from repo data. Recognised forms live in `propstore.grounding.predicates`. Omit for abstract (non-grounded) predicates whose truth will be asserted by rules, not data.
- `--description` — short human-readable explanation. Always supply for RCT predicates.

## Step 4: Verify

```bash
pks build
```

Expect: `Build rebuilt:` or `Build unchanged:` with zero warnings. If build fails, a predicate declaration has a schema error — diagnose and re-run `pks predicate add` with corrections.

## Output

```
Predicates registered: knowledge/predicates/<author>_<year>.yaml
  Predicates: N total (one emit_success per add)
```

## When To Rerun

Rerun this skill if author-rules needs predicates you haven't declared. Use additional `pks predicate add` calls with the same `--file` to append — one predicates file per paper is the convention. Duplicate ids inside a single file are rejected by the CLI.
