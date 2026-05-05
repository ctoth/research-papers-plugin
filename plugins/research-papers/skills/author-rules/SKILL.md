---
name: author-rules
description: Author the DeLP rules (strict, defeasible, proper_defeater, blocking_defeater) encoding a paper's stated argument structure. Per-paper rules file in knowledge/rules/. Runs after register-predicates.
argument-hint: "<papers/Author_Year_Title>"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Author Rules: $ARGUMENTS

Encode a paper's stated argument structure as DeLP rules. Each rule has a head atom, a body of atoms, and a kind (strict, defeasible, proper_defeater, blocking_defeater).

Use `pks rule add` (propstore >= 0.2.0). The CLI parses a shallow atom DSL, validates the schema, and commits on master. Do NOT hand-author YAML or run `git commit` yourself. Rule-priority pairs (`superiority`) are not yet exposed via CLI; if you need them, stop here and ask Q.

## Theoretical Background

Garcia & Simari 2004 DeLP:
- **Strict** rule (`L0 <- L1, ..., Ln`): indefeasible. Empty body = a fact.
- **Defeasible** rule (`L0 -< L1, ..., Ln`): tentative; can be defeated.
- **Proper defeater** (`--kind proper_defeater`): the head literal directly contradicts the conclusion of the rule it attacks. The attacked rule has head `L`; the defeater's head is `~L`. Use this when the paper argues *against* the standard conclusion with a counter-conclusion of its own (the common case).
- **Blocking defeater** (`--kind blocking_defeater`): the body provides counter-evidence that undermines a *premise* of the attacked argument. The head doesn't necessarily contradict the attacked conclusion directly — it just blocks the attacked argument from going through. Use when the paper undercuts a premise rather than asserting the opposite conclusion.
- **Strong negation** (`~L`) is permitted on literal heads and bodies.
- Language is safe: every variable in the head must appear in the body.

**Choosing proper vs blocking:** if the paper says "the standard conclusion C is wrong, the truth is ~C" -> `proper_defeater` with head `~C`. If the paper says "the argument for C relies on premise P, and P doesn't hold here" -> `blocking_defeater` whose body asserts `~P` (or evidence against P).

## CLI atom DSL

`pks rule add` accepts atom strings with this shape:

```
[~]predicate(term1, term2, ...)
```

- A leading `~` marks strong negation on the literal.
- Terms whose first character is uppercase are treated as variables (`X`, `Dose`); everything else is a constant.
- Quoted strings (`"low"`) and numeric literals coerce to typed constants.
- Zero-arity atoms are just `predicate` (no parens) or `predicate()`.

**CRITICAL flag form — use `--head=<atom>` and `--body=<atom>`, NOT `--head <atom>`:**

The separate-argument form (`--head '~safe(X)'`) is broken on Windows regardless of quoting style — `pks` receives the `~` as the start of a path token and expands it to the user home directory, producing `C:\Users\...safe(X)`. Single-quoting in bash does not prevent this; PowerShell does not prevent this; backslash-escaping does not prevent this. The expansion is inside the pks launcher, past the shell.

The equals-form (`--head=~safe(X)`, `--body=~p(X)`) bypasses the expansion entirely and is portable. Use it for every `--head` and `--body` value, with or without a leading `~`.

**Additional shell-quoting note for Git Bash / MSYS on Windows:** parentheses in the atom payload (`pred(X)`) trigger bash's subshell grouping, producing `syntax error near unexpected token '('`. Wrap the whole flag token in double quotes: `"--head=~pred(X)"`, `"--body=pred(X,Y)"`. The `~` is still not expanded (it's not a standalone token after `=`), and the parens are protected:

```bash
pks rule add \
  --file ikeda_2014 \
  --paper Ikeda_2014_Low-doseAspirinPrimaryPrevention \
  --id r_ikeda_not_indicated \
  --kind proper_defeater \
  --head=~aspirin_indicated_for_primary_prevention(X) \
  --body=~aspirin_has_net_benefit(X) \
  --body=jppp_like_cohort(X)
```

Do NOT fall back to positive-encoding predicates (e.g. `aspirin_not_indicated/1` instead of `~aspirin_indicated/1`) just to avoid `~`. That loses strong negation semantics. Use the equals form and keep the negation.

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
- "Our result contradicts the expectation that Z" → `proper_defeater` with head `~Z`.
- "The argument for Z assumes premise P, which doesn't hold here" → `blocking_defeater` whose body asserts `~P`.
- "By definition, if X then Y" → strict rule.
- "Effect A offsets benefit B, so no net gain" → defeasible rule with negated head.

## Step 2: Add Rules Via CLI

Use the file stem `<author>_<year>` (e.g. `ikeda_2014`). The first `pks rule add` call creates `knowledge/rules/<stem>.yaml` with `source.paper = <paper-directory-name>` from `--paper`; subsequent calls append (the `--paper` must match).

Conventions:

- Rule IDs: `r_<what_it_concludes>` or `r_<paper_slug>_<what>`. Stable across re-runs.
- Variables: uppercase single letters (`X`, `Y`) per DeLP convention. All head variables must appear in the body.
- Use a leading `~` for strong negation. Proper defeaters use this pattern when the paper is arguing against a standard conclusion (head `~L` directly contradicts the attacked rule's head `L`). Blocking defeaters typically negate a premise of the attacked argument in the body instead. **Always use the `--head=<atom>` / `--body=<atom>` equals-form** (see CLI atom DSL above for why).

```bash
cd knowledge  # or pass -C to each pks call

# Defeasible rule: aspirin reduces MI in JPPP-like cohort
pks rule add \
  --file ikeda_2014 \
  --paper Ikeda_2014_Low-doseAspirinPrimaryPrevention \
  --id r_ikeda_mi_reduction \
  --kind defeasible \
  --head=aspirin_reduces_nonfatal_mi(X) \
  --body=jppp_like_cohort(X)

# Defeasible rule with negated head: no net benefit conclusion
pks rule add \
  --file ikeda_2014 \
  --paper Ikeda_2014_Low-doseAspirinPrimaryPrevention \
  --id r_ikeda_no_net_benefit \
  --kind defeasible \
  --head=~aspirin_has_net_benefit(X) \
  --body=aspirin_increases_extracranial_hemorrhage(X) \
  --body=aspirin_reduces_nonfatal_mi(X)

# Proper defeater: paper argues against standard indication with a counter-conclusion
pks rule add \
  --file ikeda_2014 \
  --paper Ikeda_2014_Low-doseAspirinPrimaryPrevention \
  --id r_ikeda_not_indicated \
  --kind proper_defeater \
  --head=~aspirin_indicated_for_primary_prevention(X) \
  --body=~aspirin_has_net_benefit(X) \
  --body=jppp_like_cohort(X)
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
