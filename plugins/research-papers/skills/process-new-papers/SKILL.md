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

- **reconcile needed**: paper-reader already invokes reconcile as part of its flow (Step 7) but you may need to do it again at the end.
