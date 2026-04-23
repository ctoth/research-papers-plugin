---
name: author-rules
description: Author the DeLP rules (strict, defeasible, defeater) encoding a paper's stated argument structure. Per-paper rules file in knowledge/rules/. Runs after register-predicates.
argument-hint: "<papers/Author_Year_Title>"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Author Rules: $ARGUMENTS

Encode a paper's stated argument structure as DeLP rules. Each rule has a head atom, a body of atoms, and a kind (strict, defeasible, defeater). Rule priorities are authored as explicit `(superior_rule_id, inferior_rule_id)` pairs.

No dedicated `pks rule add` CLI exists today — this skill writes YAML directly to `knowledge/rules/<author>_<year>.yaml` and commits on master.

## Theoretical Background

Garcia & Simari 2004 DeLP:
- **Strict** rule (`L0 <- L1, ..., Ln`): indefeasible. Empty body = a fact.
- **Defeasible** rule (`L0 -< L1, ..., Ln`): tentative; can be defeated.
- **Defeater**: pure attack; body provides evidence against the head.
- **Strong negation** (`~L`) is permitted on literal heads and bodies.
- Language is safe: every variable in the head must appear in the body.

Heads and bodies are atoms: predicate + terms + optional `negated: true` for strong negation. Terms are `kind: var` with a `name` (uppercase convention like `X`) or `kind: const` with a `value` (string/int/float/bool).

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

Read `notes.md` and `claims.yaml`. Find the paper's core argumentative moves — statements of the form:

- "Because X, we conclude Y" → defeasible rule, body has X premises, head has Y.
- "Our result contradicts the expectation that Z" → defeater against Z.
- "By definition, if X then Y" → strict rule.
- "Effect A offsets benefit B, so no net gain" → defeasible rule with negated head.

For each identified reasoning step, write a rule. Rules are the skeletal structure of the paper's argument — justifications (intra-paper claim-to-claim hyperedges) are richer but narrower; rules generalize over cohorts via variables.

## Step 2: Author The Rules File

Path: `knowledge/rules/<author>_<year>.yaml` (e.g., `knowledge/rules/ikeda_2014.yaml`).

Schema (`RulesFileDocument`):

```yaml
source:
  paper: <paper-directory-name>
rules:
- id: r_<short_descriptive_slug>
  kind: defeasible   # or strict, or defeater
  head:
    predicate: <predicate_name>
    terms:
    - kind: var
      name: X
    negated: false   # omit or true for strong negation ~
  body:
  - predicate: <body_predicate_1>
    terms:
    - kind: var
      name: X
  - predicate: <body_predicate_2>
    terms:
    - kind: var
      name: X
# ... more rules
superiority:
- [r_specific_rule, r_general_rule]   # first dominates second
```

Conventions:
- Rule IDs: `r_<paper_slug>_<what_it_concludes>`. Lowercase snake_case. Stable across re-runs.
- Variables: uppercase single letters (`X`, `Y`) per DeLP convention. All head variables must appear in the body.
- Use `negated: true` to express strong negation `~L`. Defeaters use this pattern when the paper is arguing against a standard conclusion.
- `superiority` is optional. Use it only when the paper explicitly argues one rule dominates another.

## Step 3: Commit

```bash
cd knowledge
git status -s   # verify nothing unexpected is staged
git add rules/<author>_<year>.yaml
git diff --cached --stat   # verify ONLY this file is staged
git commit -m "Author DeLP rules for <Author>_<Year>"
```

**Always run `git diff --cached --stat` before committing inside knowledge/.** The propstore git backend shares the index with user git commands.

## Step 4: Verify

```bash
pks build
```

Expect: `Build rebuilt:` or `Build unchanged:` with zero warnings. Build failures here usually mean:
- Rule head variable not in body → safety violation.
- Predicate not declared → run register-predicates for the missing one.
- Arity mismatch → rule uses wrong number of terms for a declared predicate.

Note: DeLP rules and predicates are not materialized as sidecar tables — they are consumed by the argumentation engine at query time (`pks world`, grounding). A successful build validates syntax; runtime argumentation is where they become visible.

## Output

```
Rules authored: knowledge/rules/<author>_<year>.yaml
  Rules: N total
    strict: X
    defeasible: Y
    defeater: Z
  Superiority pairs: M
  Commit: <sha>
```

## When To Rerun

Rerun if you missed a reasoning move and want to add more rules, or if a rule's logic was wrong. Edit the existing file and recommit — one rules file per paper.
