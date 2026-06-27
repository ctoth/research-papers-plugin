---
name: paper-retriever-scihub
description: Paywalled-access backend for paper-retriever. Retrieves a paywalled paper's PDF via sci-hub browser automation, given an identifier (DOI/URL) and the target paper directory name. Invoked by paper-retriever when open-access channels fail; enabled by default. Disable this skill to remove sci-hub from the retrieval waterfall.
argument-hint: "<doi-or-identifier> <dirname>"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI. Requires browser automation."
---

# Paper Retriever — sci-hub access: $ARGUMENTS

This is a **paywalled-access backend** invoked by `paper-retriever` when open-access
channels fail. It is a pluggable access method: one of possibly several
`paper-retriever-*` access skills (sci-hub, institutional, …). A user enables only the
access methods they have; this one ships enabled by default.

## Contract

- **Inputs:** `<identifier>` — a DOI/URL naming the intended paper — and `<dirname>` —
  the canonical paper directory `paper-retriever` already planned (e.g.
  `Author_Year_ShortTitle`).
- **Job:** place the intended paper's PDF at `./papers/<dirname>/paper.pdf`. Nothing
  else — `paper-retriever` materializes `metadata.json` and verifies after you return.
- **On success:** report that `./papers/<dirname>/paper.pdf` now holds the intended
  paper. **On miss** (sci-hub does not have it, or no browser automation): report failure
  cleanly so `paper-retriever` can try the next access method. Do not fabricate a PDF.

## Steps

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
6. Create the paper directory and download the PDF:
   `mkdir -p "./papers/<dirname>" && curl -L -o "./papers/<dirname>/paper.pdf" "EXTRACTED_URL" 2>&1`

Verify the result is a real PDF before reporting success
(`file "./papers/<dirname>/paper.pdf"` reports "PDF document", size > 100KB) and that it
is the **intended** paper (title page matches the identifier). If it is wrong or missing,
report a miss — do not leave a bad PDF in place (`rm -f "./papers/<dirname>/paper.pdf"`).
