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
