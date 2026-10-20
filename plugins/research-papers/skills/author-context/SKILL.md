---
name: author-context
description: Identify a paper analysis context and author it only through an available Propstore context-owner workflow.
argument-hint: "<papers/Author_Year_Title>"
disable-model-invocation: false
---

# Author Context: $ARGUMENTS

A context is a first-class `ist(c, p)` qualifier: it records the scope in which
an assertion holds. Identify the population, design, intervention, comparator,
follow-up, and analysis perspective relevant to that assertion. A paper reporting
different populations or analyses may need distinct contexts; do not force them
all into one trial-wide claim about applicability.

Ontology-policy reference:
`plugins/research-papers/docs/ontology-authoring-policy.md`.

## Step 0: Validate inputs and the actual authoring surface

```bash
paper_dir="$ARGUMENTS"
ls "$paper_dir"/notes.md 2>/dev/null || echo "MISSING: notes.md"
ls "$paper_dir"/metadata.json 2>/dev/null || echo "MISSING: metadata.json"
ls knowledge/.git 2>/dev/null || echo "MISSING: knowledge/.git"
pks context --help
```

Stop on missing inputs. The current charter-based CLI exposes only context
`list` and `show`; it has no `context add`, update, remove, or lifting-rule
authoring workflow. When that is the installed surface, STOP and report:
`Context authoring is unavailable in this pks CLI; no context was written.`
Do not hand-author canonical YAML, call a removed command, or substitute an
agent-written SDK script. The typed Context family is not this skill's missing
CLI workflow. This blocker also blocks dependent extraction in `paper-process`.

If the installed version exposes an owner-backed authoring command, continue
using its documented syntax rather than assuming historical flags or paths.

## Step 1: Identify the analysis scope

Read the notes and original page images for the scope being attributed to the
paper. Use a stable descriptive name such as `ctx_author_year_analysis`.
Separate source-reported design facts from reviewer modelling assumptions.
The latter require explicit reviewer attribution; they are not extracted facts.

Keep endpoint, arm, subgroup and analysis selectors at claim level when they
vary within a context. Put a fact in the context only if it applies to every
assertion being assigned there. A recorded population does not imply that a
result transports to other populations.

## Step 2: Author through the available owner

CEL assumptions must use concepts and forms already available to that owner.
Do not promise to register an undefined name later, reinterpret structural
concepts as booleans, flatten an unknown dotted expression to make it parse,
or substitute a score/ratio form for an incompatible unbounded quantity.
Report a missing concept, form, or authoring capability at its actual owner.

Use the installed owner-backed command to write the attributed description,
assumptions, parameters, and perspective. Never edit identity hashes manually.

## Step 3: Verify and report

Read the resulting context through `pks context show <name>`. Report the actual
stored scope, its attribution, and the claims assigned to it. A successful write
does not establish cross-context applicability; that requires independently
justified lifting. If authoring was unavailable, report the blocker rather than
printing a successful context/file result.
