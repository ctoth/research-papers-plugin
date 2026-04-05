=== skills/adjudicate/SKILL.md ===
---
name: adjudicate
description: Systematically adjudicate disagreements across a paper collection. Produces ruthless verdicts on who was wrong, what supersedes what, and what the best current understanding is. Organized by topic clusters with actionable replacement values for implementation.
argument-hint: "[topic-scope or --all]"
context: fork
agent: general-purpose
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Adjudicate: $ARGUMENTS

Systematically adjudicate disagreements across the paper collection. Not summaries — *judgments*.

This skill writes verdict documents and may acquire missing evidence through `paper-process`. It does not mutate propstore source branches directly.

## Step 0: Parse Arguments

- If `$ARGUMENTS` is `--all`: full collection sweep — discover topics, assign papers, produce all verdicts
- If `$ARGUMENTS` is a topic name (e.g., "vowel formants"): produce a single verdict for that topic
- If `$ARGUMENTS` is a list of paper directories: adjudicate only the disagreements among those specific papers

## Step 1: Scope the Collection

```bash
ls -d papers/*/ | grep -v "papers/pngs" | wc -l
ls papers/*/notes.md | wc -l
```

Read `papers/index.md` (if it exists) or sample `papers/*/description.md` files to understand what topics the collection covers.

Check for existing verdicts:
```bash
ls research/verdicts/*.md 2>/dev/null
```

## Step 2: Discover Topic Clusters

For `--all` mode, identify natural topic clusters where papers make overlapping claims. Scan description.md files and notes.md cross-reference sections to find areas of disagreement.

**Standard topic areas** (adapt to collection):
- Source/generation models
- Target values (formants, spectra, durations, etc.)
- Dynamic phenomena (coarticulation, transitions, temporal patterns)
- Higher-level organization (prosody, phrase structure)
- Speaker variation (gender, age, style)
- Perceptual correlates

For single-topic mode, skip this step — use the provided topic.

## Step 3: Assign Papers to Topics

For each topic, identify the specific paper directories whose notes.md must be read. A paper can belong to multiple topics.

```bash
# Example: find papers relevant to "vowel formants"
grep -rl "formant" papers/*/notes.md --include="notes.md" | head -30
```

Write the assignment to `reports/paper-topic-assignment.md`:
```markdown
## Topic: [Name]
Papers to read:
- papers/Author_Year_Title/
- papers/Author_Year_Title/
[...]
Estimated scope: N papers, ~M lines of notes
```

## Step 4: Produce Verdicts

For each topic, read ALL assigned notes.md files and render a verdict.

### Decision Rubric

Apply this hierarchy by default. Override with explicit reasoning only.

**Evidence hierarchy (higher beats lower):**
1. Multiple independent empirical replications > single study
2. Direct acoustic/physiological measurement > derived/computed value
3. Larger sample (N>50) > smaller sample (N<10)
4. Modern measurement technology > older (LPC > spectrograph, EGG > indirect estimation)
5. Controlled lab conditions > naturalistic observation (for baseline values)
6. Naturalistic observation > controlled conditions (for ecological validity)
7. Theory with empirical validation > theory without
8. Original paper with published errata/corrections > uncorrected original

**Override permitted when:**
- The older study controlled for a variable the newer one didn't
- The newer study measured a fundamentally different population/context
- Sample size difference is small and the smaller study had better methodology
- A foundational theoretical framework remains correct despite age because the physics hasn't changed

### Four Categories of "Wrong"

Every finding of error gets one of these labels:

1. **WRONG** — Methodology error, logical flaw, or measurement artifact. The finding was incorrect even for its original scope.
2. **SUPERSEDED** — Correct at the time, better data replaced it. Not the authors' fault.
3. **LIMITED** — Correct for its specific population/context but not generalizable as broadly as applied.
4. **INCOMPARABLE** — Papers appear to disagree but measured different things. Apples-to-oranges.

### Verdict Document Template

Write each verdict to `research/verdicts/NN-topic-name.md`:

```markdown
# Verdict: [Topic]

## Papers Considered
[Exact folder names for traceability]

## Historical Timeline
[Who said what, when — chronological. The story of the field.]

## Findings by Category

### Wrong (methodology error or flawed reasoning)
[Each: paper, claim, what was wrong, evidence. Label: WRONG]

### Superseded (better data replaced it)
[Each: old paper/claim → new paper/claim, why new wins. Label: SUPERSEDED]

### Limited (correct but over-applied)
[Each: paper, claim, valid scope, where it breaks down. Label: LIMITED]

### Incomparable (different questions mistaken for disagreement)
[Each: the two papers, what each actually measured, why comparison is invalid. Label: INCOMPARABLE]

## What Subsumes What
[Broader theories encompassing narrower ones. The intellectual genealogy.]

## Genuinely Uncertain
[Active disagreements with no resolution. The honest "we don't know."]

## Best Current Understanding
[The verdict. For each sub-question: answer, evidence, confidence (high/medium/low).]

## Synthesizer Audit
[What the implementation currently uses vs what it should use.
Each entry: current value (file:line) + source paper → category (correct/WRONG/SUPERSEDED/LIMITED) → replacement value with source paper.
Include actual numbers ready to implement.]

## Open Questions
[What the collection can't answer. Gaps. Papers we'd need to acquire.]
```

### Tone

Ruthless. If the evidence says a paper was wrong, say it plainly. No hedging, no "may have been superseded." Name names, cite evidence, render judgment.

"Peterson & Barney's F3 values for children were WRONG — Hillenbrand 1995 showed they were 174 Hz too high, likely due to spectrograph limitations."

Not: "Later work found somewhat different values."

### Actionability

Every Synthesizer Audit entry that recommends a change must include the actual replacement values. "Replace IY1 F1=270 with F1=342 per Hillenbrand 1995 Table III" — not just "consider updating."

### Gap Filling

If a critical missing paper would change the verdict, use the paper-process skill to acquire it:
```
Use the paper-process skill to retrieve and process: [citation or DOI]
```

If nested skill invocation is unavailable or unreliable on this platform, derive this skill's
installed directory from the injected `<path>`, then run:

```bash
uv run "<skill-dir>/../paper-process/scripts/emit_nested_process_fallback.py"
```

Read the FULL stdout and follow it exactly instead of opening `paper-process/SKILL.md` piecemeal.

A verdict rendered without key evidence is worse than a slower verdict.

## Step 5: Wave Ordering (for --all mode)

Topics have soft dependencies. Process in waves:

**Wave 1 — Foundations (parallel):** Topics about fundamental models, baseline measurements, and architectural assumptions. No topic depends on another within this wave.

**Wave 2 — Dynamics (parallel):** Topics about time-varying phenomena (coarticulation, duration, prosody). May reference Wave 1 verdicts.

**Wave 3 — Higher-level (parallel):** Topics about speaker variation, emotion, style. May reference Wave 1 and 2 verdicts.

**Wave 4 — Master synthesis (sequential):** One pass reading all verdicts, producing `research/verdicts/00-master-synthesis.md`:
- Cross-topic interactions and contradictions
- Priority-ordered list of implementation changes needed
- Confidence map: what's solid ground, what's quicksand
- Papers the collection still needs

## Step 6: Notes and Progress

Create `research/verdicts/notes-progress.md` and update it after each verdict:
- What was adjudicated
- Surprises and course corrections
- Running tally of WRONG/SUPERSEDED/LIMITED/INCOMPARABLE findings

---

## CRITICAL: File Modified Error Workaround

If Edit/Write fails with "file unexpectedly modified":
1. Read the file again
2. Retry the edit
3. Try path formats: `./relative`, `C:/forward/slashes`, `C:\back\slashes`
4. Prefer your file editing tools over shell text manipulation (cat, sed, echo)
5. If all formats fail, STOP and report

## CRITICAL: Parallel Swarm Awareness

You may be running alongside other agents. NEVER use git restore/checkout/reset/clean.

---

## Completion

When done, reply ONLY:
```
Done - see research/verdicts/
  Verdicts: [list of verdict files]
  Master synthesis: research/verdicts/00-master-synthesis.md
  Findings: X WRONG, Y SUPERSEDED, Z LIMITED, W INCOMPARABLE
  Gaps: N papers flagged for acquisition
```

Do NOT:
- Output full verdict content to conversation
- Modify paper notes.md files (verdicts are separate documents)
- Skip the Synthesizer Audit section
- Use hedging language ("may", "possibly", "could be") in verdict conclusions

=== skills/enrich-claims/SKILL.md ===
---
name: enrich-claims
description: Enrich an existing claims.yaml generated by generate_claims.py. Fixes page numbers, aligns concept references with the paper-local concepts.yaml inventory, converts SymPy expressions, adds variable bindings, conditions, notes, uncertainty, and missing claims.
argument-hint: "<papers/Author_Year_Title>"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Enrich Claims: $ARGUMENTS

Improve an existing `claims.yaml` with real data from the paper. This skill assumes a paper-local `concepts.yaml` exists or that you will keep concept names consistent until `register-concepts` runs.

## Step 0: Validate

```bash
paper_dir="$ARGUMENTS"
ls "$paper_dir"/notes.md 2>/dev/null || echo "MISSING: notes.md"
ls "$paper_dir"/claims.yaml 2>/dev/null || echo "MISSING: claims.yaml"
```

Both must exist. If `claims.yaml` is missing, generate it first:

```bash
uv run scripts/generate_claims.py "$paper_dir"
```

This command uses a `scripts/...` path relative to this skill's directory. It extracts parameters from tables, equations from `$$...$$` blocks, and observations from the Testable Properties section. The output has placeholder page numbers (0) and raw concept names — that is what this skill fixes.

## Step 1: Read Source Material

Read these files:
- `<paper_dir>/claims.yaml` — the mechanical extraction to enrich
- `<paper_dir>/notes.md` — the full paper notes with equations, parameters, context

If available, also read:
- `<paper_dir>/paper.pdf` or page images in `<paper_dir>/pngs/` — for verifying page numbers
- `<paper_dir>/concepts.yaml` — for aligning concept references with the paper's source-local inventory

## Step 2: Enrich Each Claim

Walk through every claim in the file. For each one, improve these fields:

### Page Numbers (provenance.page)
Replace `page: 0` with the actual page number. Cross-reference:
- The parameter name against sections in notes.md
- Table/figure references
- Section headings in notes.md "Figures of Interest" or equation locations

If the exact page cannot be determined, add `provenance.section` with the section name and leave page as 0.

### Concept Resolution (concept)
The generator produces lowercase underscore names like `fundamental_frequency`. Check against the paper-local concept inventory:

```bash
ls "$paper_dir"/concepts.yaml 2>/dev/null
```

For each concept name:
- If a matching `local_name` exists in `concepts.yaml`, use that exact name
- If a matching `proposed_name` exists, convert the claim to the corresponding `local_name`
- If no match exists, keep the descriptive name and flag it for `register-concepts` to absorb later

### SymPy Expressions (sympy)
For equation claims, the generator copies LaTeX into both `expression` and `sympy`. Replace `sympy` with a valid SymPy-parseable expression:

- LaTeX `\frac{a}{b}` → SymPy `a/b`
- LaTeX `e^{x}` → SymPy `exp(x)`
- LaTeX `\sqrt{x}` → SymPy `sqrt(x)`
- LaTeX `\sum_{i=0}^{N}` → SymPy `Sum(f(i), (i, 0, N))`
- Subscripts `T_p` → SymPy `T_p`

The `sympy` field encodes as `Eq(lhs, rhs)` — dependent variable on left, expression on right. Use paper-local concept names (not letter symbols) as variable names for dimensional consistency verification.

**How to build a sympy field:**
1. Identify the dependent variable — use its paper-local concept name as lhs
2. Write rhs using paper-local concept names for all physical quantities
3. Use bare symbols for mathematical constants (pi, e, I, numeric coefficients)
4. Wrap in `Eq(lhs, rhs)`

**Examples:**

| Expression | sympy |
|------------|-------|
| `F = m * a` | `Eq(force, mass * acceleration)` |
| `E = 0.5 * m * v^2` | `Eq(energy, 0.5 * mass * velocity**2)` |
| `v = f * lambda` | `Eq(velocity, frequency * wavelength)` |

**Common mistakes:**
- Bare expression without `Eq()` wrapper
- Using raw letter symbols instead of concept names
- Mapping mathematical constants (i, pi, e) to concepts — use bare sympy symbols

### Variable Bindings (variables)
For equation claims, populate variable mappings:

```yaml
variables:
  - symbol: "S"
    concept: "similarity_score"
    role: "dependent"
  - symbol: "q_i"
    concept: "query_embedding"
    role: "independent"
```

Roles: `dependent`, `independent`, `parameter`, `constant`.

### Conditions (conditions)
Add CEL expressions where the paper specifies conditions:

```yaml
conditions:
  - "dataset == 'ActivityNet'"
  - "model == 'GPT-4o'"
```

**Vocabulary constraint:** Every string literal compared against a category concept should match the paper-local inventory where one exists. If the paper uses a new value, add a note in `concepts.yaml` or keep the condition but flag it for later concept enrichment.

### Notes (notes)
Add when methodological context matters:
- Sample size or population details not in conditions
- Measurement methodology caveats
- Whether a value is measured vs. derived vs. assumed

### Uncertainty (uncertainty, uncertainty_type)
```yaml
uncertainty: 0.29
uncertainty_type: sd  # sd, se, ci95, or range
```

### Sample Size (sample_size)
Add if the paper reports how many observations a parameter estimate is based on.

### Measurement Claims
Ensure measurement-type claims have:
- `target_concept`, `measure` (jnd_absolute, preference_rating, accuracy, f1_score, etc.)
- `value` and `unit`
- `evaluation_population` if specified
- `methodology` description

## Step 3: Add Missing Claims

After enriching existing claims, check if notes contain uncaptured information:
- Parameters in prose but not tables
- Observations in Discussion/Results not extracted
- Model descriptions
- Key findings stated as conclusions

Add new claims with sequential IDs continuing from the highest existing ID.

## Step 4: Write and Validate

Write enriched claims back to `<paper_dir>/claims.yaml`.

```bash
pks claim validate-file "$paper_dir"/claims.yaml
```

If validation fails, fix and re-validate. **Do not consider enrichment complete until validation passes.**

## Step 5: Re-ingest Into The Source Branch

If this paper already has a source branch, push the enriched claims back into it:

```bash
source_name=$(basename "$paper_dir")
pks source add-claim "$source_name" --batch "$paper_dir/claims.yaml"
```

If this fails because the source branch does not exist yet, stop and use `paper-process` or initialize the source branch first.

## Step 6: Stamp Provenance

```bash
uv run plugins/research-papers/scripts/stamp_provenance.py \
  "<paper_dir>/claims.yaml" \
  --agent "<your model name>" --skill enrich-claims
```

This records which model enriched claims, when, and which plugin version was used. Plugin version is autodetected.

## Provenance Rules

- `paper`: paper directory name
- `page`: integer; use 0 only as last resort
- `section`: section name or number
- `table`: table identifier (e.g., "Table 2")
- `figure`: figure identifier
- `quote_fragment`: brief supporting quote (1-2 sentences max)

## Quality Checklist

- [ ] Every claim has unique sequential ID
- [ ] Every claim has type, provenance with real page numbers where possible
- [ ] Parameter claims have concept, value (or bounds), and unit
- [ ] Equation claims have expression, valid sympy, and variable bindings
- [ ] Conditions use consistent CEL vocabulary
- [ ] Concept names match the paper-local inventory where one exists
- [ ] Notes added where methodological context matters

## Output

```
Claims enriched: papers/[dirname]/claims.yaml
  Validation: PASS (0 errors, N warnings)
  Claims: N total (P parameter, E equation, O observation, M model, X measurement, K mechanism, C comparison, L limitation)
  Page numbers resolved: X of Y
  Concepts aligned to inventory: X of Y
  SymPy expressions added: X of Y
  Conditions added: X claims
  Notes added: X claims
  New claims added: X
```

=== skills/extract-claims/SKILL.md ===
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

=== skills/extract-justifications/SKILL.md ===
---
name: extract-justifications
description: Extract intra-paper justification structure from a paper's notes.md and claims.yaml. Produces justifications.yaml mapping premise sets to conclusions via typed inference rules. Requires claims to already exist.
argument-hint: "<papers/Author_Year_Title>"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Extract Justifications: $ARGUMENTS

Extract the intra-paper argumentative structure: which claims serve as premises for which conclusions, via what type of reasoning. Produces a `justifications.yaml` file that propstore can compile into structured arguments.

## What Justifications Are

A justification is a directed hyperedge: a set of premise claims that together support or attack a conclusion claim, via a typed inference rule. Unlike stances (binary claim-to-claim edges), justifications capture the "these premises *together* entail this conclusion by this kind of reasoning" structure.

Stances say "claim A relates to claim B." Justifications say "claims A, B, and C jointly support claim D via causal explanation." They are complementary: stances are the inter-paper argumentation graph; justifications are the intra-paper reasoning graph.

### Rule Kinds

Every justification has a `rule_kind` that types the inference step:

- **empirical_support** — Experimental data directly supports the conclusion. "We observed X, therefore Y." The premises are result claims; the conclusion is a finding or generalization.

- **causal_explanation** — A mechanism explains why a result holds. "X happens because Y inhibits Z." The premises include mechanism claims; the conclusion is the explained result.

- **methodological_inference** — A methodological choice leads to a conclusion. "Because we used randomized assignment, confounding is controlled." Premises are methodology claims; conclusion is a validity claim.

- **statistical_inference** — A statistical test or model produces a conclusion. "p < 0.05 with HR 0.88, therefore the effect is significant." Premises are measurement/parameter claims; conclusion is a finding.

- **definition_application** — Applying a formal definition to classify or derive. "X meets criteria A, B, C, therefore X is a Y." Premises are observations matching definitional criteria; conclusion is the classification.

- **scope_limitation** — Evidence narrows the applicability of a claim. "Effect observed only in subgroup Z, therefore the general claim requires qualification." Premises are limitation/observation claims; conclusion is a qualified version of a broader claim.

- **comparison_based_inference** — Comparative reasoning across methods, systems, or findings. "A outperforms B on metric M under conditions C, therefore A is preferable for context C." Premises are comparison claims; conclusion is a recommendation or ranking.

### Attack Targets

When a justification represents a critique rather than support, it includes an `attack_target` that specifies what is being attacked:

- **conclusion** — The critique targets the conclusion directly (maps to rebut in ASPIC+)
- **premise** — The critique targets the quality of evidence/premises (maps to undermine)
- **inference_rule** — The critique targets the methodology/reasoning step itself (maps to undercut)

This distinction is critical: propstore's defeat calculus treats undercuts as preference-independent (always defeat), while rebuts and undermines are preference-dependent.

## Step 0: Validate

```bash
paper_dir="$ARGUMENTS"
ls "$paper_dir"/notes.md 2>/dev/null || echo "MISSING: notes.md"
ls "$paper_dir"/claims.yaml 2>/dev/null || echo "MISSING: claims.yaml"
ls "$paper_dir"/justifications.yaml 2>/dev/null && echo "EXISTS: justifications.yaml — will overwrite"
```

- `notes.md` missing -> STOP. Run paper-reader first.
- `claims.yaml` missing -> STOP. Run extract-claims first.
- `justifications.yaml` already exists -> report and ask whether to overwrite.

## Step 1: Read Source Material

Read:
- `<paper_dir>/notes.md` — primary source for identifying reasoning structure
- `<paper_dir>/claims.yaml` — the claim IDs you will reference as premises and conclusions
- `<paper_dir>/paper.pdf` or page images in `<paper_dir>/pngs/` — for page numbers and verification

Read all of notes.md. Identify where the paper connects its own claims through reasoning — where one or more claims serve as evidence or justification for another claim. Do not limit your search to specific sections or linguistic patterns; reasoning structure can appear anywhere and take any form.

## Step 2: Assemble Justifications

For each identified inferential step:

1. Identify the **conclusion** — which claim ID is being supported or attacked
2. Identify the **premises** — which claim IDs together support this step
3. Determine the **rule_kind** — what type of reasoning connects premises to conclusion
4. If the step is a critique, determine the **attack_target** — what is being attacked (conclusion, premise, or inference_rule) and which claim is targeted
5. Record **provenance** — where in the paper this inferential move is stated

### Schema

```yaml
source:
  paper: <paper_dir_name>

justifications:
  - id: just1
    conclusion: claim12
    premises:
      - claim3
      - claim8
    rule_kind: causal_explanation
    provenance:
      page: 14
      section: Discussion
      quote_fragment: "Because X inhibits Y, the observed reduction..."

  - id: just2
    conclusion: claim20
    premises:
      - claim5
    rule_kind: methodological_inference
    attack_target:
      kind: inference_rule
      target_claim: claim9
    provenance:
      page: 22
      section: Discussion
      quote_fragment: "This approach fails to account for..."
```

### Field Reference

**Required fields:**
- `id` — Unique within file. Format: `just` + sequential integer (just1, just2, ...).
- `conclusion` — Claim ID from this paper's claims.yaml. The claim being supported or derived.
- `premises` — List of claim IDs from this paper's claims.yaml. The claims that together support the conclusion. Must have at least one.
- `rule_kind` — One of: `empirical_support`, `causal_explanation`, `methodological_inference`, `statistical_inference`, `definition_application`, `scope_limitation`, `comparison_based_inference`.
- `provenance` — Where in the paper this inferential move is stated.
  - `page` — Integer page number. Use 0 only as last resort.
  - `section` — Section name where the reasoning appears.
  - `quote_fragment` — Brief quote (1-2 sentences max) showing the inferential move.

**Optional fields:**
- `attack_target` — Only present when the justification represents a critique.
  - `kind` — One of: `conclusion`, `premise`, `inference_rule`.
  - `target_claim` — The claim ID being attacked.

### Rules

1. **All claim IDs must exist in this paper's claims.yaml.** Do not reference claims from other papers — that is what stances are for.
2. **One inferential step per justification.** If a chain of reasoning has three steps (A+B->C, C+D->E, E->F), create three justifications, not one.
3. **Premises must be a genuine set.** Do not list the same claim twice. Do not include the conclusion as a premise.
4. **Do not fabricate reasoning the paper does not make.** If the paper presents a result without connecting it to premises, it is an isolated claim — do not invent a justification.
5. **Quote fragments must come from the paper.** Do not paraphrase or synthesize — use actual text.
6. **Attack justifications need both attack_target and standard fields.** A critique still has premises (the evidence for the attack) and a conclusion (what the attacker concludes).

## Step 3: Write

Write to `<paper_dir>/justifications.yaml`.

## Step 4: Validate

Check:
- Every `conclusion` and every entry in `premises` references a valid claim ID in `<paper_dir>/claims.yaml`
- No justification has its conclusion in its own premises list
- Every `rule_kind` is one of the seven valid values
- Every `attack_target.kind` (if present) is one of: `conclusion`, `premise`, `inference_rule`
- Every `attack_target.target_claim` (if present) references a valid claim ID
- No duplicate justification IDs
- At least one premise per justification

If validation fails, fix and re-validate.

## Step 5: Ingest into Propstore

If a propstore source branch exists for this paper, ingest the justifications:

```bash
source_name=$(basename "$paper_dir")
pks source add-justification "$source_name" --batch "$paper_dir/justifications.yaml"
```

If this fails with claim reference errors, the referenced claim IDs don't match the source branch's claims. Fix and retry.

## Step 6: Stamp Provenance

```bash
uv run plugins/research-papers/scripts/stamp_provenance.py \
  "<paper_dir>/justifications.yaml" \
  --agent "<your model name>" --skill extract-justifications
```

This records which model extracted justifications, when, and which plugin version was used.

## Quality Checklist

- [ ] Every justification has unique sequential ID
- [ ] Every conclusion and premise references a valid claim ID
- [ ] Rule kinds are semantically appropriate (not just syntactically valid)
- [ ] Attack targets correctly distinguish conclusion/premise/inference_rule
- [ ] Quote fragments are actual paper text, not paraphrases
- [ ] Provenance has real page numbers and section names
- [ ] No fabricated connections — only reasoning the paper actually makes
- [ ] Subargument chains are decomposed into individual steps
- [ ] Provenance stamped

## Output

```
Justifications extracted: papers/[dirname]/justifications.yaml
  Justifications: N total
    empirical_support: X
    causal_explanation: X
    methodological_inference: X
    statistical_inference: X
    definition_application: X
    scope_limitation: X
    comparison_based_inference: X
  Attack justifications: X (conclusion: A, premise: B, inference_rule: C)
  Claims participating: X of Y total claims
    As conclusion: X
    As premise: X
    Intermediate (both): X
    Isolated: X
```

=== skills/extract-stances/SKILL.md ===
---
name: extract-stances
description: Extract inter-claim stances from a paper collection. Reads each paper's notes.md and claims.yaml, identifies argumentative relationships between claims across papers, and writes standalone stances.yaml files. Requires claims to already exist.
argument-hint: "<papers/Author_Year_Title> [--cluster paper1,paper2,...] or --all"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Extract Stances: $ARGUMENTS

Extract argumentative relationships (stances) between claims across a paper collection. Writes a standalone `stances.yaml` file per paper (not embedded in claims.yaml).

## What Stances Are

A stance is a directed relationship from one claim to another. It says: "this claim, from this paper, has this argumentative relationship to that claim, from that paper." Stances are the edges that connect isolated claim nodes into a reasoning graph.

### Stance Types and Their Precise Semantics

There are six stance types, drawn from the ASPIC+ structured argumentation tradition. They fall into three categories based on how propstore's defeat calculus treats them.

**Preference-independent (always succeed as defeats):**

- **undercuts** — Attacks the *inference rule* or *methodology* that produced the target claim, rather than the conclusion itself. "Your method is flawed, so your result doesn't follow." Example: Paper B shows that Paper A's trial was underpowered due to event rate deflation. This doesn't say Paper A's HR value is wrong — it says the non-significance conclusion doesn't follow from the data because the trial couldn't detect the effect. Undercuts always defeat their target regardless of the relative strength of the two claims, because a broken inference invalidates its conclusion no matter how large the sample.

- **supersedes** — Replaces the target claim. The attacker is strictly newer, larger, longer, or corrects an error. "This claim replaces that one." Example: Wolfe 2025 (extended ASPREE follow-up, 8.3 years) supersedes McNeil 2018 (original ASPREE, 4.7 years) on all-cause mortality — same cohort, longer observation. Supersedes always defeats because the replacement is definitional, not a matter of evidence strength.

**Preference-dependent (succeed only if attacker is not strictly weaker):**

- **rebuts** — Attacks the *conclusion* directly. "My result contradicts your result." Example: Paper A finds aspirin HR 0.80 (beneficial), Paper B finds HR 1.14 (harmful) for the same endpoint in a comparable population. Each rebuts the other. Which defeat succeeds depends on relative claim strength — propstore computes this from sample_size, uncertainty, and confidence metadata using Modgil & Prakken's Def 19 set comparison (elitist or democratic).

- **undermines** — Attacks a *premise* or *evidence quality* of the target. "Your inputs are wrong, so your conclusion is unsupported." Example: Paper B shows that Paper A's risk calculator overestimated baseline event rates by 2x, undermining Paper A's conclusion that aspirin should be given to "moderate risk" patients (who were actually low risk). Like rebuts, undermines succeeds only if the attacker is not strictly weaker.

**Support (not attacks):**

- **supports** — Provides corroborating evidence. "My result confirms your result." Example: ASCEND's null primary endpoint (HR 0.88, NS after bleeding offset) supports ARRIVE's null result (HR 0.96) — two independent trials in different populations converging on the same conclusion. Support edges propagate through the graph: if A supports B and C attacks B, then C indirectly threatens A (Cayrol 2005 derived defeats).

- **explains** — Provides a mechanistic or causal account. "Here's *why* your result holds." Example: A mechanism claim about statin co-prescription reducing baseline cardiovascular risk explains why modern aspirin trials find null results where older trials found benefit. Explains is directional — the explanation supports the finding, not the other way around.

### Where to Find Stances in Papers

Stances live in the *argumentative structure* of papers, not the results tables. Look for:

1. **Discussion sections** — Where authors compare their results to prior work. "Our findings are consistent with..." (supports), "Unlike the earlier trial..." (rebuts), "The discrepancy may be explained by..." (explains/undermines).

2. **Collection Cross-References in notes.md** — The reconcile skill already identified conceptual links between papers. These are stance candidates.

3. **Open Questions and Tensions** — Documented in notes.md. A tension between two papers' findings is a rebuts pair.

4. **Supersession chains** — Later papers on the same cohort or with larger samples supersede earlier ones. Extended follow-ups supersede original reports.

5. **Methodological critiques** — When Paper B notes Paper A was underpowered, open-label, or had high crossover, these are undercuts.

### What NOT to Stance

- Do not create stances between claims in the *same* paper. Intra-paper structure is captured by justifications (extract-justifications skill).
- Do not speculate. Every stance must be traceable to something the paper says or to a verifiable structural relationship (same cohort = supersedes, same endpoint + different result = rebuts).
- Do not create rebuts between claims that have different conditions and don't actually conflict. Two HR values for different endpoints are not in tension.

## Step 0: Determine Mode

Parse `$ARGUMENTS`:

```bash
if [[ "$ARGUMENTS" == "--all" ]]; then
  ls -d papers/*/ | grep -v "papers/pngs\|papers/tagged" | sort
else
  paper_dir="$ARGUMENTS"
fi
```

If `--cluster paper1,paper2,...` is provided, only consider stances between papers in the specified cluster. This is used by the ingest-collection skill for cluster-based dispatch.

## Step 1: Load All Claims

Read every `claims.yaml` in the collection (or the cluster). Build a mental index: which paper has which claims, what concepts they reference, what values they assert.

```bash
for d in papers/*/; do
  if [ -f "$d/claims.yaml" ]; then
    echo "=== $d ==="
    cat "$d/claims.yaml"
  fi
done
```

Also read the concept registry to understand what concepts are shared across papers:

```bash
ls knowledge/concepts/*.yaml 2>/dev/null | head -50
```

## Step 2: Load Cross-References

For the target paper (or each paper in --all mode), read:
- `<paper_dir>/notes.md` — especially the Collection Cross-References section, Discussion, Arguments Against Prior Work, and Open Questions
- `<paper_dir>/citations.md` — the reference list showing which other papers this one cites

These contain the textual evidence for stances.

## Step 3: Identify Stance Candidates

For each claim in the target paper, ask:
1. Does this claim's concept appear in other papers' claims? (shared concept = potential interaction)
2. Does the notes.md Discussion section mention prior work's findings? (explicit comparison = stance)
3. Is this paper a follow-up or extension of another paper in the collection? (supersedes candidate)
4. Does this paper critique another paper's methodology? (undercuts candidate)

## Step 4: Classify Each Stance

For each candidate, determine the stance type using the precise semantics above. Ask:
- Is the relationship about methodology (undercuts) or conclusions (rebuts)?
- Is it a replacement (supersedes) or a disagreement (rebuts)?
- Is it corroboration (supports) or explanation (explains)?
- Does it attack a premise (undermines) or the conclusion (rebuts)?

## Step 5: Write Standalone stances.yaml

Write stances to a **separate** `stances.yaml` file (do NOT embed in claims.yaml):

```yaml
source:
  paper: <paper_dir_name>

stances:
  - source_claim: "claim3"
    target: "Bowman_2018_EffectsAspirinPrimaryPrevention:claim11"
    type: supports
    strength: "strong"
    note: "Independent replication of null primary prevention result"
  - source_claim: "claim7"
    target: "Unknown_2009_AspirinPrimarySecondaryPrevention:claim7"
    type: undermines
    strength: "moderate"
    note: "Low observed event rates undermine older risk estimates"
```

**Required fields per stance:** `source_claim` (claim ID from this paper), `type` (one of: rebuts, undercuts, undermines, supports, explains, supersedes), `target` (claim ID — see targeting rules below).

**Optional fields:** `strength` (strong/moderate/weak), `note` (textual justification — always include this).

**Claim ID targeting:**
- **Same paper:** use the bare claim ID (e.g., `"claim3"`)
- **Different paper:** use `PaperDirName:claimID` (e.g., `"Bowman_2018_EffectsAspirinPrimaryPrevention:claim11"`). The paper directory name is the folder name under `papers/`.

Write to `<paper_dir>/stances.yaml`.

## Step 6: Ingest into Propstore

```bash
source_name=$(basename "$paper_dir")
pks source add-stance "$source_name" --batch "$paper_dir/stances.yaml"
```

If this fails with claim reference errors, the referenced claim IDs don't match the source branch's claims.yaml. Fix the references and retry.

## Step 7: Stamp Provenance

```bash
uv run plugins/research-papers/scripts/stamp_provenance.py \
  "<paper_dir>/stances.yaml" \
  --agent "<your model name>" --skill extract-stances
```

## Output

When done with each paper:
```
Stances extracted: papers/[dirname]/stances.yaml
  Stances written: N total
    supports: X
    rebuts: X
    undercuts: X
    undermines: X
    explains: X
    supersedes: X
  Cross-paper links: N (targeting claims in M other papers)
```

=== skills/ingest-collection/SKILL.md ===
---
name: ingest-collection
description: Orchestrate a full knowledge store rebuild from a paper collection. Initializes propstore, processes all papers through source branches, extracts cross-paper stances via argumentative clusters, runs concept alignment, promotes all sources, and builds the sidecar.
argument-hint: "<papers-directory> [--knowledge-dir <path>]"
disable-model-invocation: false
compatibility: "Claude Code."
---

# Ingest Collection: $ARGUMENTS

Rebuild a propstore knowledge store from scratch using a collection of papers that already have notes.md and claims.yaml.

## Prerequisites

- Papers directory with subdirectories, each containing at minimum: `paper.pdf`, `notes.md`, `metadata.json`
- `pks` CLI available (propstore installed)
- Existing claims.yaml files will be re-extracted if `--fresh` is specified

## Step 0: Parse Arguments and Validate

```bash
papers_dir="$ARGUMENTS"
knowledge_dir="${papers_dir}/../knowledge"  # default: sibling of papers dir
ls "$papers_dir"/*/notes.md | head -20
```

List all paper directories with their artifact status:
```bash
for d in "$papers_dir"/*/; do
  name=$(basename "$d")
  notes=$([ -f "$d/notes.md" ] && echo "Y" || echo "N")
  claims=$([ -f "$d/claims.yaml" ] && echo "Y" || echo "N")
  justs=$([ -f "$d/justifications.yaml" ] && echo "Y" || echo "N")
  stances=$([ -f "$d/stances.yaml" ] && echo "Y" || echo "N")
  echo "$name  notes=$notes claims=$claims justifications=$justs stances=$stances"
done
```

## Step 1: Initialize Propstore

```bash
# Delete old knowledge store if it exists
rm -rf "$knowledge_dir"
pks init "$knowledge_dir"
```

Verify:
```bash
ls "$knowledge_dir"/.git 2>/dev/null && echo "Propstore initialized"
pks form list
```

## Step 2: Per-Paper Pipeline (Parallel)

For each paper directory, run the per-paper pipeline. These can run in parallel — each paper gets its own isolated source branch.

For each paper:

### 2a: Initialize source branch
```bash
source_name=$(basename "$paper_dir")
# Read metadata.json for origin
pks source init "$source_name" --kind academic_paper \
  --origin-type <doi|arxiv|url|file> --origin-value "<value>" \
  --content-file "$paper_dir/paper.pdf"
pks source write-notes "$source_name" --file "$paper_dir/notes.md"
pks source write-metadata "$source_name" --file "$paper_dir/metadata.json"
```

### 2b: Extract claims (if not already done or --fresh)
```
/research-papers:extract-claims <paper_dir>
```

### 2c: Register concepts
```
/research-papers:register-concepts <paper_dir>
```

### 2d: Extract justifications
```
/research-papers:extract-justifications <paper_dir>
```

### 2e: Finalize (without stances — those come later)
```bash
pks source finalize "$source_name"
```

Report finalize status for each paper before proceeding.

**Parallelization:** If subagents are available, dispatch one agent per paper. Each agent runs steps 2a-2e independently. Wait for all to complete before proceeding to Step 3.

## Step 3: Build Citation Graph and Identify Argumentative Clusters

After all papers are finalized, build a citation graph to identify which papers argue with each other.

Read all papers' citations.md and notes.md Cross-References sections:
```bash
for d in "$papers_dir"/*/; do
  echo "=== $(basename $d) ==="
  grep -A 20 "## Collection Cross-References" "$d/notes.md" 2>/dev/null
  echo "---"
done
```

Identify **argumentative clusters** — groups of papers that:
- Cite each other directly
- Measure the same endpoints in overlapping populations
- Are follow-ups of the same trial
- Have explicit Discussion-section comparisons

Example clusters for aspirin:
- **2018 Megatrials:** ASCEND + ARRIVE + ASPREE (all published 2018, compared in editorials)
- **Diabetes Subgroup:** POPADAD + JPAD + ASCEND (all diabetic populations)
- **ASPREE Chain:** ASPREE mortality + ASPREE-XT follow-up (same cohort)
- **Meta vs Trials:** ATT 2009 meta-analysis vs individual trials it includes

Papers may appear in multiple clusters. That's fine — stances from different clusters will be different.

## Step 4: Extract Stances per Cluster (Parallel)

For each argumentative cluster, dispatch a stance extraction agent:

```
/research-papers:extract-stances <paper_dir> --cluster paper1,paper2,paper3
```

The agent reads all claims within its cluster and extracts stances for each paper in the cluster. Stances go into standalone `stances.yaml` files.

After all cluster agents complete, ingest stances:
```bash
for d in "$papers_dir"/*/; do
  source_name=$(basename "$d")
  if [ -f "$d/stances.yaml" ]; then
    pks source add-stance "$source_name" --batch "$d/stances.yaml"
  fi
done
```

## Step 5: Concept Alignment

After all papers have concepts registered, check for alignment candidates:

```bash
# List all source branches
pks log --oneline | head -20
```

Review concept alignment. The system auto-links exact name matches. For ambiguous cases (same name, different definition; or different name, similar definition), review and decide:

```bash
pks concept alignment status 2>/dev/null
```

Report:
- Auto-linked (exact match): N concepts
- Newly proposed (no match): N concepts
- Alignment candidates (ambiguous): N concepts — list them for Q's review

## Step 6: Promote All Sources

After alignment is resolved, promote each source to master:

```bash
for d in "$papers_dir"/*/; do
  source_name=$(basename "$d")
  pks source promote "$source_name" 2>&1 || echo "FAILED: $source_name"
done
```

## Step 7: Build Sidecar

```bash
pks build
```

Verify:
```bash
pks query "SELECT COUNT(*) FROM claims"
pks query "SELECT COUNT(*) FROM concepts"
pks query "SELECT conflict_type, COUNT(*) FROM conflicts GROUP BY conflict_type"
```

## Step 8: Report

Write to `reports/ingest-collection-report.md`:

- Papers processed: N
- Claims total: N (breakdown by type)
- Concepts: N registered, N aligned, N newly proposed
- Justifications: N total
- Stances: N total (breakdown by type)
- Conflicts detected: N (breakdown by type)
- Argumentative clusters identified: N (list them)
- Source branches: N finalized, N promoted, N blocked
- Any errors or blockers encountered

## Error Recovery

- **Finalize blocked:** Fix the specific errors listed in finalize_report.json, then re-finalize.
- **Promote fails (unresolved concepts):** Run concept alignment, then retry promote.
- **Build fails:** Check `pks validate` output for structural issues.
- **Stance ingestion fails (unknown claim refs):** The referenced paper may not be finalized yet. Ensure all papers are finalized before ingesting stances.

=== skills/lint-paper/SKILL.md ===
---
name: lint-paper
description: Check paper directories for completeness, format compliance, and index consistency. Run on a single paper or --all for the entire collection.
argument-hint: "<papers/Author_Year_Title> or --all"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Lint Paper: $ARGUMENTS

Audit paper directories for completeness and format compliance. No AI needed — just file checks and grep.
Use `papers/db.yaml` as the schema contract for collection-level format expectations.

## Step 0: Determine Mode

```bash
if [[ "$ARGUMENTS" == "--all" ]]; then
  ls -d papers/*/ | grep -v "papers/tagged" | sort
else
  paper_dir="$ARGUMENTS"
fi
```

## Step 1: Check Each Paper

For each paper directory, run all checks and collect results.

### Required Files

| File | Status |
|------|--------|
| `notes.md` | REQUIRED — run paper-reader if missing |
| `description.md` | REQUIRED — run paper-reader if missing |
| `abstract.md` | recommended |
| `citations.md` | recommended |
| `paper.pdf` or `pngs/` | REQUIRED — at least one source artifact must exist. Notes without a verifiable source are untrustworthy. |

### Format Checks

1. **Notes metadata**: Does `notes.md` have YAML frontmatter with at least `title:` and `year:`?
   ```bash
   head -8 "$paper_dir/notes.md" | grep -E "^title:|^year:"
   ```
   Missing → report as `NOTES_METADATA_MISSING`

2. **Tags**: Does `description.md` have YAML frontmatter with a `tags:` field?
   ```bash
   head -5 "$paper_dir/description.md" | grep "tags:"
   ```
   Missing → report as `UNTAGGED`

3. **Wikilinks**: Are cross-references in `notes.md` using `[[wikilinks]]`?
   ```bash
   # Check for old-style bold refs in cross-reference sections
   grep -c '\*\*[A-Z][A-Za-z0-9_]*_[0-9]\{4\}' "$paper_dir/notes.md"
   ```
   Found → report as `LEGACY_BOLD_REFS`

4. **Frontmatter validity**:
   - If `notes.md` has `---` delimiters, is the YAML valid?
   - If `description.md` has `---` delimiters, is the YAML valid?
   - Check that `---` appears on lines 1 and 3+ (not empty frontmatter)
   - Check that `title:` is present in `notes.md`
   - Check that `tags:` value is a list, not empty in `description.md`

5. **Cross-references section**: Does `notes.md` have `## Collection Cross-References`?
   ```bash
   grep -c "## Collection Cross-References" "$paper_dir/notes.md"
   ```
   Missing → report as `NOT_RECONCILED`

### Index Checks

6. **In index**: Is the paper listed in `papers/index.md`?
   ```bash
   grep -c "## $(basename $paper_dir)" papers/index.md
   ```
   Missing → report as `NOT_INDEXED`

7. **Index description matches**: Does the description in `index.md` match `description.md`?
   Only check if both exist — flag `INDEX_STALE` if they differ.

### Source Artifact Checks

8. **Source artifact**: Does the paper have a PDF or page images?
   ```bash
   ls "$paper_dir/paper.pdf" "$paper_dir"/pngs/page-*.png 2>/dev/null | wc -l
   ```
   Zero → report as `NO_SOURCE_ARTIFACT` (notes without a verifiable source are untrustworthy — retrieve the PDF)

9. **Orphan PDF**: Is there a PDF in `papers/` root with a name matching this paper?
   ```bash
   ls papers/*.pdf 2>/dev/null
   ```
   Any root-level PDFs → report as `ORPHAN_PDF` (should have been moved by paper-reader)

10. **Page citations in notes**: Do findings in notes.md include page references?
    ```bash
    grep -c '(p\.[0-9]' "$paper_dir/notes.md"
    ```
    Zero → report as `NO_PAGE_CITATIONS` (re-read paper with updated paper-reader to add page provenance)

## Step 2: Report

### Single Paper Mode

```
Lint: papers/Author_Year_Title/
  ✓ notes.md
  ✓ description.md
  ✓ abstract.md
  ✗ citations.md — MISSING
  ✓ paper.pdf
  ✗ notes metadata — NOTES_METADATA_MISSING
  ✗ tags — UNTAGGED
  ✓ wikilinks
  ✗ cross-references — NOT_RECONCILED
  ✓ indexed
```

### --all Mode

Group by status:

```
Lint: N papers checked

Complete (M papers):
  - Paper1, Paper2, ...

Issues found:

  MISSING notes.md (need paper-reader):
    - Paper3

  MISSING description.md (need paper-reader):
    - Paper4

  NOTES_METADATA_MISSING (need migrate_notes_frontmatter.py or re-run paper-reader):
    - Paper4a

  UNTAGGED (need tag-papers):
    - Paper5, Paper6, Paper7, ...

  NOT_RECONCILED (need reconcile):
    - Paper8, Paper9

  LEGACY_BOLD_REFS (need migrate-format.py):
    - Paper10

  NOT_INDEXED (need generate-paper-index.py):
    - Paper11

  ORPHAN_PDF (unprocessed PDFs in papers/ root):
    - somefile.pdf
```

Then a summary line:
```
Summary: M complete, N issues across K papers
```

## Do NOT:

- Modify any files (this is read-only audit)
- Read PDF content or page images
- Use AI/LLM features (this is pure file/grep checks)

=== skills/make-skill/SKILL.md ===
---
name: make-skill
description: Create new skills from existing prompts or workflow patterns. Analyzes prompt files to extract reusable structure, determines appropriate frontmatter settings, and generates properly formatted SKILL.md files.
argument-hint: "[prompt-path(s)] [--name name] [--global]"
allowed-tools: Read, Write, Bash(mkdir:*), Bash(ls:*), Glob
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Make Skill: $ARGUMENTS

Create a new skill from existing prompt file(s).

## Step 1: Parse Arguments

Extract from `$ARGUMENTS`:
- **paths**: Prompt file paths or glob patterns (e.g., `./prompts/research-*.md`, `./prompts/paper-reader.md`)
- **--name NAME**: Optional explicit skill name (otherwise derived from content)
- **--global**: If present, install to the user-level skills directory for the active platform instead of the repo-local skills directory

## Step 2: Read Source Prompts

```bash
# If glob pattern, expand it first
ls $PATHS 2>/dev/null || echo "No matches"
```

Read all matching prompt files.

## Step 3: Analyze Patterns

For each prompt, identify:

### Fixed Elements (Boilerplate)
- Output format templates
- Section headers
- Standard instructions
- Safety boilerplate (file error workarounds, parallel swarm awareness)

### Variable Elements
- Topic/subject (what `$ARGUMENTS` would replace)
- Input file paths
- Output file paths/names
- Domain-specific content

### Workflow Characteristics
- **Research/reading**: Searches web, reads many files, investigates
- **Implementation**: Modifies code, creates/edits files
- **Audit/review**: Reads code, produces reports
- **Commit/deploy**: Git operations, side effects

## Step 4: Determine Frontmatter

Based on analysis, select appropriate settings:

### Context & Agent
```yaml
# If the skill reads many files or does web research:
context: fork
agent: general-purpose

# If the skill is simple/linear with few file reads:
# (omit context - defaults to inline)
```

### Model Invocation
```yaml
# If skill has side effects (commits, edits code, deploys):
disable-model-invocation: true

# If skill is read-only or research:
# (omit - allows external model calls)
```

### Tool Restrictions
```yaml
# Read-only research/analysis:
allowed-tools: Read, WebSearch, WebFetch, Glob, Grep

# File creation without code modification:
allowed-tools: Read, Write, Bash(mkdir:*), Bash(mv:*), Bash(rm:*), Bash(ls:*)

# Full implementation work:
# (omit - allows all tools)
```

### Name & Description
```yaml
name: [derived-from-content-or-explicit]
description: [One sentence describing what skill does and when to use it]
argument-hint: [what arguments look like]
```

## Step 5: Generate Skill Content

Create the SKILL.md with:

1. **YAML frontmatter** (determined above)

2. **Title**: `# [Skill Name]: $ARGUMENTS`

3. **Objective section**: What the skill accomplishes

4. **Steps**: Numbered steps extracted from prompts, generalized:
   - Replace hardcoded values with `$ARGUMENTS` or parameters
   - Keep structural instructions
   - Include decision trees where appropriate

5. **Output format**: Template for results

6. **Safety boilerplate** (ALWAYS include):
```markdown
---

## CRITICAL: File Modified Error Workaround

If Edit/Write fails with "file unexpectedly modified":
1. Read the file again
2. Retry the edit
3. Try path formats: `./relative`, `C:/forward/slashes`, `C:\back\slashes`
4. Prefer your file editing tools over shell text manipulation (cat, sed, echo)
5. If all formats fail, STOP and report

## CRITICAL: Parallel Swarm Awareness

You may be running alongside other agents. NEVER use git restore/checkout/reset/clean.

---
```

7. **Completion instructions**:
```markdown
## Completion

When done, reply ONLY:
\`\`\`
Done - [brief description of output location]
\`\`\`

Do NOT:
- Output findings to conversation
- Modify files outside scope
- Leave temporary files behind
```

## Step 6: Determine Location

```bash
# Project-specific (default)
mkdir -p "./.agents/skills/[skill-name]"
# Output: ./.agents/skills/[skill-name]/SKILL.md

# Global (if --global flag)
# Codex: ~/.codex/skills/[skill-name]
# Claude/Gemini: use that platform's user-level skills directory
```

## Step 7: Write Skill File

Write the generated SKILL.md to the appropriate location.

## Step 8: Show Summary

Present to user:

```markdown
## Skill Created

**Name:** [skill-name]
**Location:** [path to SKILL.md]
**Description:** [description]

### Frontmatter Settings
- context: [value or "default (inline)"]
- agent: [value or "default"]
- disable-model-invocation: [true/false]
- allowed-tools: [list or "all"]

### Pattern Analysis
**Fixed elements:** [what stays constant]
**Variable elements:** [what $ARGUMENTS replaces]
**Source prompts:** [list of files analyzed]

### Usage
```
$[skill-name] [example-arguments]
```

**Confirm creation? [Y/n]**
```

Wait for user confirmation before finalizing. If user says no or requests changes, iterate.

---

## CRITICAL: File Modified Error Workaround

If Edit/Write fails with "file unexpectedly modified":
1. Read the file again
2. Retry the edit
3. Try path formats: `./relative`, `C:/forward/slashes`, `C:\back\slashes`
4. Prefer your file editing tools over shell text manipulation (cat, sed, echo)
5. If all formats fail, STOP and report

## CRITICAL: Parallel Swarm Awareness

You may be running alongside other agents. NEVER use git restore/checkout/reset/clean.

---

## Completion

When user confirms, reply:
```
Done - created [path to SKILL.md]
```

Do NOT:
- Create skills without showing summary first
- Overwrite existing skills without warning
- Create documentation files beyond SKILL.md

=== skills/paper-process/SKILL.md ===
---
name: paper-process
description: Retrieve a paper, extract notes, and ingest into propstore. Combines paper-retriever, paper-reader, register-concepts, extract-claims, and extract-justifications into one pks-aware pipeline. Give it a URL, DOI, or title.
argument-hint: "<url-or-doi-or-title>"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Paper Process: $ARGUMENTS

Download a scientific paper, extract structured notes, register concepts, extract claims and justifications, and ingest everything into a propstore source branch.

This is the per-paper propstore ingestion orchestrator. `paper-reader` remains a paper-artifact skill; collection-wide stance extraction belongs to `ingest-collection`.

## Execution Discipline

This skill is a checklist, not an outcome sketch.

**CRITICAL:**
This skill does NOT authorize creating any new scripts, automation, temp programs, or alternate workflows.
If the listed commands or nested skills cannot complete a step, stop immediately and report the blocker.

- Follow the steps in order.
- `$ARGUMENTS` names exactly one intended paper. Preserve that paper's identity through retrieval, reading, claim extraction, and reporting.
- Do not substitute unlisted scripts, tools, or custom workflows for retrieval, reading, or claim extraction.
- If you can invoke the named nested skill, do that. If you cannot, use the fallback helper below and follow its stdout literally.
- If you are blocked on a specific step, stop there and report the exact blocker instead of inventing a workaround.
- Do not report progress from intermediate artifacts not named in this procedure.
- If the input is a weak locator, first infer the intended paper and continue with the strongest identity-preserving input available (DOI, ACL ID/URL, arXiv ID/URL, S2 ID, exact title, or direct PDF URL).
- If retrieval resolves to a materially different paper than the one named by `$ARGUMENTS`, stop and report the mismatch instead of continuing.

## Step 1: Retrieve the Paper

### Primary: Skill Invocation (Claude Code and compatible platforms)

Invoke the paper-retriever skill directly:

```
/research-papers:paper-retriever $ARGUMENTS
```

Retrieval succeeds only when the intended paper's PDF exists at the output path. Do not treat "some related paper was found" as success.

When retrieval completes, note the output path (e.g., `papers/Author_Year_ShortTitle/paper.pdf`).

### Fallback (Codex CLI, Gemini CLI, or platforms where skill invocation fails)

Use this skill's injected `<path>` to locate the installed `paper-process` skill directory, then run:

```bash
uv run "<skill-dir>/scripts/emit_nested_process_fallback.py"
```

Read the FULL stdout and follow it exactly instead of opening sibling `SKILL.md` files piecemeal.

## Step 2: Read and Extract Notes

### Primary: Skill Invocation (Claude Code and compatible platforms)

Invoke the paper-reader skill with the path from Step 1:

```
/research-papers:paper-reader <path-from-step-1>
```

Follow all instructions through to completion (notes.md, description.md, abstract.md, citations.md, index.md update).

### Fallback (Codex CLI, Gemini CLI, or platforms where skill invocation fails)

If you already ran the `emit_nested_process_fallback.py` helper in Step 1, follow the paper-reader section of that output. Otherwise, follow the paper-reader SKILL.md instructions directly.

## Step 3: Clean Up Source PDF

If the original argument was a local file path (e.g., `papers/somefile.pdf` in the root of `papers/`), and the paper directory now contains `paper.pdf`, **delete the original root-level PDF**:

```bash
# Only if the source was a local file and the paper dir copy exists
rm "./papers/somefile.pdf"
```

This keeps the `papers/` root clean — any PDF still in the root is unprocessed. Do NOT delete if the source was a URL (nothing to clean up) or if the paper directory doesn't have `paper.pdf` yet (something went wrong).

## Step 4: Initialize Propstore Source Branch

```bash
paper_dir="<paper-directory-path>"
source_name=$(basename "$paper_dir")
```

Read metadata.json to determine origin:
```bash
cat "$paper_dir/metadata.json"
```

Initialize the source branch:
```bash
pks source init "$source_name" \
  --kind academic_paper \
  --origin-type <doi|arxiv|url|file> \
  --origin-value "<doi-or-url-or-path>" \
  --content-file "$paper_dir/paper.pdf"
```

Push notes and metadata:
```bash
pks source write-notes "$source_name" --file "$paper_dir/notes.md"
pks source write-metadata "$source_name" --file "$paper_dir/metadata.json"
```

If `pks` is not available or `knowledge/` doesn't exist, STOP and report: "No propstore found. Run `pks init` on the knowledge directory first."

## Step 5: Extract Claims

### Primary: Skill Invocation

```
/research-papers:extract-claims <paper-directory-path>
```

The skill will use canonical concept names from any existing concepts.yaml and ingest claims via `pks source add-claim`.

### Fallback

Follow the extract-claims SKILL.md instructions directly on the paper directory.

## Step 6: Register Concepts

### Primary: Skill Invocation

```
/research-papers:register-concepts <paper-directory-path>
```

This runs `propose_concepts.py pks-batch` to extract concept names from claims.yaml, enriches definitions from notes.md, and calls `pks source add-concepts`.

### Fallback

Follow the register-concepts SKILL.md instructions directly.

**Note:** register-concepts runs AFTER extract-claims because it derives the concept inventory from claims.yaml. The pipeline is: extract claims first (using descriptive names), then register concepts (deriving from what claims actually reference), then the pks source branch links concepts to claims during finalize.

## Step 7: Extract Justifications

### Primary: Skill Invocation

```
/research-papers:extract-justifications <paper-directory-path>
```

The skill writes justifications.yaml and ingests via `pks source add-justification`.

### Fallback

Follow the extract-justifications SKILL.md instructions directly.

## Step 8: Finalize Source Branch

```bash
pks source finalize "$source_name"
```

Read the finalize report:
```bash
cat "$paper_dir/finalize_report.json" 2>/dev/null || echo "Check pks source branch for report"
```

If status is "blocked", report the errors. Common issues:
- Unknown concept references → re-run register-concepts
- Missing claim artifact IDs → re-run add-claim
- Unlinked concepts → alignment needed (resolved at collection level)

**Note:** Stances are NOT extracted here. Cross-paper stance extraction happens at collection level via the ingest-collection skill, after all papers have claims. This is because stances require visibility into other papers' claims.

## Step 9: Report

When all steps have completed, write a summary to `./reports/paper-$SAFE_NAME.md` where $SAFE_NAME is derived from the paper directory name. Include:

- Paper directory path
- Whether retrieval succeeded (and source: arxiv/sci-hub/etc.)
- Whether reading succeeded
- Whether claim extraction succeeded (claim count by type)
- Whether concept registration succeeded (N exact-match links, N newly proposed)
- Whether justification extraction succeeded (justification count)
- Whether finalize succeeded (status: ready/blocked)
- Usefulness rating for this project

## Error Handling

- If retrieval fails: report failure and stop. Do not proceed to reading.
- If reading fails: report what was retrieved but note the reading failure. Do not proceed to claim extraction.
- If claim extraction fails: report what was retrieved and read but note the extraction failure.
- If pks source init fails: report the error. This may mean propstore is not initialized.
- If finalize is blocked: report the specific errors. The paper is still usable — finalize can be re-run after fixing issues.

=== skills/paper-reader/SKILL.md ===
---
name: paper-reader
description: Read scientific papers and extract implementation-focused notes. Converts PDFs to page images, then reads them. Papers <=50pp are read directly; papers >50pp are chunked into 50-page ranges for thorough parallel extraction. Creates structured notes in papers/ directory.
argument-hint: "[path/to/paper.pdf]"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI. Requires shell access; subagents are optional but improve large-paper throughput."
---

# Paper Reader: $ARGUMENTS

Read a scientific paper and create comprehensive implementation-focused notes.

## Execution Discipline

This skill is a checklist, not an outcome sketch.

- Follow the steps in order.
- Do not substitute alternate text-extraction or summarization workflows for the required page-image reading flow unless this skill explicitly tells you to.
- Do not add unlisted probes or "better" preprocessing steps.
- If you are blocked on a specific step, stop there and report the exact blocker instead of inventing a workaround.
- Do not report progress from intermediate artifacts not named in this procedure.
- This skill stops at paper artifacts and collection cross-references. It does not initialize or mutate propstore source branches.
- Do not declare yourself blocked merely because this skill does not name a platform-specific image-view tool. Use the platform's local image-reading capability (for example, `Read Image` in Claude Code or `view_image` in Codex) to inspect `pngs/page-*.png`.
- Only report an image-reading blocker after you have actually attempted to inspect a local page image such as `page-000.png` and the platform refused or failed.

## Extraction Objective

The target output in this repo is a **dense paper surrogate**, not a sharpened executive summary.

- Favor **high recall over compression**.
- Preserve the paper's formal content, definitions, equations, thresholds, algorithm steps, caveats, and section-level structure.
- Do **not** collapse notes into only the "main idea" or a few elegant abstractions.
- Do **not** optimize for brevity. Optimize for faithful extraction with useful organization.
- The standard is: a later reader should rarely need to reopen the PDF except to inspect a figure in full detail.

## Subagent Model Policy

Paper extraction is high-stakes and context-heavy. If you dispatch any subagent for reading, chunk extraction, synthesis, abstract extraction, citations extraction, or end-to-end paper processing:

- Use the **strongest available full-size model** on the platform.
- **Never** use a mini, small, flash, nano, lightweight, or economy tier model for paper extraction work.
- If the platform exposes named model choices, choose the top-tier frontier model rather than a cheaper/faster variant.
- If the strongest full model is unavailable, do the work yourself instead of delegating to a weaker mini-tier worker.

## Script Paths

The command examples below use `scripts/...` paths that are relative to this skill's directory. Resolve them against the installed skill location, not the user's project root.

## Step 0: Check for Existing Paper

If the argument is a directory, use it directly. If it's a PDF file, use `paper_hash.py lookup` to find a matching paper directory:

```bash
paper_path="$ARGUMENTS"
if [ -d "$paper_path" ]; then
  paper_dir="$paper_path"
elif [ -f "$paper_path" ]; then
  HASH_SCRIPT="scripts/paper_hash.py"
  if [ -f "$HASH_SCRIPT" ]; then
    paper_dir=$(python3 "$HASH_SCRIPT" --papers-dir papers/ lookup "$(basename "$paper_path" .pdf)" 2>/dev/null)
    [ $? -ne 0 ] && paper_dir=""
    [ -n "$paper_dir" ] && paper_dir="papers/$paper_dir"
  else
    basename=$(basename "$paper_path" .pdf)
    paper_dir=$(ls -d papers/*/ 2>/dev/null | grep -i "${basename%_*}" | head -1)
  fi
fi
```

### Case A: No existing directory found
Continue to Step 1.

### Case B: Directory exists — check gaps

```bash
ls -la "$paper_dir"/*.md 2>/dev/null
ls "$paper_dir"/pngs/ 2>/dev/null | head -3
ls "$paper_dir"/*.pdf 2>/dev/null | head -1
```

- **No `notes.md`?** Incomplete — continue to Step 1.
- **No `notes.md`, but `paper.pdf` and `pngs/page-000.png` already exist?** This is a rerun/regeneration case. Do **not** rename or move files. Reuse the existing paper directory, inspect the existing page images directly, and continue to Step 1 with the existing assets.
- **No `notes.md`, `paper.pdf` exists, but `pngs/` is missing or incomplete?** Regenerate `pngs/` from the existing `paper.pdf`, then continue.
- **All files present (notes + abstract + citations)?** If the argument was a root-level PDF (i.e., NOT inside a paper directory's own folder), delete it (`rm "$paper_path"`). **NEVER delete a PDF that lives inside its own paper directory** (e.g., `papers/Author_Year/paper.pdf`). Report "Already complete," stop.
- **Missing abstract.md and/or citations.md?** Fill gaps using page images or PDF, then delete root PDF and stop. See Steps 5-6 for format.

---

## Step 1: Determine Working PDF and Reuse/Convert Assets

First determine the working PDF path:

```bash
paper_path="$ARGUMENTS"
if [ -d "$paper_path" ]; then
  paper_dir="$paper_path"
  work_pdf="$paper_dir/paper.pdf"
else
  work_pdf="$paper_path"
fi
```

If you are in a rerun/regeneration case and `"$paper_dir"/pngs/page-000.png` already exists, **reuse the existing page images**. Do not reconvert just because `notes.md` is missing.

Get page count:
```bash
pdfinfo "$work_pdf" 2>/dev/null | grep Pages || echo "pdfinfo not available"
```

If `pngs/page-000.png` does not already exist, extract page 0 first in a temp dir for metadata:

```bash
tmpdir=$(mktemp -d)
magick -density 150 "$work_pdf[0]" -quality 90 -resize '1960x1960>' "$tmpdir/page0.png"
```

Read either the existing `pngs/page-000.png` or `$tmpdir/page0.png` to extract author, year, and title. Determine directory name: `LastName_Year_2-4WordTitle` (e.g., `Mack_2021_AccessibilityResearchSurvey`).

For a new paper, set:

```bash
paper_dir="./papers/Author_Year_ShortTitle"
```

If this is a new paper, create the output directory and convert all pages:
```bash
mkdir -p "$paper_dir/pngs"
# Move source PDF into paper directory — skip if already there
if [ "$(realpath "$work_pdf")" != "$(realpath "$paper_dir/paper.pdf")" ]; then
  mv "$work_pdf" "$paper_dir/paper.pdf"  # MUST be mv, NEVER cp
fi
magick -density 150 "$paper_dir/paper.pdf" -quality 90 -resize '1960x1960>' "$paper_dir/pngs/page-%03d.png"
rm -rf "$tmpdir"
```

If this is an existing paper directory with `paper.pdf` present but missing/incomplete `pngs/`, regenerate:
```bash
mkdir -p "$paper_dir/pngs"
magick -density 150 "$paper_dir/paper.pdf" -quality 90 -resize '1960x1960>' "$paper_dir/pngs/page-%03d.png"
rm -rf "$tmpdir"
```

**CRITICAL: Use `mv`, NEVER `cp`.** The root-level PDF must be removed. A PDF left in `papers/` root is indistinguishable from an unprocessed paper.

**CRITICAL: Never write temp files to `papers/` root.** Use `mktemp -d` for temp work.

Count pages:
```bash
ls "$paper_dir"/pngs/page-*.png | wc -l
```

**Decision:**
- **≤50 pages**: Read all page images yourself (Step 2A)
- **>50 pages**: Chunk protocol (Step 2B)

## Step 1.5: Prove the Page-Image Lane Works

Before long extraction, inspect `page-000.png` from the paper's `pngs/` directory using the platform's local image-reading capability (for example, `Read Image` in Claude Code or `view_image` in Codex).

- This is the intended workflow. It is **not** an OCR/text-extraction fallback.
- Do not stop just because the exact tool name is unspecified in this skill.
- Only stop if you actually attempted to inspect `page-000.png` and the platform prevented it.

Once `page-000.png` is visible, continue immediately to Step 2A or Step 2B.

---

## Step 2A: Direct Read (≤50 pages)

**CRITICAL: Read EVERY page image. No skipping, no sampling, no "reading enough to get the gist."** Read every single `page-NNN.png` file from `page-000` through the last page. If you have 34 pages, read 34 page images. Agents routinely skip pages to save tokens — this produces incomplete notes that miss equations, parameters, and key details buried in middle sections. The entire point of reading the paper is completeness. If you skip pages, the notes are worthless.

For papers with 50 pages or fewer, the assigned worker must do this reading itself. Do **not** dispatch additional readers for a small paper.

Take thorough notes as you go. Continue to Step 3.

---

## Step 2B: Chunk Protocol (>50 pages)

Split into **50-page chunks**. Calculate ranges:
- Chunk 1: pages 000-049
- Chunk 2: pages 050-099
- Last chunk: whatever remains

### Write ONE Template Prompt

Write to `./prompts/paper-chunk-reader.md`:

```markdown
# Task: Read Paper Chunk and Extract Notes

## Context
You are reading a chunk of [PAPER TITLE] being processed in parallel.
Page images: `./papers/Author_Year_ShortTitle/pngs/page-NNN.png`

Use the strongest available full-size model for this job. Do not use any mini/small tier model.

## Your Chunk
**START_PAGE** to **END_PAGE** (inclusive)

Read each page image in your range. Be exhaustive — extract EVERY equation, parameter, algorithm step, implementation detail, limitation, criticism of prior work, and design rationale. Do not summarize away formal content or skip "minor" material. **Tag every finding with its page number** using *(p.N)* notation — downstream claim extraction depends on this.

## Output Format
Write DIRECTLY to `./papers/Author_Year_ShortTitle/chunks/chunk-STARTPAGE-ENDPAGE.md`:

# Pages START-END Notes

## Chapters/Sections Covered
## Key Findings
## Equations Found (LaTeX)
## Parameters Found (table)
## Rules/Algorithms
## Figures of Interest
## Quotes Worth Preserving
## Implementation Notes

## CRITICAL: Parallel Swarm Awareness
You are running alongside other chunk readers.
- Only write to YOUR chunk file in the chunks/ directory
- NEVER use git restore/checkout/reset/clean
```

### Process All Chunks

```bash
mkdir -p "./papers/Author_Year_ShortTitle/chunks"
```

**If you can dispatch parallel subagents**, launch one per chunk simultaneously. Each reads its page range and writes to `chunks/chunk-START-END.md`. Use the strongest available full-size model for every chunk worker. Never use a mini/small tier worker for chunk extraction.

Do not dispatch chunk workers until you have successfully inspected at least one local page image from this paper yourself. If you cannot inspect even `page-000.png`, that is a concrete blocker and you should stop there.

**If parallel dispatch is not available**, process each chunk sequentially yourself.

### Synthesize

Read all `chunks/chunk-*.md` files and synthesize into `notes.md`. Merge, deduplicate, and organize into the format from Step 3. Preserve detail; synthesis should reorganize and deduplicate, not compress the paper into sparse abstractions. If you can dispatch a synthesis subagent, do so using the strongest available full-size model; otherwise do it yourself.

Continue to Step 3.

---

## Step 3: Write Notes

**Be exhaustive.** Extract every equation, every parameter, every algorithm, every stated limitation, every criticism of prior work, and every explicit design choice the authors justify. The goal is that someone implementing this paper never needs to open the PDF. More detail is better than elegant compression.

Write to `./papers/Author_Year_ShortTitle/notes.md`:

```markdown
---
title: "[Full Paper Title]"
authors: "[All authors]"
year: [Year]
venue: "[Journal/Conference/Thesis]"
doi_url: "[If available]"
---

# [Full Paper Title]

## One-Sentence Summary
[What this paper provides for implementation - be specific]

## Problem Addressed
[What gap or issue does this paper solve?]

## Key Contributions
- [Contribution 1]
- [Contribution 2]

## Study Design (empirical papers)
- **Type:** [RCT / cohort / case-control / meta-analysis / systematic review / cross-sectional / etc.]
- **Population:** [N, demographics, inclusion/exclusion criteria] *(p.N)*
- **Intervention(s):** [what was administered, dosage, duration, route] *(p.N)*
- **Comparator(s):** [placebo, active control, standard of care] *(p.N)*
- **Primary endpoint(s):** [what was measured as the main outcome] *(p.N)*
- **Secondary endpoint(s):** [additional outcomes] *(p.N)*
- **Follow-up:** [duration, completeness, dropout rates] *(p.N)*

*Leave this section empty for non-empirical papers (pure theory, algorithms, proofs).*

## Methodology
[High-level description of approach — experimental design, computational method, analytical framework, etc.]

## Key Equations / Statistical Models

$$
[equation in LaTeX]
$$
Where: [variable definitions with units]
*(p.N)*

*Include statistical models (regression specifications, survival models, Bayesian priors) alongside mathematical equations. For clinical papers, capture the primary analysis model even if not presented in formal notation.*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|

*Capture every measurable quantity: physical constants, algorithm thresholds, dosages, sample sizes, hazard ratios, odds ratios, confidence intervals, p-value thresholds, effect sizes — whatever the paper's domain uses.*

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|

*One row per reported effect. Use for any empirical paper — clinical trials, A/B tests, benchmarks, ablation studies. Measure column: HR, OR, RR, RD, ATE, Cohen's d, accuracy, F1, BLEU, etc. Include both primary and subgroup results.*

## Methods & Implementation Details
- Study protocol / experimental setup *(p.N)*
- Statistical methods and software used *(p.N)*
- Data structures / algorithms needed *(p.N)*
- Initialization procedures / calibration *(p.N)*
- Edge cases / sensitivity analyses *(p.N)*
- Pseudo-code if provided *(p.N)*
- Adverse events / safety monitoring (clinical papers) *(p.N)*

## Figures of Interest
- **Fig N (p.X):** [What it shows]

## Results Summary
[Key findings — performance characteristics, clinical outcomes, effect magnitudes, statistical significance] *(p.N)*

## Limitations
[What authors acknowledge doesn't work] *(p.N)*

## Arguments Against Prior Work
- [What specific prior approaches does this paper criticize?] *(p.N)*
- [What failure modes or limitations of prior work does it identify?] *(p.N)*
- [What evidence does it present for the criticism?] *(p.N)*

## Design Rationale
- [What architectural choices does this paper justify?] *(p.N)*
- [What alternatives were considered and why were they rejected?] *(p.N)*
- [What properties does the chosen design preserve that alternatives don't?] *(p.N)*

## Testable Properties
- [Property 1: e.g., "Parameter X must be in [low, high]"] *(p.N)*
- [Property 2: e.g., "Increasing A must increase B"] *(p.N)*
- [Property 3: e.g., "Treatment effect HR < 1.0 for primary endpoint"] *(p.N)*
- [Property 4: e.g., "NNT for outcome Y = Z over N years"] *(p.N)*
- [Property 5: e.g., "Subgroup analysis shows effect modification by age"] *(p.N)*

## Relevance to Project
[How this paper applies to the project's research domain]

## Open Questions
- [ ] [Unclear aspects]

## Related Work Worth Reading
- [Papers cited worth following]
```

### Frontmatter Schema

- Required: `title`, `year`
- Recommended: `authors`, `venue`, `doi_url`
- Optional: `pages`, `affiliation`, `affiliations`, `institution`, `publisher`, `supervisor`, `supervisors`, `funding`, `pacs`, `note`, `correction_doi`, `citation`
- Legacy aliases (do not emit in new papers): `author`, `doi`, `url`, `journal`, `type`, `paper`

## Step 3.5: Write metadata.json

Write `./papers/Author_Year_ShortTitle/metadata.json`.

Use this schema and fill every field you can from the paper/frontmatter:

```json
{
  "title": "Full Paper Title",
  "authors": ["Author One", "Author Two"],
  "year": "2024",
  "arxiv_id": null,
  "doi": "10.xxxx/xxxxx",
  "abstract": "Exact or near-exact abstract text",
  "url": null,
  "pdf_url": null
}
```

Rules:
- `title`, `authors`, and `year` are required.
- `authors` must be a JSON array, not a single string.
- Use `null` for unknown fields rather than omitting them.
- `doi` should be the DOI string without `https://doi.org/` when possible.
- If the paper is on arXiv, fill `arxiv_id`.

---

## Extraction Guidelines

### Parameter Table Format (MANDATORY)

| Name | Symbol | Units | Default | Range | Notes |
|------|--------|-------|---------|-------|-------|
| Fundamental frequency | F0 | Hz | 120 | 60-500 | Male speaker baseline |
| Aspirin dose | — | mg/day | 100 | 75-325 | Low-dose range |
| Hazard ratio (MACE) | HR | — | 0.89 | 0.77-1.03 | Primary composite endpoint |
| Learning rate | α | — | 0.001 | 1e-5–0.1 | Adam optimizer |

**Rules:**
- **One row per parameter.** Each row is one measurable quantity — physical constants, algorithm thresholds, dosages, effect sizes, confidence bounds.
- **Name column required.** Full descriptive name.
- **Units column required.** SI, standard domain units, or `-` for dimensionless ratios/rates.
- **Default/Range**: At least one must be populated. `X-Y` for ranges. For effect sizes, the point estimate goes in Default, the CI goes in Range.
- **Notes**: Source table/figure, conditions, caveats, subgroup.

**If a parameter varies by context**, create **one table per context** (e.g., "Modal Voice Parameters", "Breathy Voice Parameters", "Age ≥75 Subgroup", "Intention-to-Treat Analysis").

**DO NOT use matrix format** (parameters as columns, contexts as rows). The extractor expects parameters as rows.

**Measurement/data tables** use descriptive headers with units in parentheses: `F1 (Hz)`, `Duration (ms)`, `HR (95% CI)`.

### Equation Format (MANDATORY)

- One equation per `$$` block
- No prose, markdown, or headers inside `$$` blocks
- Variable definitions go in prose AFTER the equation block
- Use standard LaTeX notation

### Page Citations (MANDATORY)

**Every finding must include its page number.** You are reading page images — you know which page you are on. Tag every equation, parameter, key finding, definition, and testable property with `*(p.N)*` where N is the page number. This is not optional — downstream claim extraction depends on page provenance to produce valid claims. A finding without a page number is a finding that cannot be traced back to the source.

- Equations: `*(p.12)*` after the Where: block
- Parameters: `Page` column in the parameter table
- Key findings / contributions: `*(p.N)*` inline
- Testable properties: `*(p.N)*` at end of each bullet
- Implementation details: `*(p.N)*` at end of each bullet
- Figures: already use `(p.X)` format — keep doing this

### Extraction Targets

- **Equations / Statistical Models**: Every equation and model specification with all variables defined and units given, with page citation. Includes regression models, survival models, Bayesian specifications — not just pure math.
- **Parameters**: Every parameter, constant, threshold, dosage, effect size, and confidence interval — values, ranges, defaults, source, page
- **Effect Sizes**: Every reported effect with measure type (HR, OR, RR, RD, Cohen's d, accuracy, etc.), point estimate, CI, p-value, and population context — with page citation
- **Algorithms / Protocols**: Numbered steps with inputs, outputs, state, page citation. For clinical studies: treatment protocols, randomization procedures, endpoint adjudication criteria.
- **Testable Properties**: Bounds, monotonic relationships, invariants, clinical thresholds, NNT/NNH, subgroup interactions — with page citation

---

## Step 4: Write Description

Write `./papers/Author_Year_ShortTitle/description.md`:

```markdown
---
tags: [tag1, tag2, tag3]
---
[Sentence 1: What the paper does/presents]
[Sentence 2: Key findings/contributions]
[Sentence 3: Relevance to this project's research domain]
```

Single paragraph, no blank lines between sentences. Tags: 2-5, lowercase, hyphens for multi-word, prefer existing tags from `papers/index.md`.

---

## Step 5: Write Abstract

Write `./papers/Author_Year_ShortTitle/abstract.md`:

```markdown
# Abstract

## Original Text (Verbatim)

[Exact abstract text from the paper]

---

## Our Interpretation

[2-3 sentences: What problem? Key finding? Why relevant?]
```

For chunked papers, if you can dispatch a subagent for this extraction, do so using `pngs/page-000.png` and the strongest available full-size model. Do not use a fast/mini/small model here. Otherwise, read `pngs/page-000.png` yourself and write `abstract.md`.

---

## Step 6: Write Citations

Write `./papers/Author_Year_ShortTitle/citations.md`:

```markdown
# Citations

## Reference List

[Every citation from References/Bibliography, preserving original formatting]

## Key Citations for Follow-up

[3-5 most relevant citations with brief notes on why]
```

For chunked papers, if you can dispatch a subagent for this extraction, do so using the last 5-10 page images and the strongest available full-size model. Do not use a fast/mini/small model here. Otherwise, read those pages yourself and write `citations.md`.

**Steps 5 and 6 can run in parallel** since they write to different files.

---

## Step 7: Cross-Reference Collection

Invoke the **reconcile** skill on `papers/Author_Year_ShortTitle` if skill invocation is available. Otherwise, follow the reconcile skill instructions directly on that directory. This handles forward/reverse cross-referencing, reconciliation of citing papers, and backward annotations.

If nested skill invocation is unavailable or unreliable on this platform, derive this skill's
installed directory from the injected `<path>`, then run:

```bash
uv run "<skill-dir>/../reconcile/scripts/emit_nested_reconcile_fallback.py"
```

Read the FULL stdout and follow it exactly on the current paper directory instead of opening
`reconcile/SKILL.md` piecemeal.

Wait for reconcile to complete before proceeding.

---

## Step 8: Update papers/index.md

Append:
```markdown
## Author_Year_ShortTitle  (tag1, tag2, tag3)
[description.md body text — no frontmatter, no tags line]
```

**This step is NOT optional.** Without it, future sessions won't know this paper exists.

---

## Step 9: Stamp Provenance

```bash
uv run plugins/research-papers/scripts/stamp_provenance.py \
  "papers/<Author_Year_ShortTitle>/notes.md" \
  --agent "<your model name>" --skill paper-reader
```

This records which model read the paper, when, and which plugin version was used. Plugin version is autodetected.

---

## Quality Checklist

- [ ] All equations with variable definitions and page citations
- [ ] All parameters in standard table format with Page column
- [ ] Algorithm steps numbered with page citations
- [ ] Figures described with page numbers
- [ ] Key findings and testable properties have page citations
- [ ] Limitations section filled
- [ ] Testable properties extracted
- [ ] description.md written
- [ ] abstract.md written
- [ ] citations.md written
- [ ] metadata.json written
- [ ] Reconcile skill invoked
- [ ] papers/index.md updated
- [ ] Provenance stamped on notes.md
- [ ] No temp files left behind

---

## Output

All papers produce: `papers/Author_Year_Title/` containing `notes.md`, `metadata.json`, `description.md`, `abstract.md`, `citations.md`, `pngs/`, and an updated `papers/index.md` entry.

Papers >50 pages also produce `chunks/`.

When done:
```
Done - created papers/[dirname]/
  - index.md updated
  - Reconciliation: [summary]
```

Then provide a brief **usefulness assessment** in the conversation (not a file):

```
## Usefulness to This Project

**Rating:** [High/Medium/Low/Marginal]
**What it provides:** [concrete takeaways]
**Actionable next steps:** [what to implement or investigate]
**Skip if:** [when this paper isn't relevant]
```

---

Do NOT:
- Delete page images or chunk reports
- Output findings to conversation instead of files
- Skip index.md update (Step 8) or reconcile (Step 7)
- Write ANY temp files to `papers/` root
- Use `cp` instead of `mv` for the source PDF

=== skills/paper-retriever/SKILL.md ===
---
name: paper-retriever
description: Retrieve a scientific paper PDF given an arxiv URL, DOI, or paper title. Downloads to papers/ directory. Uses direct download for arxiv, Chrome + sci-hub for paywalled papers.
argument-hint: "<arxiv-url-or-doi> [optional-output-name]"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI. Requires shell access; browser automation is optional for paywalled papers."
---

# Paper Retriever: $ARGUMENTS

Download a scientific paper PDF to the `papers/` directory.

## Script Paths

The command examples below use `scripts/...` paths that are relative to this skill's directory. Resolve them against the installed skill location, not the user's project root.

## Step 1: Parse Input

The argument can be:
- An arxiv URL: `https://arxiv.org/abs/XXXX.XXXXX` or `https://arxiv.org/pdf/XXXX.XXXXX`
- A DOI: `10.XXXX/...`
- An ACL Anthology URL: `https://aclanthology.org/...`
- An AAAI URL: `https://ojs.aaai.org/...`
- A paper title (will search)

`$ARGUMENTS` names exactly one intended paper. Preserve that identity throughout retrieval.

The goal of this skill is to obtain the intended paper's PDF. Metadata resolution and canonical naming support that goal; they are not the definition of success.

## Step 1.5: Normalize to an Identity-Preserving Input

Before downloading, decide whether the input is already a strong paper identifier:

- **Strong inputs:** arxiv ID/URL, DOI/DOI URL, ACL Anthology URL, S2 paper ID, direct PDF URL, exact paper title
- **Weak inputs:** publisher landing pages, journal homepages, PMC/article pages, society pages, or generic URLs that may require interpretation before they identify one paper cleanly

If the input is weak, first infer the intended paper and continue with the strongest identity-preserving input available. Prefer:

1. DOI
2. ACL Anthology ID/URL
3. arXiv ID/URL
4. S2 paper ID
5. exact paper title
6. the original weak URL only if it is still the clearest remaining identifier

Do not keep retrying a weak URL mechanically when a stronger identifier is already apparent.

## Step 2: Search (title input only)

If the input is a paper title (not a URL or DOI), search for it first:

```bash
uv run scripts/search_papers.py "PAPER TITLE" --source all --max-results 5 --json
```

Review the results. If there's a clear match, extract the strongest available identifier and continue to Step 3. If ambiguous, present the top results to the user and ask which one.

For weak URL input, use the inferred title or metadata from Step 1.5 and perform the same search/normalization before Step 3.

## Step 3: Download

Use the fetch_paper.py script to download the PDF and extract metadata:

```bash
uv run scripts/fetch_paper.py "<identifier>" --papers-dir papers/
```

Where `<identifier>` is the arxiv ID/URL, DOI, ACL URL, or S2 paper ID from the input or search results.

If you had to normalize a weak input first, use the normalized identifier here rather than the original weak URL.

Use `fetch_paper.py` as the first download path, not as the definition of whether retrieval is possible. One metadata-resolution failure does not by itself mean the paper is unretrievable.

The script will:
1. Resolve metadata (title, authors, year, abstract) from arxiv or Semantic Scholar
2. Attempt PDF download via waterfall: direct download → Unpaywall → report fallback needed
3. Only after a real PDF is downloaded, create the canonical paper directory (`Author_Year_ShortTitle`)
4. Only after a real PDF is downloaded, write `metadata.json` alongside `paper.pdf`

Before treating Step 3 as successful, verify that the resolved metadata still matches the intended paper. If not, stop on mismatch.

If `fetch_paper.py` obtains the intended paper's PDF through an allowed path, Step 3 succeeded even if metadata had to be materialized afterward.

## Step 4: Handle Fallback (if needed)

If fetch_paper.py returns `"fallback_needed": true`, the paper couldn't be downloaded via open-access channels. In that case it returns the planned `dirname`/`directory` plus inline `metadata`, but it does **not** create `metadata.json` or the paper directory yet. Fall back to browser automation for sci-hub:

**Try browser automation in this order:**

### Option 1: Any available browser automation (preferred)

If you have browser automation available, use it to:

1. Open `https://sci-hub.st/`
2. Find the input field and enter the URL or DOI
3. Submit the form
4. Inspect the result page for an iframe, embed, or direct PDF link
5. If needed, evaluate JavaScript in the page to extract the PDF URL:
   ```js
   const iframe = document.querySelector('#pdf');
   if (iframe) return iframe.src;
   const embed = document.querySelector('embed[type="application/pdf"]');
   if (embed) return embed.src;
   const links = [...document.querySelectorAll('a')].filter(a => a.href.includes('.pdf'));
   return links.map(a => a.href);
   ```
6. Create the paper directory and download the PDF: `mkdir -p "./papers/<dirname>" && curl -L -o "./papers/<dirname>/paper.pdf" "EXTRACTED_URL" 2>&1`
7. Materialize `metadata.json` only after `paper.pdf` exists:
   `uv run scripts/fetch_paper.py "<identifier>" --papers-dir papers/ --output-dir "<dirname>" --metadata-only`

If browser automation or a direct PDF URL yields the intended paper's PDF, retrieval succeeded. Finalize metadata afterward.

### Option 2: No browser automation

Report the DOI/URL and ask the user to download the PDF manually to the paper directory.

## Step 5: Verify

```bash
file "./papers/<dirname>/paper.pdf"
ls -la "./papers/<dirname>/"
```

Confirm:
- PDF exists and is valid ("PDF document" in file output)
- File size is reasonable (>100KB for a real paper)
- `metadata.json` exists with title, authors, year

The core success condition is that the intended paper's PDF exists at `./papers/<dirname>/paper.pdf`. `metadata.json` should also exist by the end of the step, but earlier metadata-resolution failures do not negate successful retrieval if the correct PDF and final metadata are in place.

## Output

When done, report:
```
Retrieved: papers/<dirname>/paper.pdf
Source: [arxiv/aclanthology/unpaywall/sci-hub]
Size: [file size]
```

## Error Handling

- If fetch_paper.py fails metadata resolution: try the other source (arxiv vs S2)
- If metadata resolution or search yields a different paper than the intended one: stop and report the mismatch
- If all download methods fail: report failure, provide the URL for manual download
- ALWAYS clean up temp files on failure: `rm -f ./papers/temp_*.pdf`

## CRITICAL: File Modified Error Workaround

If Edit/Write fails with "file unexpectedly modified":
1. Read the file again
2. Retry the edit
3. Try path formats: `./relative`, `C:/forward/slashes`, `C:\back\slashes`
4. Prefer your file editing tools over shell text manipulation (cat, sed, echo)
5. If all formats fail, STOP and report

## CRITICAL: Parallel Swarm Awareness

You may be running alongside other agents in parallel.

**FORBIDDEN GIT COMMANDS - NEVER USE THESE:**
- `git stash`, `git restore`, `git checkout`, `git reset`, `git clean`

=== skills/process-leads/SKILL.md ===
---
name: process-leads
description: >-
  Extract all "New Leads" from the paper collection and process them via
  paper-process. Retrieves and reads papers that other papers in your collection
  cite but you don't have yet. Use --all to process everything, or pass a number
  to limit (e.g., "10" for first 10). Add --parallel N to process N leads
  concurrently via subagents (default: sequential).
argument-hint: "[--all | N] [--parallel M]"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI. Subagents are optional but recommended for throughput."
---

# Process Leads: $ARGUMENTS

Find papers cited as "New Leads" across the collection and retrieve+read them.

## Execution Discipline

This skill is a checklist, not an outcome sketch.

- Follow the steps in order.
- Do not add retrieval heuristics, ranking schemes, batching logic, or alternate workflows beyond what this skill specifies.
- If you can invoke the named nested skill, do that. If you cannot, use the fallback helper below and follow its stdout literally.
- If you are blocked on a specific step, stop there and report the exact blocker instead of inventing a workaround.

## Script Paths

The command examples below use `scripts/...` paths that are relative to this skill's directory. Resolve them against the installed skill location, not the user's project root.

## Step 1: Extract All Leads

There are two lead-discovery modes. Use **both** and merge results (deduplicating by author+year).

### Mode A: Notes-based leads (existing behavior)

Extract leads from "New Leads" sections in notes.md files:

```bash
python3 scripts/paper_hash.py --papers-dir papers/ extract-leads
```

### Mode B: Citation-graph leads (new)

If `$ARGUMENTS` contains `--citations` or `--citations-from <identifier>`, also discover leads via Semantic Scholar citation graph:

```bash
uv run scripts/get_citations.py <identifier> --direction references --filter-existing --papers-dir papers/ --json
```

Where `<identifier>` is an arxiv ID or DOI of a paper already in the collection. If `--citations-from` is not specified but `--citations` is, pick the most recently added paper (by directory mtime).

This gets the actual reference list from S2 rather than relying on what paper-reader chose to highlight. Merge these with Mode A leads, deduplicating by author surname + year.

## Step 2: Determine Batch Size and Parallelism

**Count (how many leads to attempt):**
- If `$ARGUMENTS` contains `--all`: no cap — process leads wave by wave until the session ends naturally (context limit, user stops you, etc.). You do NOT need to finish all leads in one session. `--all` just means "don't stop after N, keep going."
- If `$ARGUMENTS` contains a number N (not after `--parallel`): process the first N leads
- If neither: default to 10

**Parallelism (how many at once):**
- If `$ARGUMENTS` contains `--parallel M`: process M leads concurrently via subagents
- If no `--parallel` flag: process sequentially (one at a time)

## Step 2.5: Triage Leads

Before processing, sort leads by retrieval likelihood. Parse ALL leads with paper_hash.py first:

```bash
python3 scripts/paper_hash.py parse "<lead text>"
```

Then classify each lead:

- **Likely available:** Has a title that sounds like a journal/conference paper, year after ~1990
- **Unlikely available:** Books (keywords: "Knowledge in Flux", "The Uses of Argument", "Introduction to..."), technical reports/deliverables, dissertations, pre-1985 papers without DOIs

**Process likely-available leads first.** Defer unlikely leads to the end of the batch. If the batch limit (N) is reached before getting to unlikely leads, that's fine — they go in the "Remaining" section of the report. Don't waste retrieval attempts on leads that will almost certainly fail when there are good leads waiting.

## Step 3: Process Leads

For each lead, build a search query from the parsed author, year, and title components.

Before dispatching a lead, normalize it to one concrete intended paper. Prefer:

1. DOI
2. ACL Anthology ID/URL
3. arXiv ID/URL
4. S2 paper ID
5. exact paper title

Do not dispatch weak landing-page URLs when the title or a stronger identifier is already available. One dispatch must correspond to one intended paper.

### Always Use Subagents

**Every paper-process invocation should run as a subagent when subagent dispatch is available**, even in sequential mode. This protects the foreman's context window from the large volume of page-reading output that paper-process generates. Use the strongest available full-size model for every such worker. Never use a mini/small/flash tier model for workers that will retrieve or read papers. If subagents are unavailable, process leads yourself one at a time and keep external notes so you do not lose state.

### Subagent Prompt Template

Each subagent receives a prompt that tells it to **invoke the paper-process skill**. The foreman does NOT summarize, paraphrase, or re-explain paper-process instructions. The subagent runs the skill itself.

**On platforms with skill invocation (Claude Code):**

Each subagent prompt is exactly:

```
Process this paper using the paper-process skill:

/research-papers:paper-process <IDENTIFIER>

Additional instructions:
- SKIP reconcile (Step 7) and index.md update (Step 8) — the foreman handles these.
- Use the strongest available full-size model for all work. Never use mini/small/flash tiers.
- If retrieval resolves to a different paper than intended, STOP and report mismatch.
- Write a per-paper report to ./reports/paper-<safe-name>.md
```

Where `<IDENTIFIER>` is the normalized identifier (DOI, arXiv URL, exact title, etc.) from the triage step. That is the entire prompt. Do not add anything else.

**On platforms WITHOUT skill invocation (Codex CLI, Gemini CLI):**

Derive this skill's installed directory from the injected `<path>`, then run:

```bash
python "<skill-dir>/../paper-process/scripts/emit_nested_process_fallback.py"
```

Read the FULL stdout. For each lead, create the subagent prompt by taking that output verbatim and replacing `$ARGUMENTS` with the normalized identifier. Append the same additional instructions listed above (skip reconcile/index.md, strongest model, mismatch stop, report path).

**Do NOT:**
- Summarize, abbreviate, or paraphrase the paper-process instructions
- Write your own version of the retrieval/reading/extraction steps
- Add extra steps, heuristics, or "improvements" to the subagent prompt
- Use worktree isolation (paper-process writes to shared state)

### Sequential Mode (default)

Process one lead at a time. Dispatch one subagent for each lead, wait for it to complete, then run reconcile + index.md update yourself (or via another strongest-available full-size subagent if you must delegate), then dispatch the next lead. If subagents are unavailable, process the lead yourself, then reconcile and update index.md before moving on. In the no-nested-skill fallback above, let the paper-process helper complete the full paper workflow and then do only any additional verification you still need before moving on.

### Parallel Mode (--parallel M)

Dispatch up to M leads concurrently using whatever subagent mechanism your platform provides.
Use the strongest available full-size model for every paper-processing worker in the wave. Do not use mini/small/flash tiers for paper retrieval or extraction.

**Batch processing:** Process in waves of M agents. Dispatch a wave, wait for all to complete, run reconcile + update index.md for each new paper from the wave, then dispatch the next wave. The session will naturally end at some point (context limit, user intervention) — that's fine. The report captures progress so the next session can pick up where you left off.

### Handling Failures

Paper-process will fail on some leads. This is expected and fine. Common reasons:
- Books (no PDF available)
- Old papers not digitized
- Paywalled without sci-hub access
- Ambiguous title

When a lead fails retrieval:
1. Log it in the report as "SKIP: [lead] — [reason]"
2. Move to the next lead
3. Do NOT retry or try alternative sources

## Step 4: Report

Write results to `./reports/process-leads-report.md`:

```markdown
# Process Leads Report

**Date:** [date]
**Leads found:** [total]
**Attempted:** [N]
**Parallelism:** [M or "sequential"]
**Succeeded:** [count]
**Failed:** [count]

## Succeeded
| # | Lead | Paper Directory |
|---|------|----------------|
| 1 | [original lead text] | papers/Author_Year_Title/ |

## Failed
| # | Lead | Reason |
|---|------|--------|
| 1 | [original lead text] | [retrieval failed / book / etc] |

## Remaining (not attempted)
[count] leads not attempted. Run again with a higher N or --all.
```

=== skills/process-new-papers/SKILL.md ===
---
name: process-new-papers
description: Process all unprocessed PDF files in the papers/ root directory. If subagents are available, parallelize across papers immediately after listing them; otherwise process sequentially. Any PDF in papers/ root is unprocessed by convention (processed papers live in subdirectories). Invokes paper-reader on each PDF.
argument-hint: ""
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Process New Papers

Find and process all unprocessed PDFs in `papers/` root.

Default execution mode:
- If subagents are available, parallelize across papers.
- Only process sequentially if subagents are unavailable.

This skill is a batch wrapper around `paper-reader`. It does not initialize or mutate propstore source branches.

## Execution Discipline

This skill is a checklist, not an outcome sketch.

- Follow the steps in order.
- Do not add preflight probes, alternate extraction tools, or substitute workflows that are not named here.
- If you can invoke `paper-reader`, do that. If you cannot, use the fallback helper below and follow its stdout literally.
- If you are blocked on a specific step, stop there and report the exact blocker instead of inventing a workaround.
- Do not do extra local investigation before delegation. After listing PDFs, the next action is to start `paper-reader` for each PDF, using subagents if available.
- Treat the parallelization instruction in Step 2 as mandatory when subagents are available, not optional guidance.

## Convention

A PDF in `papers/` root (e.g. `papers/something.pdf`) is **unprocessed**. Once paper-reader processes it, the PDF is `mv`'d into a subdirectory (e.g. `papers/Author_Year_Title/paper.pdf`). So `ls papers/*.pdf` gives you the to-do list.

## Step 1: List Unprocessed PDFs

```bash
ls papers/*.pdf 2>/dev/null
```

If no PDFs found, report "No unprocessed papers found" and stop.

Otherwise, list what was found:
```
Found N unprocessed paper(s):
1. papers/filename1.pdf
2. papers/filename2.pdf
...
```

## Step 2: Process Each Paper

Required control flow:
1. If subagents are available and there is more than one PDF, spawn the subagents now.
2. Assign each subagent one PDF path and use the strongest available full-size model for every worker.
3. In each subagent, invoke `paper-reader` for that PDF, or use the fallback helper below if nested skill invocation is unavailable.
4. Wait for all papers to complete.
5. Only if subagents are unavailable, process the PDFs yourself one by one.

For each PDF found, invoke the **paper-reader** skill:

```
$paper-reader papers/filename.pdf
```

If explicit skill invocation is not available, follow the paper-reader SKILL.md instructions directly for each PDF. The paper-reader skill handles:
- Creating the output directory
- Moving the PDF (not copying)
- Extracting notes, description, abstract, citations
- Cross-referencing with the collection (reconcile)
- Updating papers/index.md
- Cleaning up the root PDF (including if already processed)

IF SUBAGENTS ARE AVAILABLE, PARALLELIZE THE PAPER READING PROCESS IMMEDIATELY AFTER STEP 1.
Do not trade away extraction quality for speed: never use a mini/small/flash tier model for any worker that will run `paper-reader`.

Do not pause to inspect tool availability, existing paper directory formats, or sample notes before starting the workers unless a worker reports a concrete blocker.

If nested skill invocation is unavailable or unreliable on this platform, derive this skill's
installed directory from the injected `<path>`, then ensure the subagent (or you if subagents are unavailable) runs:

```bash
uv run "<skill-dir>/../paper-reader/scripts/emit_nested_reader_fallback.py"
```

Read the FULL stdout and follow it exactly for the current PDF instead of opening
`paper-reader/SKILL.md` piecemeal.

Anti-patterns to avoid:
- Do not replace Step 2 with manual repo exploration.
- Do not inspect all PDFs locally before spawning workers.
- Do not interpret "do the minimum thing" as permission to ignore the explicit parallelization requirement.
- Do not serialize the work when subagents are available.

## Step 3: Summary

After all papers are processed:

```
Processed N paper(s):
1. papers/filename1.pdf -> papers/Author_Year_Title/
2. papers/filename2.pdf -> papers/Author_Year_Title/
...

Remaining unprocessed: [ls papers/*.pdf output, or "none"]
```

## Notes

- **Already-processed PDFs**: If paper-reader detects a paper is already complete, it will delete the duplicate root PDF and move on. This is expected behavior.

- **reconcile needed**: paper-reader already invokes reconcile as part of its flow (Step 7.5) but you may need to do again at the end.

=== skills/reconcile/SKILL.md ===
---
name: reconcile
description: Cross-reference a paper against the collection. Finds which cited papers are already collected, which are new leads, which collection papers cite this one, and reconciles all cross-references bidirectionally. Run on a single paper directory or use --all for the entire collection.
argument-hint: "<papers/Author_Year_Title> or --all"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Reconcile: $ARGUMENTS

Cross-reference a paper (or all papers) against the collection, ensuring every citation link is bidirectional and accurate.

This is a notes-layer skill. It updates paper notes and collection cross-references only; it does not initialize or mutate propstore source branches.

## Step 0: Determine Mode

Parse `$ARGUMENTS`:

- If `--all`: list all paper directories and process each one sequentially (Step 1 onward, looping)
- Otherwise: treat as a single paper directory path

```bash
if [[ "$ARGUMENTS" == "--all" ]]; then
  ls -d papers/*/ | grep -v "papers/pngs" | sort
  # Process each directory through Steps 1-5
else
  paper_dir="$ARGUMENTS"
fi
```

## Step 1: Validate Paper Directory

```bash
ls "$paper_dir"/notes.md "$paper_dir"/citations.md 2>/dev/null
```

**Required files:**
- `notes.md` — must exist (contains the cross-references section we'll update)
- `citations.md` — must exist (contains the reference list we cross-reference from)

If either is missing, report and skip this paper:
```
SKIP: papers/[dirname]/ — missing [notes.md|citations.md], run paper-reader first
```

**Also check:** Does `notes.md` already have a `## Collection Cross-References` section?
- If yes: this paper has been reconciled before. Read the existing section to understand current state, then update it.
- If no: this is a first-time reconciliation. Create the section from scratch.

---

## Step 2: Forward Cross-Referencing (This Paper Cites → Collection)

Check which papers cited by this one are already in the collection.

### 2.1: Extract Citation Keys

Read `citations.md` — focus on both the full Reference List and the Key Citations for Follow-up section. Extract author last names and years for the key citations.

### 2.2: Search Collection Index

For each key citation, grep `papers/index.md` for the author's last name:

```bash
grep -i "AuthorName" ./papers/index.md
```

If found, the matching line contains the directory name. For more detail, read `papers/<dirname>/description.md`.

### 2.3: Write/Update Forward Cross-References

In `notes.md`, write or update the `## Collection Cross-References` section:

```markdown
## Collection Cross-References

### Already in Collection
- [[AuthorA_Year_ShortTitle]] — cited for [reason from citations.md context]

### New Leads (Not Yet in Collection)
- AuthorB (Year) — "Paper title" — relevant for [reason]

### Supersedes or Recontextualizes
- [If this paper extends/corrects/supersedes an existing collection paper, note it here]
- [Only genuine relationships — not every citation]

### Conceptual Links (not citation-based)
- [[PaperC_Year_Title]] — [specific topical connection: what claim/finding/method links these papers]
```

### 2.4: Backward Annotation (Supersedes Only)

If the "Supersedes or Recontextualizes" section is non-empty, append a see-also note to each affected paper's notes.md:

```bash
echo "" >> ./papers/AffectedPaper_Dir/notes.md
echo "---" >> ./papers/AffectedPaper_Dir/notes.md
echo "" >> ./papers/AffectedPaper_Dir/notes.md
echo "**See also:** [[NewPaper_Dir]] - [relationship description]" >> ./papers/AffectedPaper_Dir/notes.md
```

**Check first** whether a see-also note already exists (to avoid duplicates):
```bash
grep -c "NewPaper_Dir" ./papers/AffectedPaper_Dir/notes.md
```

---

## Step 3: Reverse Citation Search (Collection Cites → This Paper)

Find papers in the collection that reference this paper.

### 3.1: Extract Search Keys

From the paper's `notes.md`, extract the first author's last name and year. Build a grep pattern:

```bash
# Search all collection markdown files for references to this paper
# Exclude the paper's own directory to avoid self-matches
grep -rl "AuthorLastName.*Year" ./papers/ --include="*.md" | grep -v "papers/AuthorLastName_Year_ShortTitle/"
```

Also try the directory name pattern:
```bash
grep -rl "AuthorLastName_Year" ./papers/ --include="*.md" | grep -v "papers/AuthorLastName_Year_ShortTitle/"
```

### 3.2: Add "Cited By" Section

If any collection papers cite this one, add or update a "Cited By" subsection in the Collection Cross-References:

```markdown
### Cited By (in Collection)
- [[CitingPaper_Year_ShortTitle]] — cites this for [aspect, determined in Step 4]
```

If no papers cite this one, either omit the section or write:
```markdown
### Cited By (in Collection)
- (none found)
```

---

## Step 4: Conceptual Links (Topic-Based, Not Citation-Based)

Steps 2–3 find explicit citation links. This step finds **conceptual connections**: collection papers that address the same problems, whose findings interact with this paper's claims, or whose methods complement or contradict this paper — regardless of whether any citation relationship exists.

This is what makes the collection a knowledge graph, not just a citation graph. **This step is not optional.** Citation-based cross-referencing alone misses the most valuable connections: papers from different research traditions that converge on the same empirical observation, or later papers that provide mechanisms for earlier observations.

### 4.1: Identify Key Claims and Topics

Read this paper's notes.md and extract the 3–6 most important claims, methods, or findings. These are the search axes.

**What to extract — be specific about the phenomenon, not just the topic:**
- A specific empirical observation (e.g., "formant transitions hold at 65ms while steady states stretch 1.5x")
- A model or framework (e.g., "multi-stream parallel representation with synchronized tiers")
- A mechanism or explanation (e.g., "aspiration overlays the CV transition as an independent stream")
- A critique of another approach (e.g., "linear phoneme models conflate phonological and phonetic units")
- An open problem the paper identifies (e.g., "minimum/maximum duration constraints not specified")

### 4.2: Search Collection for Topic Matches

For each claim/topic, think about what kinds of papers would connect:

**Same phenomenon, different framework:**
- Does another tradition (articulatory phonology, acoustic phonetics, perceptual studies) observe the same thing this paper describes? Search for the phenomenon's acoustic/articulatory/perceptual terms.
- Example: "stable transition duration" → search for "stiffness", "gesture duration", "transition.*ms", "formant transition"

**Mechanism for observation (or observation for mechanism):**
- Does this paper observe something that another paper explains, or vice versa?
- Example: paper observes "only steady states lengthen" → search for "boundary lengthening", "phrase-final", "π-gesture", "prosodic.*slowing"

**Data that grounds or challenges claims:**
- Does another paper provide the empirical measurements this paper's model requires?
- Does another paper's data contradict this paper's predictions?

**Cross-level connections:**
- Articulatory ↔ Acoustic ↔ Perceptual papers often address the same phenomenon at different levels of description

Use targeted grep searches across `papers/*/notes.md`:
```bash
# Search for papers discussing the same phenomenon
grep -rl "relevant_term" ./papers/ --include="notes.md" | grep -v "papers/ThisPaper/"
```

Read matching sections (not full files) to assess connection strength.

### 4.3: Classify Connection Strength

For each match, classify as:
- **Strong** — directly addresses the same problem, provides data this paper uses, contradicts/confirms a key finding, or provides a mechanism for this paper's observations (or vice versa). Different formalisms converging on the same empirical fact is always Strong.
- **Moderate** — related methodology or overlapping problem space, but not directly interacting
- **Weak** — tangential overlap; omit from cross-references

Only surface **Strong** and **Moderate** connections. Weak connections create noise.

### 4.4: Write Conceptual Links Section

Add a `### Conceptual Links (not citation-based)` subsection to the Collection Cross-References:

```markdown
### Conceptual Links (not citation-based)
- [[PaperA_Year_Title]] — [specific connection: what claim/finding/method connects these papers and how they relate — convergence, tension, mechanism↔observation, etc.]
- [[PaperB_Year_Title]] — [specific connection]
```

Each entry must state the **specific relationship**, not just "related to duration modeling." Good: "Hertz's 'stable transition phenomenon' (CV transitions hold at ~65ms while steady states stretch) is exactly what AP predicts for a high-stiffness gesture — different formalisms, same empirical convergence." Bad: "Also about formant transitions."

Group entries by theme when there are 3+ connections (use bold subheadings like `**Duration modeling:**`).

### 4.5: Bidirectional Annotation

For **Strong** connections, check if the connected paper's notes.md already mentions this paper:
- If not, add a reciprocal entry in that paper's `### Conceptual Links (not citation-based)` section (create the subsection if needed)
- Check for duplicates before writing

For **Moderate** connections, only annotate this paper (not the connected paper) — the connected paper's own reconciliation pass will pick it up if the connection is genuinely bidirectional.

---

## Step 5: Reconcile Citing Papers

For each paper found in Step 3, **read its notes.md** (specifically the Collection Cross-References, Related Work, and Open Questions sections). Check for and fix:

### 5.1: Leads Listing This Paper

Leads can appear in **two places** depending on whether the citing paper has been reconciled before:

1. **`### New Leads (Not Yet in Collection)`** — inside a `## Collection Cross-References` section (reconciled papers)
2. **`## Related Work Worth Reading`** — a flat list at the end of notes.md (unreconciled papers, the paper-reader default)

Search both sections for an entry matching this paper (by author name and year).

**If found in `### New Leads (Not Yet in Collection)`:**
- **Move** the entry out of "New Leads"
- **Add** it to `### Now in Collection (previously listed as leads)` (create subsection if needed)

**If found in `## Related Work Worth Reading`:**
- **Do NOT delete** the entry (that section is the paper-reader's historical output)
- **Annotate inline** by appending `→ NOW IN COLLECTION: [[Author_Year_ShortTitle]]` to the entry
- **Add** the entry to `### Now in Collection (previously listed as leads)` in the `## Collection Cross-References` section (create section and subsection if needed)

In both cases, write the "Now in Collection" entry with:
  - Correct description of what this paper actually contributes
  - Key finding summary
  - Any tensions or confirmations between the two papers' findings

Example:
```markdown
### Now in Collection (previously listed as leads)
- [[Groth_2010_AnatomyNanopublication]] — Defines nanopublication model (concept→triple→statement→annotation→nanopublication) with RDF Named Graph serialization. Structurally analogous to the micropublication model but focused on Semantic Web interoperability rather than argumentation structure.
```

### 5.2: Inaccurate Descriptions

If the citing paper describes this paper inaccurately (wrong method, wrong finding, wrong scope):
- **Edit** the description inline to be correct
- Common errors: confusing which variables were manipulated, attributing findings from a different paper by the same author group

### 5.3: Open Questions Answered

If the citing paper has open questions (`## Open Questions`) that this paper addresses:
- **Annotate** the question: append `[Addressed by Author_Year_ShortTitle — finding summary]`
- Do NOT check the box — that's for the user to decide

### 5.4: Interesting Tensions

If the new paper's findings conflict with or nuance the citing paper's conclusions:
- **Document in the citing paper's notes** (in the cross-references section or as an inline note)
- **Document in this paper's notes** (in the cross-references section)
- Be specific: what differs, why (different methodology? different controls? different population?)

---

## Step 6: Report

Output a summary:

```
Reconciled: papers/[dirname]/
  Forward: N already in collection, M new leads, K supersedes
  Reverse: J collection papers cite this one
  Conceptual: S topic-based connections surfaced (T strong, U moderate)
  Updated:
    - papers/CitingPaper1/ — moved lead to "Now in Collection", corrected description
    - papers/CitingPaper2/ — added to "Already in Collection"
    - papers/AffectedPaper/ — added see-also backward annotation
    - papers/ConnectedPaper/ — added conceptual link (bidirectional)
  Tensions found:
    - [brief description of any finding conflicts, or "none"]
```

For `--all` mode, output a final summary after all papers are processed:

```
Reconciliation complete: X papers processed
  - Y papers had citing papers in collection
  - Z leads marked as fulfilled
  - S conceptual links surfaced
  - W tensions documented
  - V papers skipped (missing notes.md or citations.md)
```

---

## The Reconciliation Principle

After reconciliation, every cross-reference in the collection should be **bidirectional and accurate**:

1. If Paper A cites Paper B, and both are in the collection:
   - A's notes mention B in "Already in Collection" (with correct description)
   - B's notes mention A in "Cited By (in Collection)"

2. If Paper A was listed as a "New Lead" in Paper B, and A is now in the collection:
   - The lead entry is moved to "Now in Collection" with accurate summary
   - Any inaccurate description from when the lead was first noted is corrected

3. If Paper A supersedes/extends Paper B:
   - A's notes say so in "Supersedes or Recontextualizes"
   - B's notes have a "See also" annotation pointing to A

4. If Papers A and B have conflicting findings:
   - Both papers' notes document the tension with specifics

5. If Papers A and B address the same problem or their findings substantively interact (even without citation):
   - At least one paper's notes mention the other in "Conceptual Links (not citation-based)"
   - Strong connections are annotated bidirectionally; moderate connections at minimum on the paper being reconciled

---

## Running on All Papers

When invoked with `--all`, process papers in alphabetical order. For each paper:

1. Run Steps 1-6
2. **Do not re-read papers that were already updated as citing papers** — their own turn will come in the alphabetical sweep
3. Be idempotent: running `--all` twice should produce the same result (no duplicate annotations)

### Idempotency Checks

Before every write operation, check if the content already exists:
- Before adding "Cited By" entry: `grep -c "PaperDirName" notes.md`
- Before adding "See also": `grep -c "PaperDirName" affected_notes.md`
- Before moving a lead: check if "Now in Collection" subsection already lists it

---

## Do NOT:
- Create or modify `papers/index.md` entries (that's paper-reader's job)
- Delete or overwrite existing notes content (only append/update cross-reference sections)
- Modify the paper's core notes sections (Summary, Parameters, Equations, etc.)
- Output full notes content to conversation (just the reconciliation summary)

=== skills/reconcile-vocabulary/SKILL.md ===
---
name: reconcile-vocabulary
description: Reconcile paper-local concept inventories across a paper collection. Identifies collision groups, proposes shared canonical names, and optionally rewrites per-paper concepts.yaml files.
argument-hint: "<papers-directory> [--fix] [--vocabulary <path>]"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Reconcile Vocabulary: $ARGUMENTS

Reconcile paper-local concept inventories across a paper collection.

## Step 1: Parse Arguments

```bash
papers_dir=""
fix_mode=false
vocab_path=""

for arg in $ARGUMENTS; do
  case "$arg" in
    --fix) fix_mode=true ;;
    --vocabulary) next_is_vocab=true ;;
    *)
      if [[ "$next_is_vocab" == "true" ]]; then
        vocab_path="$arg"
        next_is_vocab=false
      else
        papers_dir="$arg"
      fi
      ;;
  esac
done
```

## Step 2: Collect All Concept Names

Read every `concepts.yaml` file under `$papers_dir`:
```bash
find "$papers_dir" -name "concepts.yaml" -type f
```

For each file, extract all concept inventory entries:
- `local_name`
- `proposed_name`
- `definition`
- `form`
- optional observed units or notes

Build a frequency table: concept_name → {count, papers[], definitions[], forms[]}.

## Step 3: Load Vocabulary (if provided)

If `--vocabulary` was given, read the YAML file. Its `concepts` mapping provides known canonical names and their aliases.

## Step 4: Identify Collision Groups

Group concept inventory entries that may refer to the same underlying concept:

1. **Exact vocabulary matches**: If two names both appear in the vocabulary file mapping to the same canonical name, they're the same concept.
2. **String similarity**: Use token overlap (split on underscore, compare token sets). Threshold: 0.6 similarity.
3. **Abbreviation expansion**: Use the vocabulary's `abbreviations` section to expand short forms before comparison.
4. **Definition overlap**: If definitions clearly describe the same concept, group them even when local names differ.
5. **Form mismatch**: If names are similar but forms differ (`ratio` vs `structural`), keep them in the same report but flag them as contested rather than auto-merged.

For each collision group, select the canonical name:
- If the vocabulary specifies one, use it
- Otherwise, pick the most descriptive (longest) name
- List all variants as aliases
- Record per-paper source names so later alignment can map back to individual `concepts.yaml` files

## Step 5: Report

Write a report with:
- Total unique concept names found
- Number of collision groups
- For each collision group: canonical name, all variants, which papers use which variant
- Contested groups where definitions or forms disagree
- Suggested vocabulary additions (new concepts not in the vocabulary file)

## Step 6: Fix Mode (--fix)

If `--fix` was passed:
1. For each collision group that is not contested, rewrite the affected `concepts.yaml` files so `proposed_name` matches the selected canonical name
2. Preserve `local_name`, definitions, forms, and all non-name fields unchanged
3. Do NOT rewrite `claims.yaml` here; claim rewriting happens later when papers are re-extracted or re-ingested against the updated concept inventory
4. Report which `concepts.yaml` files were modified

## Output

```
Vocabulary reconciliation complete.
  Papers scanned: N
  Unique concept names: N
  Collision groups found: N
  Contested groups: N
  - [canonical_name]: [variant1] (3 papers), [variant2] (1 paper)
  ...

Report written to: reports/vocabulary-reconciliation-report.md
```

=== skills/register-concepts/SKILL.md ===
---
name: register-concepts
description: Register concepts needed by a paper into a propstore source branch. Runs propose_concepts.py to extract concept inventory from claims, then enriches definitions via notes.md, and calls pks source add-concepts.
argument-hint: "<papers/Author_Year_Title>"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Register Concepts: $ARGUMENTS

Register all concepts needed by a paper into its propstore source branch. This must run after extract-claims (needs claims.yaml) and after `pks source init` has created the source branch.

## Step 0: Validate

```bash
paper_dir="$ARGUMENTS"
ls "$paper_dir"/notes.md 2>/dev/null || echo "MISSING: notes.md"
ls "$paper_dir"/claims.yaml 2>/dev/null || echo "MISSING: claims.yaml"
```

If `notes.md` is missing → STOP, run paper-reader first.
If `claims.yaml` is missing → STOP, run extract-claims first.

## Step 1: Check Propstore State

```bash
ls knowledge/.git 2>/dev/null
pks source --help 2>/dev/null | head -20
```

If no `knowledge/` directory exists → STOP. Report: "No propstore found. Run `pks init` first."

## Step 2: Mechanical Concept Extraction

Run the concept proposer to extract all concept names from this paper's claims.yaml:

```bash
uv run scripts/propose_concepts.py pks-batch "$paper_dir" \
  --registry-dir knowledge/concepts \
  --output "$paper_dir/concepts.yaml"
```

Read the output `concepts.yaml`. It will have entries like:
```yaml
concepts:
  - local_name: "hazard_ratio"
    proposed_name: "hazard_ratio"
    definition: "Auto-proposed from 5 claim(s)."
    form: "structural"
```

## Step 3: Enrich Definitions

The auto-generated definitions are placeholders. For each concept in `concepts.yaml`:

1. Read the paper's `notes.md` to find how this concept is described
2. Replace the placeholder definition with a 1-2 sentence definition that:
   - Distinguishes this concept from near-neighbors
   - Would make sense to someone unfamiliar with this specific paper
   - Is specific enough to match against similar concepts in other papers

Good: "Ratio of hazard rates between treatment and control arms, measuring the relative risk of an event occurring in the intervention group."
Bad: "A ratio."

3. Verify the `form` is correct:
   - `ratio` for dimensionless ratios (hazard ratio, odds ratio, rate ratio, relative risk)
   - `rate` for event rates (events per person-year, incidence rate)
   - `score` for evaluation metrics, p-values, absolute risk differences
   - `count` for discrete quantities (person-years, sample size)
   - `structural` for methods, architectures, abstract concepts
   - `category` for condition variables with enumerated values

4. Write the enriched `concepts.yaml` back to disk.

## Step 4: Ingest into Propstore

```bash
source_name=$(basename "$paper_dir")
pks source add-concepts "$source_name" --batch "$paper_dir/concepts.yaml"
```

If this fails with "unknown source branch", the source branch hasn't been initialized. Run:
```bash
# See paper-process skill for full init sequence
pks source init "$source_name" --kind academic_paper --origin-type doi --origin-value "<doi>"
```

## Step 5: Report Alignment

After add-concepts, check which concepts exact-matched existing canonical names vs which remain newly proposed:

```
Concepts registered for: papers/[dirname]
  Exact-match links: N (list names)
  Newly proposed: N (list names)
  Total in concepts.yaml: N
```

Newly proposed concepts will need alignment decisions after all papers are finalized.

=== skills/research/SKILL.md ===
---
name: research
description: Research a topic using web search and create structured findings. Use when you need to investigate approaches, find papers, compare implementations, or gather knowledge on a topic. Creates structured notes in reports/ directory.
argument-hint: "[topic]"
context: fork
agent: general-purpose
compatibility: "Claude Code, Codex CLI, and Gemini CLI. Requires web search access."
---

# Research: $ARGUMENTS

Research a topic and create comprehensive implementation-focused findings.

## Objective

Conduct web-based research on **$ARGUMENTS** to answer:
1. What approaches/systems exist?
2. What papers describe them?
3. What are the tradeoffs (complexity vs quality)?
4. What implementations exist?
5. What's the recommended approach for this project?

## Research Methods

Search the web to find:
- Academic papers and key authors
- Documentation and specifications
- Open-source implementations
- Comparison studies

Fetch and read these pages to:
- Read paper abstracts/summaries
- Extract key information from documentation
- Check implementation details

## Output Format

Write findings to `./reports/research-$ARGUMENTS.md`:

```markdown
# Research: $ARGUMENTS

## Summary
[One paragraph overview of findings]

## Approaches Found

### [Approach 1 Name]
**Source:** [URL]
**Description:** [What it is]
**Pros:** [Advantages]
**Cons:** [Disadvantages]
**Complexity:** [Low/Medium/High]

[Repeat for each major approach]

## Key Papers
- [Author (Year)](URL) - [What it contributes]
- [Author (Year)](URL) - [What it contributes]

## Existing Implementations
- **[Name]** ([URL]): [Description, language, license]

## Complexity vs Quality Tradeoffs
[Analysis of what level of complexity gets what level of quality]

## Recommendations
[Specific recommendations for this project's research area]

## Estimated Implementation Effort
- **Minimal approach:** [What you get]
- **Full approach:** [What you get]

## Open Questions
- [ ] [Unresolved question]
- [ ] [Area needing more investigation]

## References
- [Full citation with URL]
```

---

## CRITICAL: File Modified Error Workaround

If Edit/Write fails with "file unexpectedly modified":
1. Read the file again
2. Retry the Edit
3. Try path formats: `./relative`, `C:/forward/slashes`, `C:\back\slashes`
4. Prefer your file editing tools over shell text manipulation (cat, sed, echo)
5. If all formats fail, STOP and report

## CRITICAL: Parallel Swarm Awareness

You may be running alongside other agents. NEVER use git restore/checkout/reset/clean.

---

## Completion

When done, reply ONLY:
```
Done - see reports/research-$ARGUMENTS.md
```

Do NOT:
- Output findings to conversation
- Read project source files (unless topic requires it)
- Modify any other files

=== skills/tag-papers/SKILL.md ===
---
name: tag-papers
description: Add tags to papers that are missing them. Reads notes.md and description.md to pick 2-5 tags, preferring tags already in use. Run on a single paper directory or use --all for the entire collection.
argument-hint: "<papers/Author_Year_Title> or --all"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Tag Papers: $ARGUMENTS

Add tags to papers in the collection that don't have them yet.

## Step 0: Determine Mode

Parse `$ARGUMENTS`:

- If `--all`: list all paper directories and process each one
- Otherwise: treat as a single paper directory path

```bash
if [[ "$ARGUMENTS" == "--all" ]]; then
  ls -d papers/*/ | sort
else
  paper_dir="$ARGUMENTS"
fi
```

## Step 1: Gather Existing Tags

Read `papers/index.md` and extract all tags currently in use:

```bash
cat ./papers/index.md
```

Parse the `(tag1, tag2)` suffixes to build a list of existing tags and their frequencies. These are your preferred vocabulary — reuse existing tags when they fit rather than inventing synonyms.

Also read `papers/tags.yaml` if it exists:

```bash
cat ./papers/tags.yaml
```

This file is the **canonical tag vocabulary**. It lists all approved tags and their aliases. If it exists, you MUST use tags from this file. Do not invent new tags when an existing tag or its alias covers the topic.

If `tags.yaml` does not exist, fall back to the existing behavior of preferring tags already used in `index.md`.

## Step 2: Check Each Paper

For each paper directory, check if it already has tags.

Read `description.md` and check:
- Does it have YAML frontmatter with a `tags:` field? → **skip**
- Does it have a legacy `Tags:` line? → **skip**
- Does `description.md` not exist? → **skip** (run paper-reader first)
- Does `notes.md` not exist? → **skip** (run paper-reader first)

## Step 3: Read and Tag

Read the paper's `notes.md` and `description.md` to understand what it's about.

Pick 2-5 tags following these guidelines:

- **Lowercase, hyphenated**: `voice-quality`, not `Voice Quality`
- **MUST use tags from tags.yaml**: if a canonical tag fits, use it. If the paper's topic matches an alias listed in tags.yaml, use the canonical form instead.
- **Proposing new tags**: if no existing tag fits, you may propose a new one. List it in Step 6 as a proposed addition to tags.yaml. Use lowercase-hyphenated format.
- **Mix specificity**: one broad tag (`acoustics`, `perception`, `synthesis`) plus one or two narrow ones (`formant-transitions`, `lf-model`)
- **Tags describe the paper's topic**, not its method or venue
- **Don't over-tag**: 3 tags is usually right

## Step 4: Write Tags

Add YAML frontmatter with tags to `description.md`. Read the file first, then:

- **If no frontmatter exists**: prepend `---\ntags: [tag1, tag2, tag3]\n---\n` before the existing content
- **If frontmatter exists but no tags field**: add `tags: [tag1, tag2, tag3]` inside the existing frontmatter
- **If a legacy `Tags:` line exists at the end**: remove it and add frontmatter instead

Use your editing tools to modify the file cleanly.

Example result:
```markdown
---
tags: [acoustics, glottal-source, voice-quality]
---
This paper presents the LF model for parameterizing glottal flow...
```

## Step 5: Update index.md

Update the paper's line in `index.md` to include its new tags. Find the line starting with `- PaperDirName` and update it to `- PaperDirName  (tag1, tag2, tag3)`.

If the paper isn't in `index.md` yet, append it.

## Step 6: Report

Output a summary:

```
Tagged: N papers
Skipped: M papers (already tagged or missing notes)

New tags introduced:
  - new-tag-1 (used by: Paper1, Paper2)
  - new-tag-2 (used by: Paper3)

Existing tags reused:
  - acoustics (now N total papers)

Untagged papers remaining:
  - Paper_Without_Notes (missing notes.md)
```

For `--all` mode, also output the full tag frequency list:

```
Tag summary:
  acoustics: 5 papers
  voice-quality: 3 papers
  ...
```

If you introduced any tags NOT in tags.yaml, list them:

```
Proposed new tags (add to tags.yaml):
  - new-tag-name: "Brief description of what this tag covers"
```

After tagging, remind the user to run `generate-paper-index.py` to rebuild the `tagged-papers/` symlinks.

---

## Do NOT:

- Modify notes.md or any file other than description.md and index.md
- Re-read the PDF (notes.md has everything you need)
- Delete or rewrite existing description text (only add/modify frontmatter)
- Invent tags when an existing tag fits

