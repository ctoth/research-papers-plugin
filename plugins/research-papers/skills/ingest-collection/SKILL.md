---
name: ingest-collection
description: Orchestrate a full knowledge store rebuild from a paper collection. Four-phase pipeline: per-paper finalize, concept alignment, first promote, then cross-paper stances with re-promote. Builds sidecar at the end.
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

---

## PHASE 1: Per-Paper Pipeline

Each paper gets its own isolated source branch. There are no cross-paper dependencies in this phase, so **if subagents are available, dispatch one subagent per paper and run them all in parallel.** Each subagent runs steps 2a–2f independently for its paper. If subagents are not available, run the steps sequentially for each paper.

**Do not proceed to Phase 2 until every paper has either finalized successfully or reported a blocker.**

For each paper directory:

### 2a: Initialize source branch

```bash
source_name=$(basename "$paper_dir")
# Read metadata.json for origin type and value
pks source init "$source_name" --kind academic_paper \
  --origin-type <doi|arxiv|url|file> --origin-value "<value>" \
  --content-file "$paper_dir/paper.pdf"
pks source write-notes "$source_name" --file "$paper_dir/notes.md"
pks source write-metadata "$source_name" --file "$paper_dir/metadata.json"
```

### 2b: Extract claims (file only)

```
/research-papers:extract-claims <paper_dir>
```

This writes `claims.yaml`. The skill may attempt `pks source add-claim` — that will fail because concepts aren't registered yet. This is expected. The important output is `claims.yaml` on disk.

### 2c: Register concepts

```
/research-papers:register-concepts <paper_dir>
```

This runs `propose_concepts.py pks-batch` to extract concept names from claims.yaml, then the agent enriches definitions and assigns forms. Output: `<paper_dir>/concepts.yaml`. The skill ingests via `pks source add-concepts`.

### 2d: Ingest claims

Now that concepts are on the source branch, ingest claims:

```bash
source_name=$(basename "$paper_dir")
pks source add-claim "$source_name" --batch "$paper_dir/claims.yaml"
```

**If add-claim fails with "unknown concept reference(s)":** the error lists the specific missing names. Add those concepts to concepts.yaml, re-run `pks source add-concepts`, retry add-claim. Iterate until add-claim succeeds.

### 2e: Extract and ingest justifications

```
/research-papers:extract-justifications <paper_dir>
```

The skill writes `justifications.yaml` and ingests via `pks source add-justification`.

### 2f: Finalize (without stances)

```bash
pks source finalize "$source_name"
```

Check the finalize report. Status must be "ready" before proceeding. If "blocked", fix the reported errors and re-finalize.

**Do NOT add stances yet.** Cross-paper stances require target claims to be on master, which happens after Phase 3.

---

## PHASE 2: Concept Alignment (Sequential)

After all papers are finalized, align concepts across source branches. This puts canonical concepts on master, which is required before source branch promotion.

### 3a: Align all source branches

```bash
# Build the list of source branches
branches=""
for d in "$papers_dir"/*/; do
  branches="$branches source/$(basename $d)"
done

pks concept align $branches
```

This produces alignment artifacts grouping concepts by name overlap.

### 3b: Review alignment clusters

```bash
# List alignment artifacts
pks concept show align:<cluster_id>
```

For each cluster, the agent reviews:
- **Exact matches** (same name, same form, similar definition across papers): accept the first, reject duplicates
- **Near-misses** (gi_bleeding vs gastrointestinal_bleeding): decide which name to canonicalize
- **Form conflicts** (same concept, different form assignments): resolve to the correct form

### 3c: Decide and promote each cluster

```bash
pks concept decide <cluster_id> --accept <best_id> --reject <other_ids>
pks concept promote-alignment <cluster_id>
```

Repeat for each cluster. After all clusters are promoted, canonical concepts are on master with artifact_ids.

Report:
- Auto-linked (exact match): N concepts
- Newly proposed: N concepts
- Alignment clusters reviewed: N
- Concepts promoted to master: N

---

## PHASE 3: First Promote (Parallel)

With concepts on master, source branches can now be promoted. This puts claims on master with logical IDs, which enables cross-paper stance references.

```bash
for d in "$papers_dir"/*/; do
  source_name=$(basename "$d")
  pks source promote "$source_name" 2>&1 || echo "FAILED: $source_name"
done
```

If promote fails with "unresolved concept mappings": the listed concept handles don't have corresponding master concepts. Check concept alignment — some clusters may not have been decided/promoted. Fix and retry.

After this phase, all claims are on master. Cross-paper claim references (e.g., `Bowman_2018_EffectsAspirinPrimaryPrevention:claim11`) resolve via master logical IDs.

---

## PHASE 4: Cross-Paper Stances + Re-Promote

Now extract stances that reference claims across papers, re-finalize to validate the cross-references, and re-promote to include stances on master.

### 5a: Build citation graph and identify argumentative clusters

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

Papers may appear in multiple clusters.

### 5b: Extract stances per cluster

**If subagents are available, dispatch one subagent per argumentative cluster in parallel.** Each subagent extracts stances for the papers in its cluster. If subagents are not available, run sequentially per cluster.

For each cluster:

```
/research-papers:extract-stances <paper_dir> --cluster paper1,paper2,paper3
```

The agent reads all claims within its cluster and extracts stances for each paper. Stances go into standalone `stances.yaml` files.

**Do not proceed to 5c until all stance extraction is complete.**

### 5c: Ingest stances, re-finalize, re-promote

For each paper that has stances:
```bash
source_name=$(basename "$d")

# Ingest stances to source branch
pks source add-stance "$source_name" --batch "$d/stances.yaml"

# Re-finalize (validates stance targets against master)
pks source finalize "$source_name"

# Re-promote (overwrites master with stances included)
pks source promote "$source_name"
```

**If finalize reports stance errors:** the listed targets don't resolve. Check that the target paper was promoted in Phase 3 and that the claim ID matches. The target format is `PaperDirName:claimID` (e.g., `Bowman_2018_EffectsAspirinPrimaryPrevention:claim11`).

**Re-finalize is safe:** it overwrites the Phase 1 finalize report on the source branch.

**Re-promote is safe:** it overwrites the Phase 3 master files and adds stance files.

---

## PHASE 5: Build and Verify

### 6a: Build sidecar

```bash
pks build
```

### 6b: Verify

```bash
pks world status
pks query "SELECT COUNT(*) FROM claims"
pks query "SELECT COUNT(*) FROM concepts"
pks query "SELECT conflict_type, COUNT(*) FROM conflicts GROUP BY conflict_type"
```

### 6c: Test semantic queries

```bash
# What do we know about aspirin?
pks world query aspirin

# Explain the argumentation around a specific claim
pks world explain <claim_artifact_id>

# What conflicts exist?
pks world status
```

## Step 7: Report

Write to `reports/ingest-collection-report.md`:

- Papers processed: N
- Claims total: N (breakdown by type)
- Concepts: N registered, N aligned, N promoted
- Justifications: N total
- Stances: N total (breakdown by type)
- Conflicts detected: N (breakdown by type: COMPATIBLE, PHI_NODE, CONFLICT, OVERLAP, PARAM_CONFLICT)
- Argumentative clusters identified: N (list them)
- Source branches: N finalized, N promoted
- Any errors or blockers encountered

## Error Recovery

- **Finalize blocked (Phase 1):** Fix the specific errors in the finalize report, then re-finalize. Common cause: add-claim failed silently (no claims on source branch).
- **Promote fails — unresolved concepts (Phase 3):** A concept handle in claims doesn't map to a master concept. Run `pks concept align` with the relevant source branches, decide, promote-alignment. Retry promote.
- **Finalize blocked — stance errors (Phase 4):** Target claim not on master. Check that the target paper was promoted in Phase 3. Check target format is `PaperDirName:claimID`.
- **Build fails:** Run `pks validate` for structural diagnostics. Common cause: concept form mismatch (claim references concept with incompatible form for its conditions).
- **add-claim fails — unknown concepts:** Iterate to fixed-point (see Phase 1, Step 2d).
