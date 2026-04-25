# Ontology Authoring Policy

This document is the ontology-policy contract for the `research-papers` ingestion skills.

Use it when deciding whether a paper fact belongs in:

- a paper-wide context
- a claim-level CEL condition
- a first-class concept
- a category value on a conditioning axis

## Core Rule

Ask, in order:

1. Does this fact hold for essentially every claim the paper makes?
2. If not, is it a dimension along which reported values vary?
3. If not, is it a reusable domain object, outcome, intervention, population, or design construct?
4. If not, is it only a selector value on an already-existing axis?

The first matching rule wins.

## Context vs Condition

Put a fact in the paper context when it is part of the paper's structural commitments:

- cohort definition
- intervention identity, dose, formulation, schedule
- comparator identity
- study design
- follow-up regime
- adjudication regime
- headline analysis perspective

Put a fact in `conditions[]` only when it varies across claims inside the same paper:

- endpoint
- subgroup
- analysis set
- comparison slice
- model arm

Bad:

- putting `aspirin == true` or `followup_years == 5.0` on every claim

Good:

- context carries the trial-wide aspirin regimen and follow-up
- claim conditions carry `endpoint == 'major_bleeding'`

## Conditioning Axis vs Value

A conditioning axis is the concept on the left-hand side of CEL:

- `endpoint`
- `population`
- `comparison`
- `intervention`

A category value is the selector literal on the right-hand side:

- `primary_endpoint`
- `per_protocol`
- `aspirin_arm`
- `placebo_arm`

Do not confuse the axis with the thing being selected.

## First-Class Concept vs Selector Literal

Use a first-class concept when the thing is independently discussable across papers:

- `all_cause_mortality`
- `major_bleeding`
- `nonfatal_myocardial_infarction`
- `intention_to_treat`
- `placebo_control`

Use a selector literal only when the paper is picking one member of an axis for a specific reported estimate:

- `endpoint == 'primary_endpoint'`
- `population == 'per_protocol'`

If the literal names a reusable clinical outcome, intervention, population, or methodological construct, prefer a first-class concept instead of leaving it as only a category value.

## Decompose Fused Labels

Do not collapse multiple independently variable dimensions into one label when the paper gives enough structure to separate them.

Examples:

- `mg/day` usually decomposes into dose plus dosing frequency
- `aspirin_vs_placebo` usually decomposes into comparison axis plus intervention/comparator identity

Keep a fused category value only when the paper treats the contrast as an indivisible named selector and the decomposition would not improve queryability.

## Current Propstore Claim Schema

Author claims against the current propstore claim contract:

- `parameter` -> `output_concept`
- `algorithm` -> `output_concept`
- `measurement` -> `target_concept`
- `observation` / `mechanism` / `comparison` / `limitation` -> `concepts[]`
- `equation` -> `variables[].concept`
- `model` -> `parameters[].concept`

Do not use top-level `concept` for parameter claims in new artifacts.

## Open Category Policy

Category value sets are open by default. That means unseen values may be temporarily tolerated, but this is not permission to dump domain concepts into category literals.

When a warning-heavy literal appears repeatedly:

1. decide whether it should be a first-class concept
2. if it is truly just a selector on an axis, add it to that axis's value set
3. if it fuses multiple dimensions, decompose it

## Examples

`all_cause_mortality`
- usually a first-class concept
- can also appear as the selected member of the `endpoint` axis for a specific claim

`primary_endpoint`
- usually a selector literal on `endpoint`
- not usually a first-class domain concept

`intention_to_treat`
- often a first-class methodological concept
- may also be the selected member of `population` when the claim is analysis-set-specific

`aspirin`
- often part of the paper-wide intervention context
- may appear as an arm selector only when the claim truly reports arm-specific values
