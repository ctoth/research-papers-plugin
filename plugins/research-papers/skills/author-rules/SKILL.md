---
name: author-rules
description: Check the installed DeLP rule-authoring capability and encode a paper's stated predicate-level reasoning only through an available owner.
argument-hint: "<papers/Author_Year_Title>"
disable-model-invocation: false
---

# Author Rules: $ARGUMENTS

Keep empirical evidence, inference licences, and contextual applicability distinct.
A study's existence or setting is not evidence for its empirical result.

## Step 0: Check the installed capability

Run the harmless read-only capability check before preparing mutations:

```bash
pks rule --help
```

The current rule CLI exposes only `list` and `show`. Rule and superiority
mutation have no CLI owner. If the installed help exposes only those read
commands, stop here and report: **Rule authoring is unavailable in this installed
CLI; no rule or superiority artifact was authored.** Include the help output
and the blocked paper. Do not run a nonexistent mutation command, hand-author
YAML, invoke a private SDK mutation, or commit artifacts as a workaround.

Do not claim a version number guarantees authoring. If a future installed
version exposes a supported mutation owner, read that owner's help and contract
before using it. The remainder describes semantic requirements, not executable
commands or a claim that this installation supports writing rules.

## Evidence and representation

For an inference among already-authored claims, use `extract-justifications`:
its premise references name the actual evidence claims. Canonical justification
licences contribute strict or defeasible rules to the ASPIC bridge. Their
conclusions must not also become unconditional reported premises.

Use predicate-level DeLP only when the paper states a predicate-level rule and
its evidence atoms have an explicit, existing grounding producer. Identify that
producer before authoring. If the claim-to-ground-fact connection is unavailable,
report that missing capability. Do not manufacture strict empirical facts.

- A setting or applicability predicate describes where a rule applies.
- An empirical conclusion must depend on its actual evidence claims.
- Withdrawing an evidence claim must remove support provided by that claim.
  An unchanged answer alone does not establish robustness: another independent
  argument may still support it.
- Do not duplicate a claim inference as a setting-seeded program that remains
  true when its evidence is withdrawn.
- Do not fabricate clinical evidence, numerical confidence, or recommendations.

## Predicate-level semantics

A strict rule is indefeasible; an empty body represents a fact only when that
fact has an explicit evidential producer. A defeasible rule is tentative.
Strong negation is part of the logical representation, not a quoting workaround.
Every variable in a rule head must appear in its body. Referenced predicates
must already be declared with matching arity and types.

A paper's objection to a reported measurement differs from an objection to
transporting that measurement into a new context. Preserve the target the paper
actually challenges. If the available representation loses that target, report
the limitation rather than silently broadening the attack.

Explicit superiority pairs require two existing non-strict rules and an acyclic
priority relation. The current read-only CLI cannot author these pairs; the
same capability stop applies to superiority authoring.

## Verification and output

Report the selected reasoning backend and real grounding inputs before claiming
a rule contributes to a query. A claim-graph result is not evidence that the
DeLP program executed. A successful build alone does not prove evidence
dependency.

When authoring is blocked, report the missing mutation owner and that no
artifacts were written. Do not emit a fabricated success count or continue the
full paper workflow past this blocked step.
