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
ls "$paper_dir"/claims.yaml 2>/dev/null && echo "EXISTS: claims.yaml — use enrich-claims to improve it"
```

- `notes.md` missing → STOP. Run paper-reader first.
- `claims.yaml` already exists → report and ask whether to overwrite or use enrich-claims instead.

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

## Step 2: Extract Claims by Type

### 2.1: Parameter Claims

For each parameter, constant, or threshold mentioned in the paper:

```yaml
- id: claim1
  type: parameter
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
- Every parameter needs at minimum: id, type, concept, provenance
- Include `value` OR `lower_bound`+`upper_bound` (at least one)
- Always include `unit` when known
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

## Step 5: Ingest into Propstore

If a propstore source branch exists for this paper, ingest the claims:

```bash
source_name=$(basename "$paper_dir")
pks source add-claim "$source_name" --batch "$paper_dir/claims.yaml"
```

If this fails with concept validation errors, the claims reference concepts not in the source branch's concepts.yaml. Fix the concept names to match what register-concepts produced, then retry.

## Step 6: Stamp Provenance

```bash
uv run plugins/research-papers/scripts/stamp_provenance.py \
  "<paper_dir>/claims.yaml" \
  --agent "<your model name>" --skill extract-claims
```

This records which model extracted claims, when, and which plugin version was used. Plugin version is autodetected.

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
- [ ] Parameter claims have concept, value (or bounds), and unit
- [ ] Equation claims have expression, valid sympy, and variable bindings
- [ ] Observation claims have statement and concepts list
- [ ] Model claims have name, equations list, and parameter bindings
- [ ] Measurement claims have target_concept, measure, value, and unit
- [ ] Mechanism claims have statement with causal/architectural reasoning
- [ ] Comparison claims name both subject and comparand with evidence
- [ ] Limitation claims specify the scope boundary
- [ ] Conditions use consistent CEL vocabulary across the file
- [ ] Concept names match the paper's concept inventory where one exists
- [ ] Context assigned if identified during register-concepts — or explicitly universal

## Output

```
Claims extracted: papers/[dirname]/claims.yaml
  Context: [context_id or "universal"]
  Validation: PASS (0 errors, N warnings)
  Claims: N total (P parameter, E equation, O observation, M model, X measurement, K mechanism, C comparison, L limitation)
```
