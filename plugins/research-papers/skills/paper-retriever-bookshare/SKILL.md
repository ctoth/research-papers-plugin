---
name: paper-retriever-bookshare
description: Credentialed-source backend for retrieving books from Bookshare (bookshare.org) into the papers/ collection. Given a book title or ISBN and a target directory name, it searches Bookshare and downloads the EPUB via the published `bookshare` CLI. Download-only (produces book.epub). Enable only if you have a Bookshare account; requires credentials in a gitignored .secrets/bookshare.json.
argument-hint: "<book-title-or-isbn> [dirname]"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI. Requires shell access, uv, and a Bookshare account."
---

# Paper Retriever — Bookshare access: $ARGUMENTS

A **credentialed-source access skill** (a sibling of `paper-retriever-scihub` and
`paper-retriever-institutional`) for pulling **books** from
[Bookshare](https://www.bookshare.org). Bookshare is account-gated, so this skill is
opt-in: enable it only if you have a Bookshare membership and credentials configured.

Unlike the DOI-based access skills, Bookshare is searched by **title or ISBN** and is
invoked directly when you want a book, not via the core retriever's paywalled-DOI handoff.

## Contract

- **Inputs:** `<book-title-or-isbn>` — a title (default) or an ISBN — and an optional
  `<dirname>` (the canonical paper directory, e.g. `Author_Year_ShortTitle`). If omitted,
  derive `<dirname>` from the chosen book's author/year/title.
- **Job:** place the book's EPUB at `./papers/<dirname>/book.epub` and write
  `./papers/<dirname>/metadata.json`. **Download-only** — it does not convert to PDF.
- **On miss** (not on Bookshare, or no entitlement): report cleanly so the caller knows
  Bookshare did not have it.

## Credentials (one-time)

Create a gitignored `.secrets/bookshare.json` at the collection root:

```json
{ "api_key": "<bookshare-api-key>", "username": "<bookshare-username>", "password": "<bookshare-password>" }
```

`.secrets/` is gitignored — credentials are never committed. The wrapper
(`scripts/bookshare_cli.py`) loads them into `BOOKSHARE_*` for the `bookshare` CLI.

## Steps

1. **Search.** Title (default) or ISBN:
   ```bash
   uv run scripts/bookshare_cli.py search "<title>" --json
   # or, for an ISBN:
   uv run scripts/bookshare_cli.py search "<isbn>" --by isbn --json
   ```
   This prints the matching book records as JSON (each has `id`, `title`, `author`,
   `downloadFormat`).

2. **Pick the intended book.** Choose the record that matches the requested book. If the
   results are ambiguous, present the top few (id / title / author) to the user and ask
   which one. Keep its `id` and metadata.

3. **Download the EPUB** to the paper directory:
   ```bash
   mkdir -p "./papers/<dirname>"
   uv run scripts/bookshare_cli.py download <id> -o "./papers/<dirname>/book.epub"
   ```

4. **Verify** it is a real EPUB before treating this as success:
   ```bash
   file "./papers/<dirname>/book.epub"   # "EPUB document" / "Zip archive data"
   ```
   An EPUB begins with the ZIP signature `PK`. If the download is empty or not a ZIP/EPUB,
   report a miss and remove it (`rm -f "./papers/<dirname>/book.epub"`).

5. **Write `metadata.json`** from the chosen record (`title`, `authors`, `year` if known;
   `isbn` if present; `source: "bookshare"`; `document_type: "book"`). For BibTeX use
   `@book` (see the book-chapter / document-type handling in `paper-reader`).

## Notes

- **Download-only by design.** Reading a book with the image-based `paper-reader` needs a
  PDF; converting EPUB→PDF is intentionally out of scope here. Retrieve the EPUB first;
  conversion/reading is a separate step.
- Same access terms as downloading from your Bookshare account by hand (including any
  watermarking). This skill automates your own entitled downloads, nothing more.
