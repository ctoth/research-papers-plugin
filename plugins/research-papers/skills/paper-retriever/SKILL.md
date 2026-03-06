---
name: paper-retriever
description: Retrieve a scientific paper PDF given an arxiv URL, DOI, or paper title. Downloads to papers/ directory. Uses direct download for arxiv, Chrome + sci-hub for paywalled papers.
argument-hint: "<arxiv-url-or-doi> [optional-output-name]"
disable-model-invocation: false
---

# Paper Retriever: $ARGUMENTS

Download a scientific paper PDF to the `papers/` directory.

## Step 1: Parse Input

The argument can be:
- An arxiv URL: `https://arxiv.org/abs/XXXX.XXXXX` or `https://arxiv.org/pdf/XXXX.XXXXX`
- A DOI: `10.XXXX/...`
- An ACL Anthology URL: `https://aclanthology.org/...`
- An AAAI URL: `https://ojs.aaai.org/...`
- A paper title (will search arxiv)

## Step 2: Determine Download Strategy

**IMPORTANT**: Use a unique temp filename to avoid collisions during parallel downloads.
Generate a short identifier from the URL (e.g., arxiv ID, last path segment).

### Case A: Arxiv URL
Arxiv PDFs are freely available. Convert URL to direct PDF link:
- `https://arxiv.org/abs/XXXX.XXXXX` -> `https://arxiv.org/pdf/XXXX.XXXXX.pdf`
- `https://arxiv.org/pdf/XXXX.XXXXX` -> already a PDF URL, ensure `.pdf` suffix

```bash
# Use arxiv ID as unique temp name to avoid parallel collisions
curl -L -o "./papers/temp_ARXIVID.pdf" "https://arxiv.org/pdf/XXXX.XXXXX.pdf" 2>&1
```

Verify it's a valid PDF:
```bash
file "./papers/temp_ARXIVID.pdf"
```

If the output contains "PDF document" -> success. Continue to Step 3.
If not -> the download failed or returned HTML. Try adding `.pdf` to the URL.

**IMPORTANT - Metadata extraction for arxiv papers:**
Most arxiv PDFs can't be parsed directly (often report "password-protected" falsely).
Instead, fetch metadata from the arxiv abstract page:

Fetch `https://arxiv.org/abs/XXXX.XXXXX` and extract:
1. Full paper title
2. All author names
3. Year of publication
4. Venue/conference if mentioned
5. Abstract text

This reliably gives you title, authors, year without needing to parse the PDF.

### Case B: ACL Anthology URL
ACL Anthology PDFs are freely available:
- `https://aclanthology.org/2024.lrec-main.292/` -> `https://aclanthology.org/2024.lrec-main.292.pdf`

```bash
curl -L -o "./papers/temp_IDENTIFIER.pdf" "https://aclanthology.org/XXXX.pdf" 2>&1
```

Fetch metadata from the abstract page too.

### Case C: Other URL or DOI (paywalled)

Use browser automation to navigate to sci-hub and download the PDF.

**Try browser tools in this order:**

#### Option 1: Playwright MCP (preferred — works on all platforms)

If Playwright MCP tools are available (`browser_navigate`, `browser_click`, etc.):

1. `browser_navigate` to `https://sci-hub.st/`
2. `browser_snapshot` to find the input field
3. `browser_type` to enter the URL/DOI in the search field
4. `browser_click` the submit/open button
5. `browser_snapshot` to look for an iframe or embed with a PDF URL
6. If needed, `browser_evaluate` to extract the PDF URL:
   ```js
   const iframe = document.querySelector('#pdf');
   if (iframe) return iframe.src;
   const embed = document.querySelector('embed[type="application/pdf"]');
   if (embed) return embed.src;
   const links = [...document.querySelectorAll('a')].filter(a => a.href.includes('.pdf'));
   return links.map(a => a.href);
   ```
7. Download: `curl -L -o "./papers/temp_IDENTIFIER.pdf" "EXTRACTED_URL" 2>&1`

#### Option 2: Claude-in-Chrome (Claude Code fallback)

If Playwright is not available but `mcp__claude-in-chrome__navigate` is:

1. `mcp__claude-in-chrome__navigate` to `https://sci-hub.st/`
2. `mcp__claude-in-chrome__form_input` to enter the URL/DOI
3. `mcp__claude-in-chrome__computer` to click submit
4. `mcp__claude-in-chrome__javascript_tool` to extract PDF URL (same JS as above)
5. Download: `curl -L -o "./papers/temp_IDENTIFIER.pdf" "EXTRACTED_URL" 2>&1`

#### Option 3: No browser automation

Report the DOI/URL and ask the user to download the PDF manually to `./papers/`.

### Case D: Paper Title (no URL)
Search arxiv first:

```bash
# URL-encode the title and search arxiv API
curl -s "http://export.arxiv.org/api/query?search_query=ti:%22PAPER+TITLE%22&max_results=3" 2>&1
```

Parse the XML response to find the arxiv ID, then follow Case A.

If not on arxiv, use Chrome to search Google Scholar and follow Case C with the found DOI.

## Step 3: Create Directory and Move PDF

From the metadata extracted in Step 2, construct the directory name:

**Naming convention**: `FirstAuthorLastName_Year_ShortTitle`
- ShortTitle: 2-4 key words from the title, CamelCase, no spaces
- Examples: `Wang_2024_DynamicHierarchicalOutlining`, `Bae_2024_CollectiveCritics`
- Drop filler words (A, The, An, For, With, etc.) from the short title
- If title has an acronym (e.g., "GROVE: A Retrieval..."), use it: `Wen_2023_GROVE`

```bash
mkdir -p "./papers/FirstAuthor_Year_ShortTitle"
mv "./papers/temp_IDENTIFIER.pdf" "./papers/FirstAuthor_Year_ShortTitle/paper.pdf"
```

## Step 4: Verify

```bash
file "./papers/FirstAuthor_Year_ShortTitle/paper.pdf"
ls -la "./papers/FirstAuthor_Year_ShortTitle/"
```

Confirm:
- PDF exists and is valid ("PDF document" in file output)
- File size is reasonable (>100KB for a real paper)

## Output

When done, report:
```
Retrieved: papers/FirstAuthor_Year_ShortTitle/paper.pdf
Source: [arxiv/aclanthology/sci-hub]
Size: [file size]
```

## Error Handling

- If curl fails: check URL, try with/without .pdf suffix
- If `file` says it's HTML, not PDF: the server returned a paywall page. Fall back to sci-hub (Case C).
- If sci-hub fails: report failure, provide the URL for manual download
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
