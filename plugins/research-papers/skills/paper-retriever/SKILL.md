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

`$ARGUMENTS` names exactly one intended paper. Preserve that identity throughout retrieval. Do not silently switch to a different paper just because search or metadata lookup returned something plausible.

The goal of this skill is to obtain the intended paper's PDF. Metadata resolution and canonical naming are supporting steps, not the definition of success.

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

Do not keep retrying a weak URL mechanically when the paper title or a stronger identifier is already apparent from the page or surrounding context.

## Step 2: Search (title input only)

If the input is a paper title (not a URL or DOI), search for it first:

```bash
uv run scripts/search_papers.py "PAPER TITLE" --source all --max-results 5 --json
```

Review the results. If there's a clear match, extract the arxiv ID or DOI and continue to Step 3. If ambiguous, present the top results to the user and ask which one.

For weak URL input, use the intended paper title or other metadata you inferred in Step 1.5 and perform the same search/normalization before Step 3.

## Step 3: Download

Use the fetch_paper.py script to download the PDF and extract metadata:

```bash
uv run scripts/fetch_paper.py "<identifier>" --papers-dir papers/
```

Where `<identifier>` is the arxiv ID/URL, DOI, ACL URL, or S2 paper ID from the input or search results.

If you had to normalize a weak input first, use the normalized identifier here rather than the original weak URL.

Use `fetch_paper.py` as the first download path, not as the definition of whether retrieval is possible. If one metadata-resolution path fails, that does not by itself mean the paper is unretrievable.

The script will:
1. Resolve metadata (title, authors, year, abstract) from arxiv or Semantic Scholar
2. Attempt PDF download via waterfall: direct download → Unpaywall → report fallback needed
3. Only after a real PDF is downloaded, create the canonical paper directory (`Author_Year_ShortTitle`)
4. Only after a real PDF is downloaded, write `metadata.json` alongside `paper.pdf`

Before treating Step 3 as successful, verify that the resolved metadata still matches the intended paper. If title/authorship/year indicate a materially different paper, stop and report an identity mismatch instead of continuing.

If `fetch_paper.py` obtains the intended paper's PDF through an allowed path, Step 3 succeeded even if metadata had to be materialized afterward.

## Step 4: Handle Fallback (if needed)

If fetch_paper.py returns `"fallback_needed": true`, the paper couldn't be downloaded via open-access channels. In that case it returns the planned `dirname`/`directory` plus inline `metadata`, but it does **not** create `metadata.json` or the paper directory yet. Fall back to browser automation for sci-hub:

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
6. Create the paper directory and download the PDF: `mkdir -p "./papers/<dirname>" && curl -L -o "./papers/<dirname>/paper.pdf" "EXTRACTED_URL" 2>&1`
7. Materialize `metadata.json` only after `paper.pdf` exists:
   `uv run scripts/fetch_paper.py "<identifier>" --papers-dir papers/ --output-dir "<dirname>" --metadata-only`

If browser automation or a direct PDF URL yields the intended paper's PDF, retrieval succeeded. Treat metadata completion and verification as follow-up work after the PDF exists.

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

The core success condition is that the intended paper's PDF exists at `./papers/<dirname>/paper.pdf`. `metadata.json` should also exist by the end of the step, but failure of an earlier metadata resolver does not by itself negate successful retrieval if the correct PDF and final metadata are in place.

## Output

When done, report:
```
Retrieved: papers/<dirname>/paper.pdf
Source: [arxiv/aclanthology/unpaywall/sci-hub]
Size: [file size]
```

## Error Handling

- If fetch_paper.py fails metadata resolution: try the other source (arxiv vs S2)
- If metadata resolution or search yields a different paper than the intended one: stop and report the mismatch; do not continue with the wrong paper
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
