---
name: paper-retriever-institutional
description: Paywalled-access backend for paper-retriever. Retrieves a paywalled paper's PDF through an institutional / library subscription (a library proxy such as EZproxy or OpenAthens, or an institutional login), given an identifier (DOI/URL) and the target paper directory name. Invoked by paper-retriever when open-access channels fail. Enable this skill only if the install has institutional access configured.
argument-hint: "<doi-or-identifier> <dirname>"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI. Requires browser automation and configured institutional/library access."
---

# Paper Retriever — institutional access: $ARGUMENTS

This is a **paywalled-access backend** invoked by `paper-retriever` when open-access
channels fail. It is a pluggable access method: one of possibly several
`paper-retriever-*` access skills (sci-hub, institutional, …). Enable this one only if
the install actually has institutional or library subscription access — otherwise it has
nothing to resolve against and should stay disabled.

## Contract

- **Inputs:** `<identifier>` — a DOI/URL naming the intended paper — and `<dirname>` —
  the canonical paper directory `paper-retriever` already planned (e.g.
  `Author_Year_ShortTitle`).
- **Job:** place the intended paper's PDF at `./papers/<dirname>/paper.pdf`. Nothing
  else — `paper-retriever` materializes `metadata.json` and verifies after you return.
- **On success:** report that `./papers/<dirname>/paper.pdf` now holds the intended
  paper. **On miss** (no access to this title, or institutional access not configured):
  report failure cleanly so `paper-retriever` can try the next access method.

## Steps

1. Resolve the paywalled DOI/URL through the configured institutional route — typically a
   library proxy that rewrites the publisher URL (e.g.
   `https://doi-org.<proxy-host>/<doi>` for EZproxy, or the OpenAthens redirector), or an
   authenticated institutional session in the browser.
2. From the proxied publisher page, locate the full-text PDF link (the publisher's
   "Download PDF" / "Full text" control).
3. Create the paper directory and download the PDF:
   `mkdir -p "./papers/<dirname>" && curl -L -o "./papers/<dirname>/paper.pdf" "PROXIED_PDF_URL" 2>&1`
   (or save via the browser's print/download if the link requires the authenticated
   session).

Verify the result is a real PDF (`file "./papers/<dirname>/paper.pdf"` reports "PDF
document", size > 100KB) and that it is the **intended** paper before reporting success.
If it is wrong or missing, report a miss and remove any bad file
(`rm -f "./papers/<dirname>/paper.pdf"`).
