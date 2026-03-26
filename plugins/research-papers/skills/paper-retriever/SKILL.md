---
name: paper-retriever
description: Retrieve a scientific paper PDF given an arxiv URL, DOI, or paper title. Downloads to papers/ directory. Uses direct download for arxiv, Chrome + sci-hub for paywalled papers.
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

## Step 2: Search (title input only)

If the input is a paper title (not a URL or DOI), search for it first:

```bash
uv run scripts/search_papers.py "PAPER TITLE" --source all --max-results 5 --json
```

Review the results. If there's a clear match, extract the arxiv ID or DOI and continue to Step 3. If ambiguous, present the top results to the user and ask which one.

## Step 3: Download

Use the fetch_paper.py script to download the PDF and extract metadata:

```bash
uv run scripts/fetch_paper.py "<identifier>" --papers-dir papers/
```

Where `<identifier>` is the arxiv ID/URL, DOI, ACL URL, or S2 paper ID from the input or search results.

The script will:
1. Resolve metadata (title, authors, year, abstract) from arxiv or Semantic Scholar
2. Create the paper directory with canonical naming (`Author_Year_ShortTitle`)
3. Write `metadata.json` to the paper directory
4. Attempt PDF download via waterfall: direct download → Unpaywall → report fallback needed

## Step 4: Handle Fallback (if needed)

If fetch_paper.py returns `"fallback_needed": true`, the paper couldn't be downloaded via open-access channels. Fall back to browser automation for sci-hub:

**Try browser automation in this order:**

### Option 1: Any available browser automation (preferred)

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
6. Download: `curl -L -o "./papers/<dirname>/paper.pdf" "EXTRACTED_URL" 2>&1`

### Option 2: No browser automation

Report the DOI/URL and ask the user to download the PDF manually to the paper directory.

## Step 5: Verify

```bash
file "./papers/<dirname>/paper.pdf"
ls -la "./papers/<dirname>/"
```

Confirm:
- PDF exists and is valid ("PDF document" in file output)
- File size is reasonable (>100KB for a real paper)
- `metadata.json` exists with title, authors, year

## Output

When done, report:
```
Retrieved: papers/<dirname>/paper.pdf
Source: [arxiv/aclanthology/unpaywall/sci-hub]
Size: [file size]
```

## Error Handling

- If fetch_paper.py fails metadata resolution: try the other source (arxiv vs S2)
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
