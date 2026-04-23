---
name: extract-claims
description: Extract propositional claims from a paper directory, building claims.yaml from scratch using notes.md. Produces machine-readable claims conforming to the propstore claim schema. If a concepts.yaml exists (from register-concepts), uses canonical concept names.
argument-hint: "<papers/Author_Year_Title>"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Extract Claims: $ARGUMENTS

Extract propositional claims from a research paper and produce a `claims.yaml` file from scratch using `notes.md` content.

## Step 0: Validate

```bash
paper_dir="$ARGUMENTS"
ls "$paper_dir"/notes.md 2>/dev/null || echo "MISSING: notes.md"
ls "$paper_dir"/claims.yaml 2>/dev/null && echo "EXISTS: claims.yaml — this run will overwrite it"
```

- `notes.md` missing → STOP. Run paper-reader first.
- `claims.yaml` already exists → overwrite it during this run. Do not ask whether to overwrite; orchestrated flow must stay non-interactive.

Check for concept inventory:
```bash
ls "$paper_dir"/concepts.yaml 2>/dev/null
```

If `<paper_dir>/concepts.yaml` exists (from register-concepts), read it and use those `local_name` values as concept references in claims. If no concept inventory exists yet, use descriptive `lowercase_underscore` names and keep them consistent across the file.

## Step 1: Read Source Material

Read:
- `<paper_dir>/notes.md` — primary source
- `<paper_dir>/paper.pdf` or page images in `<paper_dir>/pngs/` — for page numbers and verification
- `<paper_dir>/concepts.yaml` — if it exists, this is the paper's source-local concept inventory from register-concepts. Use `local_name` values as concept references in all claims.

### Page Image Verification Lane

When a claim cites page `N`, the corresponding page image is:

- `pngs/page-{(N-1):03d}.png`

Examples:

- page 1 → `pngs/page-000.png`
- page 12 → `pngs/page-011.png`

For claims with precise numerics, spot-check the cited page image directly rather than trusting only `notes.md`.

Spot-check at minimum:

- exact values
- lower and upper confidence bounds
- p-values
- sample-size-dependent reported quantities

Only verify the cited pages you actually use. Do not reread every page image for claim extraction if the paper has already been read into `notes.md`.

## Step 2: Extract Claims by Type

### 2.0: Determine the paper's context

**Every claim must reference an existing context.** Propstore's master-side `ClaimDocument.context` is a required field; claims without context cannot be promoted from a source branch to master. Source-side `SourceClaimDocument.context` is optional at ingest time, but promote will fail if it is missing.

Convention: one context per paper, named `ctx_<author>_<year>_<trial-slug>` (e.g., `ctx_ikeda_2014_jppp`, `ctx_bowman_2018_ascend`). The context carries the trial's structural assumptions (population, intervention, follow-up, design) as CEL assumptions and parameters; claim-level `conditions[]` handle finer axes like endpoint or ITT-vs-per-protocol.

If no context exists for this paper yet, run the `author-context` skill FIRST, before extracting claims. That skill calls `pks context add` with the trial's structural assumptions.

Write the chosen context name into `context:` on EVERY claim in the output (see 2.1 onward).

### 2.1: Parameter Claims

For each parameter, constant, or threshold mentioned in the paper:

```yaml
- id: claim1
  type: parameter
  context: <ctx_author_year_slug>
  concept: <local_concept_name or descriptive_name>
  value: <number>
  unit: <unit string>
  conditions:
    - "<CEL expression>"
  provenance:
    paper: <paper_dir_name>
    page: <page number>
    section: "<section name>"
    quote_fragment: "<brief supporting quote>"
  notes: "<methodological context>"
```

Rules:
- Every parameter needs at minimum: id, type, **context**, concept, provenance
- Include `value` OR `lower_bound`+`upper_bound` (at least one). **Never** use `lower_bound` alone or `upper_bound` alone — the validator rejects unpaired bounds. If only one bound is known, use `value` with a `notes` field explaining the bound direction (e.g., ">85%").
- Include `unit` for dimensional quantities (mass, time, pressure, etc.). **Omit `unit` for dimensionless forms** (ratio, count, score, boolean, etc.) — propstore auto-fills `unit: '1'` at build time. **Never use compound units that conflate independently-variable dimensions** (e.g., `mg/day` conflates dose and frequency). Split into separate concepts with simple units and express the relationship through CEL conditions. See register-concepts "Compound-Unit Decomposition" for the full rule.
- For temporal quantities, use clinical time units directly: `mo` (month), `yr` (year), `d` (day), `wk` (week). Do not convert to hours or seconds — the `time` form accepts all of these natively.
- Use names from the paper's `concepts.yaml` inventory when available; otherwise use descriptive lowercase_underscore names

### 2.2: Equation Claims

For each equation or mathematical relationship:

```yaml
- id: claim5
  type: equation
  expression: "F = m * a"
  sympy: "Eq(concept2, concept1 * concept3)"
  variables:
    - symbol: "F"
      concept: "force"
      role: "dependent"
    - symbol: "m"
      concept: "mass"
      role: "independent"
    - symbol: "a"
      concept: "acceleration"
      role: "independent"
  provenance:
    paper: <paper_dir_name>
    page: 4
    section: "Method"
```

Rules:
- `expression`: human-readable string
- `sympy`: valid `Eq(lhs, rhs)` using concept IDs for physical quantities, bare symbols for constants (pi, e, numeric coefficients)
- Every symbol must have a variable binding
- Mathematical constants (i, pi, e, 0.5, 2) are NOT concepts

### 2.3: Observation Claims

For qualitative claims, empirical observations, and testable properties:

```yaml
- id: claim8
  type: observation
  statement: "Single declarative sentence capturing the claim."
  concepts:
    - concept_a
    - concept_b
  provenance:
    paper: <paper_dir_name>
    page: 7
    section: "Results"
    quote_fragment: "Brief supporting quote"
```

Rules:
- `statement`: a single declarative sentence
- `concepts`: list all concept IDs referenced
- Testable properties from notes.md are good candidates

### 2.4: Model Claims

For parameterized equation systems (multi-equation frameworks):

```yaml
- id: claim12
  type: model
  name: "Model name"
  equations:
    - "equation1"
    - "equation2"
  parameters:
    - name: "param_name"
      concept: "concept_name"
      note: "What this parameter controls"
  provenance:
    paper: <paper_dir_name>
    page: 5
    section: "Method"
```

### 2.5: Measurement Claims

For perceptual, behavioral, or evaluation measurements:

```yaml
- id: claim15
  type: measurement
  target_concept: concept_name
  measure: preference_rating
  value: 4.2
  unit: "points"
  evaluation_population: "participant_group"
  methodology: "Brief method description"
  conditions:
    - "system == 'SystemA'"
  provenance:
    paper: <paper_dir_name>
    page: 12
```

Measure types: `jnd_absolute`, `jnd_relative`, `discrimination_threshold`, `preference_rating`, `detection_threshold`, `correlation`, `effect_size`, `accuracy`, `precision`, `recall`, `f1_score`, `mean_average_precision`, `intersection_over_union`, `benchmark_score`

### 2.6: Mechanism Claims

For causal or architectural arguments:

```yaml
- id: claim18
  type: mechanism
  statement: "X works by Y because Z — include the reasoning chain, not just the conclusion."
  concepts:
    - concept_a
    - concept_b
  provenance:
    paper: <paper_dir_name>
    page: 12
    section: "Discussion"
    quote_fragment: "Supporting quote"
```

### 2.7: Comparison Claims

For contrastive claims positioning this work against prior approaches:

```yaml
- id: claim20
  type: comparison
  statement: "Unlike Y, X handles Z — must name both subject and comparand with evidence."
  concepts:
    - concept_a
    - concept_b
  provenance:
    paper: <paper_dir_name>
    page: 3
    section: "Related Work"
```

### 2.8: Limitation Claims

For acknowledged scope boundaries, failure modes, unsolved problems:

```yaml
- id: claim22
  type: limitation
  statement: "What the approach does not handle — specify the boundary, not just 'has limitations'."
  concepts:
    - concept_a
  provenance:
    paper: <paper_dir_name>
    page: 42
    section: "Limitations"
```

## CEL Conditions Contract

**Every name on the left-hand side of a CEL condition must be a registered concept.** The propstore CEL checker (`cel_checker.py`) resolves every `NameNode` against the concept registry. If a name is not a registered concept, validation fails with `Undefined concept`.

This means condition variables like `endpoint`, `comparison`, `intervention`, `population` are **not free-form strings** — they are concepts that must exist in the registry with appropriate forms. The form determines what operations are valid:

- **category** concepts: can use `==`, `!=`, `in [...]` with string literals
- **quantity** concepts: can use `==`, `!=`, `<`, `>`, `<=`, `>=` with numeric literals
- **boolean** concepts: can use `==`, `!=` with `true`/`false`
- **structural** concepts: **cannot appear in CEL expressions at all**

### What this means in practice

When you write `conditions: ["endpoint == 'composite_primary'"]`, the name `endpoint` must be a registered concept with form `category`. If it isn't registered yet, you must register it (via register-concepts or `pks source propose-concept --name endpoint --form category --values composite_primary,secondary`) before validation will pass.

**Before writing any CEL condition, verify the name exists in the concept registry.** If you're introducing a new conditioning axis (e.g., `endpoint`, `comparison`, `population`), register it as a concept first. These conditioning-axis concepts are just as real as the measurement concepts — they're the dimensions along which parameter values vary.

### Meta rule

When producing artifacts that a downstream tool validates, discover the validation contract from the tool — do not assume you know it. The CEL checker is the authority on what condition expressions are legal, not this skill document.

## Step 3: Assemble and Write

```yaml
source:
  paper: <paper_dir_name>

claims:
  - id: claim1
    ...
```

Write to `<paper_dir>/claims.yaml`.

## Step 4: Validate

```bash
ls knowledge/.git 2>/dev/null || echo "MISSING: knowledge/.git"
pks claim validate-file "$paper_dir"/claims.yaml
```

If `knowledge/.git` is missing → STOP. Run `pks init` or use `paper-process`, which initializes the source branch first.

If validation fails, fix and re-validate. **Do not consider extraction complete until validation passes.**

**Note on source-branch workflows:** `validate-file` checks concepts against the master registry (`knowledge/concepts/`). If you are building a new source branch where concepts have been proposed but not yet promoted to master, the master concepts directory may be empty and `validate-file` will report false "Undefined concept" errors. In that case, proceed to Step 5 — `pks source add-claim` validates claims against the **source branch's own concept registry**, which includes proposed concepts. If `add-claim` succeeds, the claims are valid.

## Step 5: Ingest into Propstore

If a propstore source branch exists for this paper, ingest the claims:

```bash
source_name=$(basename "$paper_dir")
pks source add-claim "$source_name" --batch "$paper_dir/claims.yaml" \
  --reader "<your model name>" --method "extract-claims"
```

If this fails with `unknown concept reference` errors, or if the add succeeds but source auto-finalize reports unknown concepts:

1. note the missing concept names
2. rerun `register-concepts`
3. add the missing concepts to `concepts.yaml`
4. ingest concepts again
5. retry `pks source add-claim`

This retry loop is expected. Use finalize feedback as the authoritative missing-concept list until the loop converges.

## Step 6: Provenance

Provenance is recorded automatically via `--reader` and `--method` flags on the `pks source add-claim` command in Step 5. No separate stamp step is needed.

If you need to override provenance after the fact, `pks source stamp-provenance` still exists but is deprecated.

---

## Claim ID Rules

- Format: `claim` + sequential integer, no padding (claim1, claim2, ... claim103)
- IDs must be unique within a file
- Never reuse an ID, even if a claim was removed

## Provenance Rules

- `paper`: paper directory name (e.g., `Gobl_1988`)
- `page`: integer; use 0 only as last resort
- `section`: section name or number
- `table`: table identifier when claim comes from a table
- `figure`: figure identifier when claim comes from a figure
- `quote_fragment`: brief quote (1-2 sentences max) directly supporting the claim

## Claim Value Filter

Before extracting a claim, ask: **"Would someone building a system in this domain query this claim?"** and **"Would someone adjudicating between competing approaches query this?"** If neither, skip it.

### EXTRACT (high value)
- **Architectural insights**: generalizable design principles
- **Design constraints**: directly usable parameters
- **Validated thresholds**: parameters the paper showed sensitivity analysis for
- **Cross-paper findings**: observations that generalize beyond one paper's experiments
- **Failure modes**: conditions under which approaches break down
- **Design rationale**: why a choice was made (mechanism)
- **Positioning against prior work**: what this approach does differently (comparison)
- **Scope boundaries**: what the approach cannot do (limitation)

### SKIP (low value)
- **Training hyperparameters without interpretation**: learning rate, batch size — UNLESS studied via ablation
- **Study logistics**: participant count, session duration, annotator wages
- **Benchmark metadata**: dataset sizes, category counts — these describe the benchmark, not findings
- **Implementation details without rationale**: "we used X" without "because Y"

### CONVERT (transform to higher-value claims)
When a paper reports the same parameter under many conditions:
- Do NOT create N separate parameter claims
- DO create 1 observation claim synthesizing the pattern

When a paper reports benchmark numbers across models:
- Do NOT create N parameter claims per model
- DO create 1-2 observation claims about what the numbers reveal

## Claim Decomposition

One proposition per claim. If a statement contains multiple independent findings, split it.

**Signals to split:**
- "and" joining two independent findings
- Multiple numbers that could each be a parameter claim
- Claims about different concepts
- Would need a semicolon to be grammatically correct

**Do not split** when a statement describes a single finding with necessary context (e.g., "X outperforms Y because Z" is one causal claim).

**Definitional claims — do not decompose components:**
When a paper introduces a formal definition, create one `observation` claim for the top-level definition. Components become `concepts` list entries, not standalone claims. If a component has non-trivial constraints described separately, it gets its own claim with an inline `supports` stance pointing at the parent.

## Duplicate Detection

Do not query master-branch claims from this skill. Create the local equation claim for this source and let propstore deduplicate or reconcile at finalize/promotion time.

## Quality Checklist

- [ ] Every claim has unique sequential ID
- [ ] Every claim has type, provenance with real page numbers where possible
- [ ] Parameter claims have concept, value (or bounds), and unit (auto-filled for dimensionless forms)
- [ ] Equation claims have expression, valid sympy, and variable bindings
- [ ] Observation claims have statement and concepts list
- [ ] Model claims have name, equations list, and parameter bindings
- [ ] Measurement claims have target_concept, measure, value, and unit
- [ ] Mechanism claims have statement with causal/architectural reasoning
- [ ] Comparison claims name both subject and comparand with evidence
- [ ] Limitation claims specify the scope boundary
- [ ] Every name in CEL conditions is a registered concept (not free-form strings)
- [ ] Conditions use consistent CEL vocabulary across the file
- [ ] Concept names match the paper's concept inventory where one exists
- [ ] **Every claim carries a `context:` field referencing a pre-authored context**

## Output

```
Claims extracted: papers/[dirname]/claims.yaml
  Context: [ctx_author_year_slug]
  Validation: PASS (0 errors, N warnings)
  Claims: N total (P parameter, E equation, O observation, M model, X measurement, K mechanism, C comparison, L limitation)
```
