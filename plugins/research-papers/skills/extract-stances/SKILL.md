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
pks source add-stance "$source_name" --batch "$paper_dir/stances.yaml" \
  --reader "<your model name>" --method "extract-stances"
```

If this fails with claim reference errors, the referenced claim IDs don't match the source branch's claims.yaml. Fix the references and retry.

## Step 7: Provenance

Provenance is recorded automatically via `--reader` and `--method` flags on the `pks source add-stance` command in Step 6. No separate stamp step is needed.

If you need to override provenance after the fact, `pks source stamp-provenance` still exists but is deprecated.

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
