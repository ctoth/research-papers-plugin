---
name: author-lifting-rules
description: Author DeLP/McCarthy context lifting rules between existing context YAMLs so cross-context claim reasoning can proceed. Collection-level, runs after all papers are ingested. Targets the CONTEXT_PHI_NODE records that accumulate when multiple per-paper contexts share concepts with no authored bridges.
argument-hint: "[knowledge-root]"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Author Lifting Rules

Author the bridges between per-paper contexts so claims in one context can be lifted into another for commensurable comparison. Without these, the conflict detector correctly classifies every cross-context claim pair on a shared concept as `CONTEXT_PHI_NODE` — informational, not a defeat. Authoring lifting rules is what turns those into either compatible lifts (silent) or real cross-context `CONFLICT` records (with defeats).

Use `pks context lifting add` (propstore >= 0.2.2 with context lifting CRUD landed). The CLI writes the rule into the TARGET context's YAML, validates the schema, and commits. Do NOT hand-author YAML or run `git commit` yourself.

## Theoretical Background

- **McCarthy 1993** ("Notes on Formalizing Context"): `ist(c, p)` — propositions are context-qualified. Cross-context comparison requires explicit lifting.
- **Guha 1991** ("Contexts: A Formalization and Some Applications"): lifting rules are authored bridges between contexts, mode-bearing — decontextualization drops context-specific constraints to reach a more general frame; bridge rules assert commensurability without subsumption; specialization imports from a broader context into a narrower one.
- **Giunchiglia & Serafini 1994** (Multi-Context Systems): local models are local; only authored bridge rules let propositions move between them.
- **Bozzato, Eiter, Serafini 2018** (CKR): justifiable exceptions extend lifting with defeasibility.

Propstore's lifting-rule schema (`LiftingRuleDocument`) carries: `id, source, target, conditions (CEL), mode ∈ {bridge | specialization | decontextualization}, justification`. Rules live INSIDE the target context's YAML. Every lift is authored — propstore never fabricates a bridge.

## Lifting modes

Pick the mode that matches the relationship between source and target contexts per the Guha 1991 / Serafini-Tamilin taxonomy:

- **`bridge`** (default): two contexts are commensurable on shared concepts without one subsuming the other. Use when neither context is a generalization of the other but specific propositions are cross-applicable.
- **`specialization`**: the SOURCE context is a specialization of the TARGET. Target is broader, source is narrower. A claim that holds in the narrower source also holds in the broader target (under the authored conditions).
- **`decontextualization`** (Guha): the SOURCE drops context-specific constraints to land in the TARGET — the classical "lifting" move that removes a context's restrictions to reach a more general frame.

The mode flows into how the conflict detector and argumentation engine treat the lifted claim at runtime. Pick based on the authored semantics of the two contexts, not on a pattern template.

## Step 0: Validate

```bash
pks context list                              # ≥ 2 contexts to bridge
pks context lifting list                      # what's already authored
pks build                                     # baseline must be green
```

If `pks context lifting list` already shows a rule between a pair you're about to author, inspect before overwriting: `pks context lifting show TARGET_CTX --rule-id R_ID`.

## Step 1: Read the contexts

Read every `knowledge/contexts/*.yaml` file in full — description, assumptions, parameters, perspective. Also sample claims in each context via `pks claim list --limit N` and `pks claim show <id>`. The bridges you author should be grounded in what the contexts actually assert, not in a template. A lift is a semantic commitment that authored claim material in the source justifies entering claim material into the target; you cannot make that commitment without reading the sources.

## Step 2: Author one lifting rule at a time

For each bridge you identify:

```bash
pks context lifting add TARGET_CTX_NAME \
  --rule-id r_lift_<short_descriptive_slug> \
  --source SOURCE_CTX_NAME \
  --mode <bridge|specialization|decontextualization> \
  [--condition "<CEL guard>"] \
  [--condition "<additional CEL guard>"] \
  --justification "<one-sentence authored rationale>"
```

Notes:

- `TARGET_CTX_NAME` (positional) is the TARGET — the context whose YAML hosts the rule.
- `--source` is the SOURCE context.
- `--rule-id` should be stable across re-runs; re-running is idempotent if ids match.
- `--condition` is a CEL expression that must hold for the lift to fire. Repeat the flag for multiple conditions (all must hold). **Conditions are the mechanism that propagates propositions between contexts** — an empty-conditions lift marks the pair as context-reachable but does not rewrite any claim conditions, so the conflict detector still sees the trial-specific conditions as disjoint and classifies cross-context pairs as regime-split PHI_NODEs. If you want the argumentation layer to produce cross-context CONFLICT records, you must author conditions that make the claim-level conditions align.
- `--justification` is authored reasoning text for audit. Always supply.

Use `--dry-run` the first time to preview without writing.

## Step 3: Verify

```bash
pks context lifting list                      # inspect the bridge graph
pks context lifting list --target TARGET_CTX  # target-scoped
pks build                                     # must still be green
pks claim conflicts 2>&1 | awk '{print $1}' | sort | uniq -c
```

Expect `pks build` to report zero warnings. The conflict-class breakdown is the semantic signal:

- **CONTEXT_PHI_NODE** count drops when new lifts connect previously-isolated contexts.
- **PHI_NODE** count (condition-based regime split) may or may not drop depending on whether your `--condition` rewrites actually align claim-level conditions.
- **CONFLICT** records appear only when lifted claims collide under identical conditions — this requires `--condition` expressions that carry the alignment.
- **OVERLAP** records appear for partial condition agreement with differing values.

Review the actual records — `pks claim conflicts | grep CONFLICT`, `pks claim conflicts | grep OVERLAP` — and sanity-check them against the contexts you lifted from and to. An empty CONFLICT list after authoring lifts means either no substantive disagreement exists across your corpus, or your lifts lack the condition rewrites needed to surface it. Do not treat "N rules authored" as the deliverable; `pks claim conflicts` output is.

## Step 4: Report

Write a short report to `reports/lifting-rules-<YYYY-MM-DD>.md` listing:

- Each authored rule (id, source, target, mode, justification).
- Before/after `CONTEXT_PHI_NODE` count.
- Any new `CONFLICT` records surfaced (these are the cross-context disagreements worth adjudicating).
- Any lifting rules considered but NOT authored (and why) — these are future-work candidates.

## When To Rerun

- A new paper lands in the corpus → author lifts from its context (if appropriate).
- A new meta-context or shared frame is authored → populate inbound lifts.
- Semantic refinement: if `--condition` was omitted initially, add a guard via `pks context lifting update`.

Do NOT delete existing lifts just because they don't fire — unused lifts are authored commitments and belong in the record.

## Forbidden

- Do NOT hand-edit context YAMLs to add lifting rules. Use the CLI.
- Do NOT author reciprocal bridges (`A→B` and `B→A`) unless the semantics genuinely warrants mutual commensurability. Most lifts are directional.
- Do NOT author a lifting rule in a context YAML other than the TARGET — the CLI places it correctly; hand-edits will break the pattern.
