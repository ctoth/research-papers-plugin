---
name: register-predicates
description: Author the DeLP/Datalog predicate declarations a paper's rules will use. Per-paper predicates file in knowledge/predicates/. Required before author-rules if the paper's rules reference predicates not yet declared.
argument-hint: "<papers/Author_Year_Title>"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Register Predicates: $ARGUMENTS

Declare the DeLP predicates a paper's rules will use. Predicates carry a name, arity, per-argument sort, optional description, and optional `derived_from` grounding DSL.

No dedicated `pks predicate add` CLI exists today — this skill writes YAML directly to `knowledge/predicates/<author>_<year>.yaml` and commits on master.

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

## Step 3: Write The Predicates File

Path: `knowledge/predicates/<author>_<year>.yaml` (e.g., `knowledge/predicates/ikeda_2014.yaml`).

Schema (`PredicatesFileDocument`):

```yaml
predicates:
- id: <predicate_name>
  arity: <int>
  arg_types:
  - <sort_1>
  - <sort_2>
  description: <one-sentence human description>
- id: <next_predicate>
  arity: <int>
  arg_types:
  - <sort>
  description: <...>
```

Optional fields per predicate:
- `derived_from: <dsl-string>` — how propstore should materialize ground atoms from repo data. Recognised forms live in `propstore.grounding.predicates`. Omit if you're authoring abstract (non-grounded) predicates whose truth will be asserted by rules, not data.

## Step 4: Commit

```bash
cd knowledge
git status -s   # verify nothing unexpected is staged
git add predicates/<author>_<year>.yaml
git diff --cached --stat   # verify ONLY this file is staged
git commit -m "Author DeLP predicates for <Author>_<Year>"
```

**Always run `git diff --cached --stat` before committing inside knowledge/.** The propstore git backend shares the index with user git commands, and an unchecked commit can accidentally include prior pending mutations from pks.

## Step 5: Verify

```bash
pks build
```

Expect: `Build rebuilt:` or `Build unchanged:` with zero warnings. If build fails, the predicates file has a schema error — fix and recommit.

## Output

```
Predicates registered: knowledge/predicates/<author>_<year>.yaml
  Predicates: N total
  Commit: <sha>
```

## When To Rerun

Rerun this skill if author-rules needs predicates you haven't declared. Add new predicates to the existing file (edit + recommit) rather than creating multiple files per paper — one predicates file per paper is the convention.
