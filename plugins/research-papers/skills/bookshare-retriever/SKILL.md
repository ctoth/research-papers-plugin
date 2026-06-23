---
name: bookshare-retriever
description: Retrieve a book (EPUB3) from Bookshare.org given a title or Bookshare title ID. Authenticates with stored credentials (official Bookshare API OAuth2 password grant, or a browser backend), downloads the EPUB into papers/, writes metadata.json, and optionally converts to paper.pdf for the reader. Public-domain / Creative Commons titles work in guest mode without credentials.
argument-hint: "<book-title-or-bookshare-id> [--convert] [--guest]"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI. Requires shell access. The official API needs a developer api_key + trusted-client approval; browser automation is an optional alternative. --convert needs headless Chrome."
---

# Bookshare Retriever: $ARGUMENTS

Download a book from Bookshare.org as EPUB3 into the `papers/` collection, then
optionally convert it to `paper.pdf` so the existing `paper-reader` pipeline can
ingest it. `$ARGUMENTS` names exactly one intended book; preserve that identity
throughout retrieval.

This skill is the authenticated instance of the source-adapter pattern (see
`templates/source-adapter/HOWTO.md`). All secrets live in the gitignored
`.secrets/bookshare.json` — never echo their values.

## Script Paths

The `scripts/...` paths below are relative to this skill's directory. Resolve them
against the installed skill location, not the user's project root.

## Step 1: Ensure config + credentials present

```bash
uv run scripts/credential_store.py show bookshare --root .
```

This prints presence only (e.g. `api_key: set`, `password: set`), never values. If
required secrets are missing for the configured auth method, STOP and tell the user
to populate the file printed by:

```bash
uv run scripts/credential_store.py path bookshare --root .
```

Populate it without exposing values in shell history, e.g.:

```bash
printf '%s' "<value>" | uv run scripts/credential_store.py set bookshare api_key --from-stdin --root .
```

- **api** backend (default) requires `api_key`, `username`, `password`.
- **browser** backend requires `username`, `password`.
- With `--guest`, skip credentials entirely (public-domain / Creative Commons only).

**Never print secret values** in your output or logs.

## Step 2: Authenticate

```bash
uv run scripts/bookshare_auth.py token --root .
```

Acquires and caches an access token via the credential store (a valid cached token
short-circuits re-auth). The command prints token validity only, never the token.

- Default `--auth-method api`: Bookshare OAuth2 password grant.
- `--auth-method browser`: drive a login in a real browser and capture the session.
- `--guest`: skip this step (no token; public-domain / CC titles only).

If authentication fails, report the error message (which contains no secret values)
and stop.

## Step 3: Resolve the title / Bookshare ID

```bash
uv run scripts/fetch_book.py "<title or Bookshare ID>" --metadata-only --root . --papers-dir papers/
```

Review the resolved metadata. If the match is ambiguous, present the candidates to
the user and ask which book to retrieve before downloading. Confirm the resolved
title still matches the intended book.

## Step 4: Download the EPUB3

```bash
uv run scripts/fetch_book.py "<resolved title or ID>" --root . --papers-dir papers/
```

The script requests EPUB3 (auto-prepared by Bookshare), streams it to a temp file,
validates the EPUB/ZIP magic bytes, and only then materializes
`papers/<dirname>/book.epub` and `papers/<dirname>/metadata.json` (dirname is the
canonical `Author_Year_ShortTitle`). Add `--guest` for public-domain / CC titles.

## Step 5: Verify

```bash
ls -la "./papers/<dirname>/"
```

Confirm `book.epub` exists (non-trivial size) and `metadata.json` carries the title,
authors, year, and `"source": "bookshare"`. The JSON result on stdout reports the
source-adapter contract keys (`success`, `directory`, `dirname`, `artifact_path`,
`artifact_type`, `metadata_path`, `downloaded`, `fallback_needed`).

## Step 6: Convert to paper.pdf (optional — only with `--convert`)

Only run this when the user passed `--convert` or set `[sources.bookshare]
convert_to_pdf = true`. Download-only is the default; books are long and the reader
pipeline is expensive.

Convert the EPUB to a PDF named `paper.pdf` using headless Chrome (the same engine
`paper-retriever` uses for HTML specs). First locate Chrome:

```bash
for p in "/c/Program Files/Google/Chrome/Application/chrome.exe" \
         "/c/Program Files (x86)/Google/Chrome/Application/chrome.exe" \
         "/usr/bin/google-chrome" "/usr/bin/chromium" \
         "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"; do
  [ -x "$p" ] && CHROME="$p" && break
done
```

Unpack the EPUB and print its spine HTML to PDF (an EPUB is a ZIP of XHTML; the
reading order is listed in the spine of its `.opf` package document):

```bash
unzip -o "./papers/<dirname>/book.epub" -d "./papers/<dirname>/epub-src"
# Order the spine XHTML per the .opf, then print to a single PDF:
"$CHROME" --headless --disable-gpu --no-sandbox \
  --print-to-pdf="./papers/<dirname>/paper.pdf" \
  --print-to-pdf-no-header \
  "file:///<absolute path to the assembled spine HTML>"
file "./papers/<dirname>/paper.pdf"   # expect "PDF document"
```

For higher-fidelity conversion the user may install Calibre and set
`[sources.bookshare] converter = "calibre"`, then
`ebook-convert "./papers/<dirname>/book.epub" "./papers/<dirname>/paper.pdf"`.

Once `paper.pdf` exists, hand off to the reader: `/research-papers:paper-reader
papers/<dirname>`.

## Output

When done, report:

```
Retrieved: papers/<dirname>/book.epub
Source: bookshare
Size: [file size]
Converted: papers/<dirname>/paper.pdf   (only if --convert was used)
```

## Error Handling

- Missing credentials → STOP at Step 1 with the file path to populate. Never print values.
- Auth failure → report the Step 2 error (no secret values) and stop.
- `fallback_needed: true` → the EPUB could not be retrieved (often a non-qualifying
  guest title or an account that lacks access); no directory is created. Report and stop.
- Always clean up temp files on failure: `rm -f ./papers/temp_fetch_*.epub`.

## Execution Discipline

Follow the steps in order. Do not substitute alternate download paths or scrape the
website outside the documented backends. If a step is blocked (e.g. no api_key yet),
stop at that step and report the blocker.
