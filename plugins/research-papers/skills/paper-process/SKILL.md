---
name: paper-process
description: Retrieve a paper and extract implementation-focused notes. Combines paper-retriever and paper-reader into one step. Give it a URL, DOI, or title.
argument-hint: "<url-or-doi-or-title>"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Paper Process: $ARGUMENTS

Download a scientific paper and extract structured notes in one shot.

## Execution Discipline

This skill is a checklist, not an outcome sketch.

**CRITICAL:**
This skill does NOT authorize creating any new scripts, automation, temp programs, or alternate workflows.
If the listed commands or nested skills cannot complete a step, stop immediately and report the blocker.

- Follow the steps in order.
- Do not substitute unlisted scripts, tools, or custom workflows for retrieval, reading, or claim extraction.
- If you can invoke the named nested skill, do that. If you cannot, use the fallback helper below and follow its stdout literally.
- If you are blocked on a specific step, stop there and report the exact blocker instead of inventing a workaround.
- Do not report progress from intermediate artifacts not named in this procedure.

## Codex / No-Nested-Skill Fallback

If your platform cannot reliably invoke one skill from inside another skill:

1. Use this skill's injected `<path>` to locate the installed `paper-process` skill directory.
2. Run this exact helper from that directory:
   ```bash
   python "<skill-dir>/scripts/emit_nested_process_fallback.py"
   ```
3. Read the FULL stdout.
4. Follow it exactly instead of opening sibling `SKILL.md` files piecemeal.

## Step 1: Retrieve the Paper

Invoke the **paper-retriever** skill with: `$ARGUMENTS`

If explicit skill invocation is available (for example `$paper-retriever` or a platform-specific slash command), use it. Otherwise, follow the paper-retriever SKILL.md instructions directly.

When retrieval completes, note the output path (e.g., `papers/Author_Year_ShortTitle/paper.pdf`).

## Step 2: Read and Extract Notes

Invoke the **paper-reader** skill with the path from Step 1.

If explicit skill invocation is available, use it. Otherwise, follow the paper-reader SKILL.md instructions directly.

Follow all instructions through to completion (notes.md, description.md, abstract.md, citations.md, index.md update).

## Step 3: Clean Up Source PDF

If the original argument was a local file path (e.g., `papers/somefile.pdf` in the root of `papers/`), and the paper directory now contains `paper.pdf`, **delete the original root-level PDF**:

```bash
# Only if the source was a local file and the paper dir copy exists
rm "./papers/somefile.pdf"
```

This keeps the `papers/` root clean — any PDF still in the root is unprocessed. Do NOT delete if the source was a URL (nothing to clean up) or if the paper directory doesn't have `paper.pdf` yet (something went wrong).

## Step 4: Extract Claims

Invoke the **extract-claims** skill with the paper directory path from Step 1.

If explicit skill invocation is available, use it. Otherwise, follow the extract-claims SKILL.md instructions directly.

The skill will auto-detect whether to enrich (if `generate_claims.py` produced a `claims.yaml`) or create from scratch.

## Step 5: Report

When all skills have completed, write a summary to `./reports/paper-$SAFE_NAME.md` where $SAFE_NAME is derived from the paper directory name. Include:

- Paper directory path
- Whether retrieval succeeded (and source: arxiv/sci-hub/etc.)
- Whether reading succeeded
- Whether claim extraction succeeded (mode used, claim count)
- Usefulness rating for this project

## Error Handling

- If retrieval fails: report failure and stop. Do not proceed to reading.
- If reading fails: report what was retrieved but note the reading failure. Do not proceed to claim extraction.
- If claim extraction fails: report what was retrieved and read but note the extraction failure.
