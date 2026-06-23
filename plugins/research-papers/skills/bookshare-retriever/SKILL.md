---
name: bookshare-retriever
description: Retrieve a book (EPUB3) from Bookshare.org given a title or Bookshare title ID. By default it logs into your Bookshare account in a real browser with your stored username/password (no developer api_key needed), downloads the EPUB into papers/, and writes metadata.json. An official-API backend and a guest (public-domain) mode are also available. Optionally converts to paper.pdf for the reader.
argument-hint: "<book-title-or-bookshare-id> [--convert] [--no-headless] [--guest]"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI. Requires shell access. The default browser backend needs your Bookshare username/password stored in .secrets/bookshare.json (run configure-bookshare) and a Chrome/Chromium browser. --convert needs headless Chrome."
---

# Bookshare Retriever: $ARGUMENTS

Download a book from Bookshare.org as EPUB3 into the `papers/` collection, then
optionally convert it to `paper.pdf` so the existing `paper-reader` pipeline can
ingest it. `$ARGUMENTS` names exactly one intended book; preserve that identity
throughout retrieval.

The **default backend is the browser** (`auth_method = "browser"`): it works with
just a username/password — no developer api_key. All secrets live in the gitignored
`.secrets/bookshare.json`; never echo their values. If credentials aren't set up
yet, run `/research-papers:configure-bookshare` first.

## Script Paths

The `scripts/...` paths below are relative to this skill's directory. Resolve them
against the installed skill location, not the user's project root.

## Step 1: Ensure credentials are present

```bash
uv run scripts/credential_store.py show bookshare --root .
```

Prints presence only (e.g. `username: set`, `password: set`), never values. For the
default browser backend you need `username` + `password`. If they're missing, STOP
and run `/research-papers:configure-bookshare` (or print the file path with
`uv run scripts/credential_store.py path bookshare --root .` and have the user fill
it). **Never print secret values.**

## Step 2: Download (default: browser backend)

```bash
uv run scripts/fetch_book.py "<title or Bookshare ID>" --root . --papers-dir papers/
```

Because the default `auth_method` is `browser`, this delegates to the browser
backend (`scripts/bookshare_browser.py`), which: opens a browser, logs into
www.bookshare.org with the stored credentials, searches for the title, requests the
EPUB, waits for Bookshare to prepare it, downloads it, validates the EPUB magic
bytes, and writes `papers/<dirname>/book.epub` + `metadata.json` (dirname is the
canonical `Author_Year_ShortTitle`).

Add `--no-headless` to watch the browser, or run the backend directly:

```bash
uv run scripts/bookshare_browser.py "<title or Bookshare ID>" --root . --papers-dir papers/ --no-headless
```

If the resolved title looks wrong, re-run with a more specific query or the exact
Bookshare ID and confirm with the user before keeping it.

### Alternatives

- **Official API** (needs a developer api_key + trusted-client approval): set
  `--auth-method api`. First acquire a token with
  `uv run scripts/bookshare_auth.py token --root .` (prints validity only, never the
  token), then `uv run scripts/fetch_book.py "<id>" --auth-method api --root .`.
- **Guest / public-domain** (no login, requires an api_key for the API): add
  `--guest` to reach only public-domain / Creative Commons titles.

## Step 3: Verify

```bash
ls -la "./papers/<dirname>/"
```

Confirm `book.epub` exists (non-trivial size) and `metadata.json` carries the title,
authors, year, and `"source": "bookshare"`. The JSON result on stdout reports the
source-adapter contract keys (`success`, `directory`, `dirname`, `artifact_path`,
`artifact_type`, `metadata_path`, `downloaded`, `fallback_needed`).

## Step 4: Convert to paper.pdf (optional — only with `--convert`)

Only when the user passed `--convert` or set `[sources.bookshare] convert_to_pdf =
true`. Download-only is the default; books are long and the reader pipeline is
expensive.

Convert the EPUB to `paper.pdf` using headless Chrome (the engine `paper-retriever`
uses). Locate Chrome:

```bash
for p in "/c/Program Files/Google/Chrome/Application/chrome.exe" \
         "/c/Program Files (x86)/Google/Chrome/Application/chrome.exe" \
         "/usr/bin/google-chrome" "/usr/bin/chromium" \
         "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"; do
  [ -x "$p" ] && CHROME="$p" && break
done
```

Unpack the EPUB and print its spine HTML to a single PDF (an EPUB is a ZIP of XHTML;
the reading order is the spine of its `.opf` package document):

```bash
unzip -o "./papers/<dirname>/book.epub" -d "./papers/<dirname>/epub-src"
"$CHROME" --headless --disable-gpu --no-sandbox \
  --print-to-pdf="./papers/<dirname>/paper.pdf" \
  --print-to-pdf-no-header \
  "file:///<absolute path to the assembled spine HTML>"
file "./papers/<dirname>/paper.pdf"   # expect "PDF document"
```

For higher fidelity the user may install Calibre and set `[sources.bookshare]
converter = "calibre"`, then `ebook-convert book.epub paper.pdf`. Once `paper.pdf`
exists, hand off: `/research-papers:paper-reader papers/<dirname>`.

## Output

```
Retrieved: papers/<dirname>/book.epub
Source: bookshare (browser)
Size: [file size]
Converted: papers/<dirname>/paper.pdf   (only if --convert was used)
```

## Error Handling

- Missing credentials → STOP at Step 1; run configure-bookshare. Never print values.
- Login/download failure → `fallback_needed: true` with an error message (no secret
  values); no directory is created. Report and stop.
- Always clean up temp files on failure: `rm -f ./papers/temp_fetch_*.epub`.

## Execution Discipline

Follow the steps in order. Do not substitute alternate download paths or scrape the
site outside the documented backends. If a step is blocked, stop and report.
