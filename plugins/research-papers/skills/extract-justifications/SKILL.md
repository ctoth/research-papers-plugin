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

The attack type is inferred from which `attack_target` fields are populated — there is no `kind` discriminator field:
- `target_claim` only → rebuts (attacks the conclusion directly)
- `target_claim` + `target_premise_index` → undermines (attacks a specific premise)
- `target_justification_id` → undercuts (attacks the inference/methodology)

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
    # Undercut: attacks the inference rule of a justification
    attack_target:
      target_justification_id: just1
    provenance:
      page: 22
      section: Discussion
      quote_fragment: "This approach fails to account for..."

  - id: just3
    conclusion: claim21
    premises:
      - claim6
    rule_kind: empirical_support
    # Rebut: attacks the conclusion claim directly
    attack_target:
      target_claim: claim9
    provenance:
      page: 25
      section: Discussion
      quote_fragment: "Contrary to the authors' conclusion..."
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
- `attack_target` — Only present when the justification represents a critique. Attack type is inferred from which fields are populated.
  - `target_claim` — The claim ID being attacked (for rebuts and undermines).
  - `target_justification_id` — The justification ID being attacked (for undercuts).
  - `target_premise_index` — Which premise in the target is being attacked (for undermines). Integer index into the target's premises list.

### Rules

1. **All claim IDs must exist in this paper's claims.yaml.** Do not reference claims from other papers — that is what stances are for.
2. **One inferential step per justification.** If a chain of reasoning has three steps (A+B->C, C+D->E, E->F), create three justifications, not one.
3. **Premises must be a genuine set.** Do not list the same claim twice. Do not include the conclusion as a premise.
4. **Do not fabricate reasoning the paper does not make.** If the paper presents a result without connecting it to premises, it is an isolated claim — do not invent a justification.
5. **Quote fragments must come from the paper.** Do not paraphrase or synthesize — use actual text.
6. **Attack justifications need both attack_target and standard fields.** A critique still has premises (the evidence for the attack) and a conclusion (what the attacker concludes). The `attack_target` must use the correct field combination: `target_claim` for rebuts, `target_claim` + `target_premise_index` for undermines, or `target_justification_id` for undercuts.

## Step 3: Write

Write to `<paper_dir>/justifications.yaml`.

## Step 4: Validate

Check:
- Every `conclusion` and every entry in `premises` references a valid claim ID in `<paper_dir>/claims.yaml`
- No justification has its conclusion in its own premises list
- Every `rule_kind` is one of the seven valid values
- Every `attack_target` (if present) has a valid field combination: `target_claim` only (rebut), `target_claim` + `target_premise_index` (undermine), or `target_justification_id` (undercut)
- Every `attack_target.target_claim` (if present) references a valid claim ID
- Every `attack_target.target_justification_id` (if present) references a valid justification ID
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
pks source stamp-provenance "$source_name" \
  --file "$paper_dir/justifications.yaml" \
  --agent "<your model name>" --skill extract-justifications
```

This records which model extracted justifications, when, and which plugin version was used.

## Quality Checklist

- [ ] Every justification has unique sequential ID
- [ ] Every conclusion and premise references a valid claim ID
- [ ] Rule kinds are semantically appropriate (not just syntactically valid)
- [ ] Attack targets use correct field combinations (rebut/undermine/undercut)
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
