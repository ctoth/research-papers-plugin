---
name: process-new-papers
description: Process all unprocessed PDF files in the papers/ root directory, one at a time. Any PDF in papers/ root is unprocessed by convention (processed papers live in subdirectories). Invokes paper-reader on each sequentially.
argument-hint: ""
disable-model-invocation: false
---

# Process New Papers

Find and process all unprocessed PDFs in `papers/` root, one at a time.

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

## Step 2: Process Each Paper Sequentially

For each PDF found, invoke the **paper-reader** skill:

```
/research-papers:paper-reader papers/filename.pdf
```

Wait for each paper to complete before starting the next. The paper-reader skill handles:
- Creating the output directory
- Moving the PDF (not copying)
- Extracting notes, description, abstract, citations
- Cross-referencing with the collection (reconcile)
- Updating papers/index.md
- Cleaning up the root PDF (including if already processed)

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

- **One at a time**: Do not process papers in parallel. Each paper-reader invocation may dispatch its own subagents internally.
- **Already-processed PDFs**: If paper-reader detects a paper is already complete, it will delete the duplicate root PDF and move on. This is expected behavior.
- **No reconcile needed**: paper-reader already invokes reconcile as part of its flow (Step 7.5). No need to run a separate reconcile pass.
