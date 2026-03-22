---
name: tag-papers
description: Add tags to papers that are missing them. Reads notes.md and description.md to pick 2-5 tags, preferring tags already in use. Run on a single paper directory or use --all for the entire collection.
argument-hint: "<papers/Author_Year_Title> or --all"
disable-model-invocation: false
---

# Tag Papers: $ARGUMENTS

Add tags to papers in the collection that don't have them yet.

## Step 0: Determine Mode

Parse `$ARGUMENTS`:

- If `--all`: list all paper directories and process each one
- Otherwise: treat as a single paper directory path

```bash
if [[ "$ARGUMENTS" == "--all" ]]; then
  ls -d papers/*/ | sort
else
  paper_dir="$ARGUMENTS"
fi
```

## Step 1: Gather Existing Tags

Read `papers/index.md` and extract all tags currently in use:

```bash
cat ./papers/index.md
```

Parse the `(tag1, tag2)` suffixes to build a list of existing tags and their frequencies. These are your preferred vocabulary — reuse existing tags when they fit rather than inventing synonyms.

Also read `papers/tags.yaml` if it exists:

```bash
cat ./papers/tags.yaml
```

This file is the **canonical tag vocabulary**. It lists all approved tags and their aliases. If it exists, you MUST use tags from this file. Do not invent new tags when an existing tag or its alias covers the topic.

If `tags.yaml` does not exist, fall back to the existing behavior of preferring tags already used in `index.md`.

## Step 2: Check Each Paper

For each paper directory, check if it already has tags.

Read `description.md` and check:
- Does it have YAML frontmatter with a `tags:` field? → **skip**
- Does it have a legacy `Tags:` line? → **skip**
- Does `description.md` not exist? → **skip** (run paper-reader first)
- Does `notes.md` not exist? → **skip** (run paper-reader first)

## Step 3: Read and Tag

Read the paper's `notes.md` and `description.md` to understand what it's about.

Pick 2-5 tags following these guidelines:

- **Lowercase, hyphenated**: `voice-quality`, not `Voice Quality`
- **MUST use tags from tags.yaml**: if a canonical tag fits, use it. If the paper's topic matches an alias listed in tags.yaml, use the canonical form instead.
- **Proposing new tags**: if no existing tag fits, you may propose a new one. List it in Step 6 as a proposed addition to tags.yaml. Use lowercase-hyphenated format.
- **Mix specificity**: one broad tag (`acoustics`, `perception`, `synthesis`) plus one or two narrow ones (`formant-transitions`, `lf-model`)
- **Tags describe the paper's topic**, not its method or venue
- **Don't over-tag**: 3 tags is usually right

## Step 4: Write Tags

Add YAML frontmatter with tags to `description.md`. Read the file first, then:

- **If no frontmatter exists**: prepend `---\ntags: [tag1, tag2, tag3]\n---\n` before the existing content
- **If frontmatter exists but no tags field**: add `tags: [tag1, tag2, tag3]` inside the existing frontmatter
- **If a legacy `Tags:` line exists at the end**: remove it and add frontmatter instead

Use your editing tools to modify the file cleanly.

Example result:
```markdown
---
tags: [acoustics, glottal-source, voice-quality]
---
This paper presents the LF model for parameterizing glottal flow...
```

## Step 5: Update index.md

Update the paper's line in `index.md` to include its new tags. Find the line starting with `- PaperDirName` and update it to `- PaperDirName  (tag1, tag2, tag3)`.

If the paper isn't in `index.md` yet, append it.

## Step 6: Report

Output a summary:

```
Tagged: N papers
Skipped: M papers (already tagged or missing notes)

New tags introduced:
  - new-tag-1 (used by: Paper1, Paper2)
  - new-tag-2 (used by: Paper3)

Existing tags reused:
  - acoustics (now N total papers)

Untagged papers remaining:
  - Paper_Without_Notes (missing notes.md)
```

For `--all` mode, also output the full tag frequency list:

```
Tag summary:
  acoustics: 5 papers
  voice-quality: 3 papers
  ...
```

If you introduced any tags NOT in tags.yaml, list them:

```
Proposed new tags (add to tags.yaml):
  - new-tag-name: "Brief description of what this tag covers"
```

After tagging, remind the user to run `generate-paper-index.py` to rebuild the `tagged-papers/` symlinks.

---

## Do NOT:

- Modify notes.md or any file other than description.md and index.md
- Re-read the PDF (notes.md has everything you need)
- Delete or rewrite existing description text (only add/modify frontmatter)
- Invent tags when an existing tag fits
