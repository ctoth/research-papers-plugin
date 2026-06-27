---
name: paper-retriever
description: Retrieve a scientific paper PDF given an arxiv URL, DOI, or paper title. Downloads to papers/ directory. Uses direct download for arxiv, Chrome print-to-pdf for publisher-direct HTML, and a title-based open-repository search (arXiv / Semantic Scholar / Unpaywall) for paywalled papers; reports "supply a PDF" when no open-access copy exists.
argument-hint: "<arxiv-url-or-doi> [optional-output-name]"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI. Requires shell access; browser automation is optional for paywalled papers."
---

# Paper Retriever: $ARGUMENTS

Download a scientific paper PDF to the `papers/` directory.

## Script Paths

The command examples below use `scripts/...` paths that are relative to this skill's directory. Resolve them against the installed skill location, not the user's project root.

## Step 1: Parse Input

The argument can be:
- An arxiv URL: `https://arxiv.org/abs/XXXX.XXXXX` or `https://arxiv.org/pdf/XXXX.XXXXX`
- A DOI: `10.XXXX/...`
- An ACL Anthology URL: `https://aclanthology.org/...`
- An AAAI URL: `https://ojs.aaai.org/...`
- A paper title (will search)

`$ARGUMENTS` names exactly one intended paper. Preserve that identity throughout retrieval.

The goal of this skill is to obtain the intended paper's PDF. Metadata resolution and canonical naming support that goal; they are not the definition of success.

## Step 1.5: Normalize to an Identity-Preserving Input

Before downloading, decide whether the input is already a strong paper identifier:

- **Strong inputs:** arxiv ID/URL, DOI/DOI URL, ACL Anthology URL, S2 paper ID, direct PDF URL, exact paper title
- **Weak inputs:** publisher landing pages, journal homepages, PMC/article pages, society pages, or generic URLs that may require interpretation before they identify one paper cleanly

If the input is weak, first infer the intended paper and continue with the strongest identity-preserving input available. Prefer:

1. DOI
2. ACL Anthology ID/URL
3. arXiv ID/URL
4. S2 paper ID
5. exact paper title
6. the original weak URL only if it is still the clearest remaining identifier

Do not keep retrying a weak URL mechanically when a stronger identifier is already apparent.

## Step 2: Search (title input only)

If the input is a paper title (not a URL or DOI), search for it first:

```bash
uv run scripts/search_papers.py "PAPER TITLE" --source all --max-results 5 --json
```

Review the results. If there's a clear match, extract the strongest available identifier and continue to Step 3. If ambiguous, present the top results to the user and ask which one.

For weak URL input, use the inferred title or metadata from Step 1.5 and perform the same search/normalization before Step 3.

## Step 3: Download

Use the fetch_paper.py script to download the PDF and extract metadata:

```bash
uv run scripts/fetch_paper.py "<identifier>" --papers-dir papers/
```

Where `<identifier>` is the arxiv ID/URL, DOI, ACL URL, or S2 paper ID from the input or search results.

If you had to normalize a weak input first, use the normalized identifier here rather than the original weak URL.

Use `fetch_paper.py` as the first download path, not as the definition of whether retrieval is possible. One metadata-resolution failure does not by itself mean the paper is unretrievable.

The script will:
1. Resolve metadata (title, authors, year, abstract) from arxiv or Semantic Scholar
2. Attempt PDF download via waterfall: direct download → Unpaywall → report fallback needed
3. Only after a real PDF is downloaded, create the canonical paper directory (`Author_Year_ShortTitle`)
4. Only after a real PDF is downloaded, write `metadata.json` alongside `paper.pdf`

Before treating Step 3 as successful, verify that the resolved metadata still matches the intended paper. If not, stop on mismatch.

If `fetch_paper.py` obtains the intended paper's PDF through an allowed path, Step 3 succeeded even if metadata had to be materialized afterward.

## Step 4: Handle Fallback (if needed)

If fetch_paper.py returns `"fallback_needed": true`, the paper couldn't be downloaded via open-access channels. In that case it returns the planned `dirname`/`directory` plus inline `metadata`, but it does **not** create `metadata.json` or the paper directory yet.

**Choose the fallback path by input shape:**

### Option 0: Publisher-hosted HTML document (W3C TR, ECMA / ISO specs, some tech reports)

Papers with **no DOI and no arxiv ID** that live at a canonical publisher URL as HTML (and possibly also as PDF) should use headless Chrome print-to-pdf. W3C Recommendations (`https://www.w3.org/TR/...`) are the canonical example.

Detect this case when:
- The input was a `w3.org/TR/...`, `ecma-international.org`, or similar publisher URL, OR
- Metadata resolution succeeded but no DOI/arxiv_id was attached, AND the paper has a stable public landing URL.

Locate Chrome:

```bash
for p in "/c/Program Files/Google/Chrome/Application/chrome.exe" \
         "/c/Program Files (x86)/Google/Chrome/Application/chrome.exe" \
         "/usr/bin/google-chrome" "/usr/bin/chromium" \
         "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"; do
  [ -x "$p" ] && CHROME="$p" && break
done
```

Print the canonical URL to PDF:

```bash
mkdir -p "./papers/<dirname>"
"$CHROME" --headless --disable-gpu --no-sandbox \
  --print-to-pdf="./papers/<dirname>/paper.pdf" \
  --print-to-pdf-no-header \
  "<canonical URL>"
```

Verify the output is a valid PDF (`file ./papers/<dirname>/paper.pdf` reports "PDF document", size > 100KB) before treating this as success. Then materialize `metadata.json`:

```bash
uv run scripts/fetch_paper.py "<identifier>" --papers-dir papers/ --output-dir "<dirname>" --metadata-only
```

If metadata resolution already failed and no DOI/arxiv lookup can produce fields, write `metadata.json` by hand from the paper's title page (title, authors, year required; `doi` and `arxiv_id` as `null`; `url` set to the canonical URL).

If this path succeeds, STOP.

### Option 1: Institutional / library access (try first, if configured)

If the install has institutional or library access configured (e.g. a library
proxy such as EZproxy / OpenAthens, or an institutional login), resolve the
paywalled DOI through it and download the PDF to the paper directory, then
materialize `metadata.json` (`--metadata-only`). Most installs will not have this
configured; if so, continue to Option 2.

### Option 2: Title-based open-repository search

For a paywalled DOI with no open-access copy from the steps above, do **not** use
shadow-library mirrors (they are unusable here: policy plus captcha walls, and
they waste latency). Instead, search the open repositories by **title**:

1. Search arXiv, Semantic Scholar, and institutional / preprint repositories for
   the paper's exact title (`uv run scripts/search_papers.py "<title>"`).
2. Query Unpaywall by title/DOI for a legal open-access PDF location.
3. If an open-access copy is found, download it to the paper directory and
   materialize `metadata.json`:
   ```bash
   mkdir -p "./papers/<dirname>" && curl -L -o "./papers/<dirname>/paper.pdf" "OPEN_ACCESS_URL"
   uv run scripts/fetch_paper.py "<identifier>" --papers-dir papers/ --output-dir "<dirname>" --metadata-only
   ```

### Option 3: No open-access copy found

If no open-access copy exists, STOP and report cleanly: "open-access copy not
found, supply a PDF." Ask the user to download the PDF manually into the paper
directory (via their institutional access or whatever route they use); do not
attempt shadow-library mirrors from here.

## Step 5: Verify

```bash
file "./papers/<dirname>/paper.pdf"
ls -la "./papers/<dirname>/"
```

Confirm:
- PDF exists and is valid ("PDF document" in file output)
- File size is reasonable (>100KB for a real paper)
- `metadata.json` exists with title, authors, year

The core success condition is that the intended paper's PDF exists at `./papers/<dirname>/paper.pdf`. `metadata.json` should also exist by the end of the step, but earlier metadata-resolution failures do not negate successful retrieval if the correct PDF and final metadata are in place.

## Output

When done, report:
```
Retrieved: papers/<dirname>/paper.pdf
Source: [arxiv/aclanthology/unpaywall/open-repository]
Size: [file size]
```

## Error Handling

- If fetch_paper.py fails metadata resolution: try the other source (arxiv vs S2)
- If metadata resolution or search yields a different paper than the intended one: stop and report the mismatch
- If all download methods fail: report failure, provide the URL for manual download
- ALWAYS clean up temp files on failure: `rm -f ./papers/temp_*.pdf`

## CRITICAL: File Modified Error Workaround

If Edit/Write fails with "file unexpectedly modified":
1. Read the file again
2. Retry the edit
3. Try path formats: `./relative`, `C:/forward/slashes`, `C:\back\slashes`
4. Prefer your file editing tools over shell text manipulation (cat, sed, echo)
5. If all formats fail, STOP and report

## CRITICAL: Parallel Swarm Awareness

You may be running alongside other agents in parallel.

**FORBIDDEN GIT COMMANDS - NEVER USE THESE:**
- `git stash`, `git restore`, `git checkout`, `git reset`, `git clean`
