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

## Step 5: Extract Claims (File Only)

### Primary: Skill Invocation

```
/research-papers:extract-claims <paper-directory-path>
```

The skill writes `claims.yaml` and may attempt `pks source add-claim`. **That ingestion step will fail** because concepts are not registered yet — this is expected. The important output is the `claims.yaml` file on disk. Claim ingestion happens in Step 7 after concepts are registered.

### Fallback

Follow the extract-claims SKILL.md instructions through Step 3 (write claims.yaml). Steps 4-5 (validate + ingest) can be skipped here — they happen later.

## Step 6: Register Concepts

### Primary: Skill Invocation

```
/research-papers:register-concepts <paper-directory-path>
```

This runs `propose_concepts.py pks-batch` to extract concept names from claims.yaml, enriches definitions from notes.md, and calls `pks source add-concepts`.

### Fallback

Follow the register-concepts SKILL.md instructions directly.

**Why this order:** register-concepts runs AFTER extract-claims because it derives the concept inventory from claims.yaml. Claims use human-readable concept names; register-concepts extracts those names and registers them on the source branch.

## Step 7: Ingest Claims

Now that concepts are registered on the source branch, ingest claims:

```bash
source_name=$(basename "$paper_dir")
pks source add-claim "$source_name" --batch "$paper_dir/claims.yaml"
```

**If this fails with "unknown concept reference(s)":** the error lists specific missing names. Add those concepts to `concepts.yaml`, re-run `pks source add-concepts`, and retry `add-claim`. Iterate until `add-claim` succeeds — the unknown set is finite and shrinks each iteration.

## Step 8: Extract Justifications

### Primary: Skill Invocation

```
/research-papers:extract-justifications <paper-directory-path>
```

The skill writes justifications.yaml and ingests via `pks source add-justification`.

### Fallback

Follow the extract-justifications SKILL.md instructions directly.

## Step 9: Finalize Source Branch

```bash
pks source finalize "$source_name"
```

If status is "blocked", fix the reported errors and re-finalize. Common issues:
- Unknown concept references → iterate Step 7
- Missing claim artifact IDs → re-run Step 7
- Justification references unresolved claims → check claim IDs in justifications.yaml match claims.yaml

**Note:** Stances are NOT extracted here. Cross-paper stance extraction happens at collection level via the ingest-collection skill, after all papers have claims on master. This is because stances require visibility into other papers' promoted claims.

## Step 10: Report

When all steps have completed, write a summary to `./reports/paper-$SAFE_NAME.md` where $SAFE_NAME is derived from the paper directory name. Include:

- Paper directory path
- Whether retrieval succeeded (and source: arxiv/sci-hub/etc.)
- Whether reading succeeded
- Whether claim extraction succeeded (claim count by type)
- Whether concept registration succeeded (N exact-match links, N newly proposed)
- Whether claim ingestion succeeded (iterate-to-fixed-point cycles needed)
- Whether justification extraction succeeded (justification count)
- Whether finalize succeeded (status: ready/blocked)
- Usefulness rating for this project

## Error Handling

- If retrieval fails: report failure and stop. Do not proceed to reading.
- If reading fails: report what was retrieved but note the reading failure. Do not proceed to claim extraction.
- If claim extraction fails: report what was retrieved and read but note the extraction failure.
- If pks source init fails: report the error. This may mean propstore is not initialized.
- If finalize is blocked: report the specific errors. The paper is still usable — finalize can be re-run after fixing issues.
