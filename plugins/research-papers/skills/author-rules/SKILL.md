---
name: author-rules
description: Author the DeLP rules (strict, defeasible, defeater) encoding a paper's stated argument structure. Per-paper rules file in knowledge/rules/. Runs after register-predicates.
argument-hint: "<papers/Author_Year_Title>"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Author Rules: $ARGUMENTS

Encode a paper's stated argument structure as DeLP rules. Each rule has a head atom, a body of atoms, and a kind (strict, defeasible, defeater).

Use `pks rule add` (propstore >= 0.2.0). The CLI parses a shallow atom DSL, validates the schema, and commits on master. Do NOT hand-author YAML or run `git commit` yourself. Rule-priority pairs (`superiority`) are not yet exposed via CLI; if you need them, stop here and ask Q.

## Theoretical Background

Garcia & Simari 2004 DeLP:
- **Strict** rule (`L0 <- L1, ..., Ln`): indefeasible. Empty body = a fact.
- **Defeasible** rule (`L0 -< L1, ..., Ln`): tentative; can be defeated.
- **Defeater**: pure attack; body provides evidence against the head.
- **Strong negation** (`~L`) is permitted on literal heads and bodies.
- Language is safe: every variable in the head must appear in the body.

## CLI atom DSL

`pks rule add` accepts atom strings with this shape:

```
[~]predicate(term1, term2, ...)
```

- A leading `~` marks strong negation on the literal.
- Terms whose first character is uppercase are treated as variables (`X`, `Dose`); everything else is a constant.
- Quoted strings (`"low"`) and numeric literals coerce to typed constants.
- Zero-arity atoms are just `predicate` (no parens) or `predicate()`.

**CRITICAL shell-quoting:** bash expands leading `~` as a home directory. ALWAYS single-quote atoms with negation: `--head '~safe(X)'`, not `--head ~safe(X)`. When in doubt, single-quote every atom string.

## Step 0: Validate

```bash
paper_dir="$ARGUMENTS"
ls "$paper_dir"/notes.md 2>/dev/null || echo "MISSING: notes.md"
ls "$paper_dir"/claims.yaml 2>/dev/null
ls knowledge/.git 2>/dev/null || echo "MISSING: knowledge/.git"
paper_stem=$(basename "$paper_dir" | tr '[:upper:]' '[:lower:]' | cut -d_ -f1-2)
ls knowledge/predicates/${paper_stem}.yaml 2>/dev/null || echo "MISSING: predicates file — run register-predicates first"
```

If the predicates file is missing, stop and run `register-predicates` first. Rule heads and bodies must reference declared predicates.

## Step 1: Identify The Paper's Stated Reasoning Steps

Read `notes.md` and `claims.yaml`. Find the paper's core argumentative moves:

- "Because X, we conclude Y" → defeasible rule, body has X premises, head has Y.
- "Our result contradicts the expectation that Z" → defeater against Z.
- "By definition, if X then Y" → strict rule.
- "Effect A offsets benefit B, so no net gain" → defeasible rule with negated head.

## Step 2: Add Rules Via CLI

Use the file stem `<author>_<year>` (e.g. `ikeda_2014`). The first `pks rule add` call creates `knowledge/rules/<stem>.yaml` with `source.paper = <paper-directory-name>` from `--paper`; subsequent calls append (the `--paper` must match).

Conventions:

- Rule IDs: `r_<what_it_concludes>` or `r_<paper_slug>_<what>`. Stable across re-runs.
- Variables: uppercase single letters (`X`, `Y`) per DeLP convention. All head variables must appear in the body.
- Use a leading `~` (single-quoted) for strong negation. Defeaters use this pattern when the paper is arguing against a standard conclusion.

```bash
cd knowledge  # or pass -C to each pks call

# Defeasible rule: aspirin reduces MI in JPPP-like cohort
pks rule add \
  --file ikeda_2014 \
  --paper Ikeda_2014_Low-doseAspirinPrimaryPrevention \
  --id r_ikeda_mi_reduction \
  --kind defeasible \
  --head 'aspirin_reduces_nonfatal_mi(X)' \
  --body 'jppp_like_cohort(X)'

# Defeasible rule with negated head: no net benefit conclusion
pks rule add \
  --file ikeda_2014 \
  --paper Ikeda_2014_Low-doseAspirinPrimaryPrevention \
  --id r_ikeda_no_net_benefit \
  --kind defeasible \
  --head '~aspirin_has_net_benefit(X)' \
  --body 'aspirin_increases_extracranial_hemorrhage(X)' \
  --body 'aspirin_reduces_nonfatal_mi(X)'

# Defeater: paper argues against standard indication
pks rule add \
  --file ikeda_2014 \
  --paper Ikeda_2014_Low-doseAspirinPrimaryPrevention \
  --id r_ikeda_not_indicated \
  --kind defeater \
  --head '~aspirin_indicated_for_primary_prevention(X)' \
  --body '~aspirin_has_net_benefit(X)' \
  --body 'jppp_like_cohort(X)'
```

Repeat for every reasoning move you identified. Duplicate rule ids inside the same file are rejected by the CLI.

## Step 3: Verify

```bash
pks build
```

Expect `Build rebuilt:` or `Build unchanged:` with zero warnings. Common build failures at this stage:

- Head variable not in body → safety violation. Fix the rule's body to include the missing variable.
- Predicate not declared → re-run `register-predicates` for the missing one.
- Arity mismatch → rule uses wrong number of terms. Check the declared predicate's `arity` and `arg_types`.

Note: DeLP rules and predicates are not materialized as sidecar tables — they are consumed by the argumentation engine at query time (`pks world`, grounding). A successful build validates syntax; runtime argumentation is where they become visible.

## Output

```
Rules authored: knowledge/rules/<author>_<year>.yaml
  Rules: N total (one emit_success per add)
```

## When To Rerun

Rerun if you missed a reasoning move and want to add more rules. Additional `pks rule add` calls with the same `--file` (and matching `--paper`) append. One rules file per paper.

## Superiority pairs (not yet in CLI)

`RulesFileDocument.superiority` expresses `(superior_rule_id, inferior_rule_id)` pairs for explicit rule priority. No CLI surface exists yet. If a paper requires superiority, stop and ask Q — do not hand-edit the YAML.
