---
name: author-lifting-rules
description: Assess justified cross-context applicability and author supported lifting rules when the installed Propstore CLI exposes their owner workflow.
argument-hint: "[knowledge-root]"
disable-model-invocation: false
---

# Author Lifting Rules

A context boundary records a difference in the question, population, endpoint,
measurement method, or assumptions. `CONTEXT_PHI_NODE` is informational; reducing
its count is not a goal. Preserve it when cross-applicability is unestablished.

## Step 0: Validate the available owner workflow

```bash
pks context --help
```

The current charter-based Propstore CLI exposes context `list` and `show`, but
does not expose context or lifting-rule mutation. If the installed CLI has that
surface, STOP and report: `Context lifting authoring is unavailable in this pks
CLI. No lifting rules were written.` Do not run the removed `context lifting
add` command, hand-edit Git documents, or substitute an agent-written SDK script.
The typed SDK's `LiftingRule` does not by itself supply this skill's CLI workflow.

If an installed version exposes an owner-backed lifting authoring command,
continue using that version's documented syntax. Do not invent old flags or
assume a rule is stored inside a target context file.

## Step 1: Read the actual contexts and claims

Read context descriptions, assumptions, parameters, perspective, and relevant
claims through the installed read commands. Check original page images for any
scientific claim used to justify transport. A reviewer's modelling assumption
must be labelled as that reviewer's assumption, not attributed to a paper.

A reported measurement and its proposed use elsewhere are different assertions.
Do not lift a whole trial into another cohort merely because both mention the
same quantity, nor interpret a conditional model as a medical recommendation.

## Step 2: Author only the warranted applicability relation

For each scientifically justified bridge, state the source context, target
context, exact applicable content, conditions, and attributed rationale. If the
available owner only supports context-wide lifting and the rationale applies to
one proposition, report that expressiveness limit instead of over-broadening it.

Conditions are gates controlling whether a lift applies. They do not rewrite
claim-level conditions, equate endpoints, or establish population equivalence.
Mode names alone do not implement proposition transformations. Do not change
conditions to manufacture conflicts or make a count decrease.

Use only the installed owner workflow. Preserve explicitly unknown or blocked
lifting outcomes; do not translate them into a successful empty comparison.

## Step 3: Verify and report

Report the authored rules and the exact context-qualified assertions the actual
query includes or excludes, with its backend and policy. A successful build or
the number of rules is not evidence that a particular inference used them.
Inspect changed comparison records individually; no new conflict is a valid
result when the evidence does not establish a shared question.

Report unestablished bridges and their reasons as unresolved, not as future
facts to be filled in. Never fabricate confidence or erase source context.
