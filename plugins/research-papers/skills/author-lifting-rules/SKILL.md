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

Pick the mode that matches the relationship between source and target contexts:

- **`bridge`** (default): two contexts are commensurable on shared concepts without one subsuming the other. Example: two independent RCTs in similar cohorts whose hazard ratios are authored as comparable.
- **`specialization`**: the SOURCE context is a specialization of the TARGET — target is broader, source is narrower. A claim that holds in the narrower source also holds in the broader target (under conditions). Example: a finding in Japanese-adults-60-85-with-CV-risk lifts to a broader elderly-primary-prevention frame as a specialization lift.
- **`decontextualization`** (Guha): the SOURCE drops context-specific constraints to land in the TARGET. Example: ASPREE-XT's extended-observational findings decontextualize (drop the "randomized phase" and "primary composite" constraints) to become claims about the underlying ASPREE cohort.

The mode flows into how the conflict detector and argumentation engine treat the lifted claim at runtime. Pick carefully.

## Step 0: Validate

```bash
pks context list                              # ≥ 2 contexts to bridge
pks context lifting list                      # what's already authored
pks build                                     # baseline must be green
```

If `pks context lifting list` already shows a rule between a pair you're about to author, inspect before overwriting: `pks context lifting show TARGET_CTX --rule-id R_ID`.

## Step 1: Identify candidate bridges

Read the knowledge store's context YAMLs (`knowledge/contexts/*.yaml`) and the claims that reference them. Look for these patterns:

### Pattern A — Meta-analysis → individual trials
If one context is a meta-analysis or pooled frame (perspective mentions pooling, assumptions mention `study_type == 'meta_analysis'`), every individual trial context whose trials it pools should have a **bridge** lifting rule authored INTO the meta context. Rule direction: `source = trial_ctx`, `target = meta_ctx`. A bridge, not specialization, because the meta-analysis doesn't claim trials are specializations of it — it claims commensurability of their reported effects.

### Pattern B — Extension of an earlier trial
If one paper is explicitly a follow-up or extended-observational phase of another (ASPREE-XT → ASPREE, longitudinal follow-ups, secondary analyses), author a **decontextualization** lift: `source = extension_ctx`, `target = base_ctx`. The extension drops whatever phase-specific constraints it adds (blinding, randomization phase, analytic cutoff) to reach the base context.

### Pattern C — Shared structural frame
If multiple trials share a cohort frame (all primary-prevention RCTs in elderly adults with CV risk factors, for instance), consider whether a shared super-frame context is worth authoring. If you author one (via `pks context add ctx_shared_frame ...`), author **specialization** lifts from each individual trial context INTO it: `source = individual_trial_ctx`, `target = shared_frame_ctx`, `mode = specialization`. This is optional — only author the super-frame if you intend cross-trial reasoning against it.

### Pattern D — Direct cross-trial commensurability
Two trials that reported the same endpoint in genuinely comparable cohorts (same primary-prevention population, same intervention class, comparable follow-up) — a **bridge** can be authored directly between them if no meta-context is mediating. Use sparingly: prefer routing through a meta-analytic or shared-frame target.

## Step 2: Author one lifting rule at a time

For each candidate bridge identified in Step 1:

```bash
pks context lifting add TARGET_CTX_NAME \
  --rule-id r_lift_<short_descriptive_slug> \
  --source SOURCE_CTX_NAME \
  --mode <bridge|specialization|decontextualization> \
  [--condition "<CEL guard>"] \
  --justification "<one-sentence authored rationale citing the pattern and the papers>"
```

Notes:

- `CONTEXT_NAME` (positional) is the TARGET — the context whose YAML hosts the rule.
- `--source` is the SOURCE context.
- `--rule-id` should be stable across re-runs; if authoring fails mid-batch, rerunning is idempotent if ids match.
- `--condition` (optional) is a CEL expression that must hold for the lift to fire. Leave empty for unconditional commensurability; add when the lift only applies under specific claim-level conditions.
- `--justification` is authored reasoning text for audit. Always supply.

Example for aspirin corpus (meta-analysis pooling individual trials):

```bash
pks context lifting add ctx_att_2009_meta \
  --rule-id r_lift_ikeda_into_att_pool \
  --source ctx_ikeda_2014_jppp \
  --mode bridge \
  --justification "ATT 2009 pooled hazard ratios across primary-prevention RCTs; Ikeda JPPP is one such RCT whose primary-endpoint HR is commensurable with the ATT pooled estimate."
```

Example for extension decontextualization:

```bash
pks context lifting add ctx_mcneil_2018_aspree \
  --rule-id r_lift_aspree_xt_to_aspree_base \
  --source ctx_wolfe_2025_aspree_xt \
  --mode decontextualization \
  --justification "ASPREE-XT (Wolfe 2025) is the post-randomization observational extension of the ASPREE cohort; extended-phase findings decontextualize into claims about the underlying ASPREE cohort."
```

Use `--dry-run` the first time to preview without writing: `pks context lifting add ctx_att_2009_meta --rule-id r_probe --source ctx_ikeda_2014_jppp --mode bridge --justification "probe" --dry-run`.

## Step 3: Verify

```bash
pks context lifting list                      # inspect the bridge graph
pks context lifting list --target ctx_att_2009_meta    # target-scoped
pks build                                     # must still be green
```

Expect: `Build rebuilt:` (or `Build unchanged:`) with zero warnings. If build fails, a lifting rule introduced a schema error or a CEL condition referenced a structural concept — diagnose and re-run `pks context lifting update` or `remove`.

After rebuild, run `pks build` output through the diagnostic summary: the `CONTEXT_PHI_NODE` count should have dropped (pairs that were context-non-liftable are now lift-connected and either classify as `COMPATIBLE` or fall through to condition-based classification). Real `CONFLICT` records may appear where lifted claims actually disagree under lifted interpretation — THAT is the interesting signal. Review each.

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
