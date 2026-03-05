---
name: reconcile
description: Cross-reference a paper against the collection. Finds which cited papers are already collected, which are new leads, which collection papers cite this one, and reconciles all cross-references bidirectionally. Run on a single paper directory or use --all for the entire collection.
argument-hint: <papers/Author_Year_Title> or --all
disable-model-invocation: false
---

# Reconcile: $ARGUMENTS

Cross-reference a paper (or all papers) against the collection, ensuring every citation link is bidirectional and accurate.

## Step 0: Determine Mode

Parse `$ARGUMENTS`:

- If `--all`: list all paper directories and process each one sequentially (Step 1 onward, looping)
- Otherwise: treat as a single paper directory path

```bash
if [[ "$ARGUMENTS" == "--all" ]]; then
  ls -d papers/*/ | grep -v "papers/pngs" | sort
  # Process each directory through Steps 1-5
else
  paper_dir="$ARGUMENTS"
fi
```

## Step 1: Validate Paper Directory

```bash
ls "$paper_dir"/notes.md "$paper_dir"/citations.md 2>/dev/null
```

**Required files:**
- `notes.md` — must exist (contains the cross-references section we'll update)
- `citations.md` — must exist (contains the reference list we cross-reference from)

If either is missing, report and skip this paper:
```
SKIP: papers/[dirname]/ — missing [notes.md|citations.md], run paper-reader first
```

**Also check:** Does `notes.md` already have a `## Collection Cross-References` section?
- If yes: this paper has been reconciled before. Read the existing section to understand current state, then update it.
- If no: this is a first-time reconciliation. Create the section from scratch.

---

## Step 2: Forward Cross-Referencing (This Paper Cites → Collection)

Check which papers cited by this one are already in the collection.

### 2.1: Extract Citation Keys

Read `citations.md` — focus on both the full Reference List and the Key Citations for Follow-up section. Extract author last names and years for the key citations.

### 2.2: Search Collection Index

For each key citation, grep `papers/AGENTS.md` for the author's last name:

```bash
grep -c "AuthorName" ./papers/AGENTS.md
```

If found, identify the exact directory name from the AGENTS.md heading.

### 2.3: Write/Update Forward Cross-References

In `notes.md`, write or update the `## Collection Cross-References` section:

```markdown
## Collection Cross-References

### Already in Collection
- **AuthorA_Year_ShortTitle** — cited for [reason from citations.md context]

### New Leads (Not Yet in Collection)
- AuthorB (Year) — "Paper title" — relevant for [reason]

### Supersedes or Recontextualizes
- [If this paper extends/corrects/supersedes an existing collection paper, note it here]
- [Only genuine relationships — not every citation]

### Conceptual Links (not citation-based)
- **PaperC_Year_Title** — [specific topical connection: what claim/finding/method links these papers]
```

### 2.4: Backward Annotation (Supersedes Only)

If the "Supersedes or Recontextualizes" section is non-empty, append a see-also note to each affected paper's notes.md:

```bash
echo "" >> ./papers/AffectedPaper_Dir/notes.md
echo "---" >> ./papers/AffectedPaper_Dir/notes.md
echo "" >> ./papers/AffectedPaper_Dir/notes.md
echo "**See also:** NewPaper_Dir - [relationship description]" >> ./papers/AffectedPaper_Dir/notes.md
```

**Check first** whether a see-also note already exists (to avoid duplicates):
```bash
grep -c "NewPaper_Dir" ./papers/AffectedPaper_Dir/notes.md
```

---

## Step 3: Reverse Citation Search (Collection Cites → This Paper)

Find papers in the collection that reference this paper.

### 3.1: Extract Search Keys

From the paper's `notes.md`, extract the first author's last name and year. Build a grep pattern:

```bash
# Search all collection markdown files for references to this paper
# Exclude the paper's own directory to avoid self-matches
grep -rl "AuthorLastName.*Year" ./papers/ --include="*.md" | grep -v "papers/AuthorLastName_Year_ShortTitle/"
```

Also try the directory name pattern:
```bash
grep -rl "AuthorLastName_Year" ./papers/ --include="*.md" | grep -v "papers/AuthorLastName_Year_ShortTitle/"
```

### 3.2: Add "Cited By" Section

If any collection papers cite this one, add or update a "Cited By" subsection in the Collection Cross-References:

```markdown
### Cited By (in Collection)
- **CitingPaper_Year_ShortTitle** — cites this for [aspect, determined in Step 4]
```

If no papers cite this one, either omit the section or write:
```markdown
### Cited By (in Collection)
- (none found)
```

---

## Step 4: Conceptual Links (Topic-Based, Not Citation-Based)

Steps 2–3 find explicit citation links. This step finds **conceptual connections**: collection papers that address the same problems, whose findings interact with this paper's claims, or whose methods complement or contradict this paper — regardless of whether any citation relationship exists.

This is what makes the collection a knowledge graph, not just a citation graph. **This step is not optional.** Citation-based cross-referencing alone misses the most valuable connections: papers from different research traditions that converge on the same empirical observation, or later papers that provide mechanisms for earlier observations.

### 4.1: Identify Key Claims and Topics

Read this paper's notes.md and extract the 3–6 most important claims, methods, or findings. These are the search axes.

**What to extract — be specific about the phenomenon, not just the topic:**
- A specific empirical observation (e.g., "formant transitions hold at 65ms while steady states stretch 1.5x")
- A model or framework (e.g., "multi-stream parallel representation with synchronized tiers")
- A mechanism or explanation (e.g., "aspiration overlays the CV transition as an independent stream")
- A critique of another approach (e.g., "linear phoneme models conflate phonological and phonetic units")
- An open problem the paper identifies (e.g., "minimum/maximum duration constraints not specified")

### 4.2: Search Collection for Topic Matches

For each claim/topic, think about what kinds of papers would connect:

**Same phenomenon, different framework:**
- Does another tradition (articulatory phonology, acoustic phonetics, perceptual studies) observe the same thing this paper describes? Search for the phenomenon's acoustic/articulatory/perceptual terms.
- Example: "stable transition duration" → search for "stiffness", "gesture duration", "transition.*ms", "formant transition"

**Mechanism for observation (or observation for mechanism):**
- Does this paper observe something that another paper explains, or vice versa?
- Example: paper observes "only steady states lengthen" → search for "boundary lengthening", "phrase-final", "π-gesture", "prosodic.*slowing"

**Data that grounds or challenges claims:**
- Does another paper provide the empirical measurements this paper's model requires?
- Does another paper's data contradict this paper's predictions?

**Cross-level connections:**
- Articulatory ↔ Acoustic ↔ Perceptual papers often address the same phenomenon at different levels of description

Use targeted grep searches across `papers/*/notes.md`:
```bash
# Search for papers discussing the same phenomenon
grep -rl "relevant_term" ./papers/ --include="notes.md" | grep -v "papers/ThisPaper/"
```

Read matching sections (not full files) to assess connection strength.

### 4.3: Classify Connection Strength

For each match, classify as:
- **Strong** — directly addresses the same problem, provides data this paper uses, contradicts/confirms a key finding, or provides a mechanism for this paper's observations (or vice versa). Different formalisms converging on the same empirical fact is always Strong.
- **Moderate** — related methodology or overlapping problem space, but not directly interacting
- **Weak** — tangential overlap; omit from cross-references

Only surface **Strong** and **Moderate** connections. Weak connections create noise.

### 4.4: Write Conceptual Links Section

Add a `### Conceptual Links (not citation-based)` subsection to the Collection Cross-References:

```markdown
### Conceptual Links (not citation-based)
- **PaperA_Year_Title** — [specific connection: what claim/finding/method connects these papers and how they relate — convergence, tension, mechanism↔observation, etc.]
- **PaperB_Year_Title** — [specific connection]
```

Each entry must state the **specific relationship**, not just "related to duration modeling." Good: "Hertz's 'stable transition phenomenon' (CV transitions hold at ~65ms while steady states stretch) is exactly what AP predicts for a high-stiffness gesture — different formalisms, same empirical convergence." Bad: "Also about formant transitions."

Group entries by theme when there are 3+ connections (use bold subheadings like `**Duration modeling:**`).

### 4.5: Bidirectional Annotation

For **Strong** connections, check if the connected paper's notes.md already mentions this paper:
- If not, add a reciprocal entry in that paper's `### Conceptual Links (not citation-based)` section (create the subsection if needed)
- Check for duplicates before writing

For **Moderate** connections, only annotate this paper (not the connected paper) — the connected paper's own reconciliation pass will pick it up if the connection is genuinely bidirectional.

---

## Step 5: Reconcile Citing Papers

For each paper found in Step 3, **read its notes.md** (specifically the Collection Cross-References, Related Work, and Open Questions sections). Check for and fix:

### 5.1: Leads Listing This Paper

If the citing paper lists this paper under "New Leads (Not Yet in Collection)":

- **Move** the entry out of "New Leads"
- **Add** a new subsection `### Now in Collection (previously listed as leads)` (if it doesn't exist)
- **Write** the entry there with:
  - Correct description of what this paper actually contributes
  - Key finding summary
  - Any tensions or confirmations between the two papers' findings

Example:
```markdown
### Now in Collection (previously listed as leads)
- **Feinberg_2008_FemininityAveragenessVoicePitch** — F0 manipulation via PSOLA shows linear pitch–attractiveness relationship. Note: Babel found opposite F0 effect when controlling for breathiness.
```

### 5.2: Inaccurate Descriptions

If the citing paper describes this paper inaccurately (wrong method, wrong finding, wrong scope):
- **Edit** the description inline to be correct
- Common errors: confusing which variables were manipulated, attributing findings from a different paper by the same author group

### 5.3: Open Questions Answered

If the citing paper has open questions (`## Open Questions`) that this paper addresses:
- **Annotate** the question: append `[Addressed by Author_Year_ShortTitle — finding summary]`
- Do NOT check the box — that's for the user to decide

### 5.4: Interesting Tensions

If the new paper's findings conflict with or nuance the citing paper's conclusions:
- **Document in the citing paper's notes** (in the cross-references section or as an inline note)
- **Document in this paper's notes** (in the cross-references section)
- Be specific: what differs, why (different methodology? different controls? different population?)

---

## Step 6: Report

Output a summary:

```
Reconciled: papers/[dirname]/
  Forward: N already in collection, M new leads, K supersedes
  Reverse: J collection papers cite this one
  Conceptual: S topic-based connections surfaced (T strong, U moderate)
  Updated:
    - papers/CitingPaper1/ — moved lead to "Now in Collection", corrected description
    - papers/CitingPaper2/ — added to "Already in Collection"
    - papers/AffectedPaper/ — added see-also backward annotation
    - papers/ConnectedPaper/ — added conceptual link (bidirectional)
  Tensions found:
    - [brief description of any finding conflicts, or "none"]
```

For `--all` mode, output a final summary after all papers are processed:

```
Reconciliation complete: X papers processed
  - Y papers had citing papers in collection
  - Z leads marked as fulfilled
  - S conceptual links surfaced
  - W tensions documented
  - V papers skipped (missing notes.md or citations.md)
```

---

## The Reconciliation Principle

After reconciliation, every cross-reference in the collection should be **bidirectional and accurate**:

1. If Paper A cites Paper B, and both are in the collection:
   - A's notes mention B in "Already in Collection" (with correct description)
   - B's notes mention A in "Cited By (in Collection)"

2. If Paper A was listed as a "New Lead" in Paper B, and A is now in the collection:
   - The lead entry is moved to "Now in Collection" with accurate summary
   - Any inaccurate description from when the lead was first noted is corrected

3. If Paper A supersedes/extends Paper B:
   - A's notes say so in "Supersedes or Recontextualizes"
   - B's notes have a "See also" annotation pointing to A

4. If Papers A and B have conflicting findings:
   - Both papers' notes document the tension with specifics

5. If Papers A and B address the same problem or their findings substantively interact (even without citation):
   - At least one paper's notes mention the other in "Conceptual Links (not citation-based)"
   - Strong connections are annotated bidirectionally; moderate connections at minimum on the paper being reconciled

---

## Running on All Papers

When invoked with `--all`, process papers in alphabetical order. For each paper:

1. Run Steps 1-6
2. **Do not re-read papers that were already updated as citing papers** — their own turn will come in the alphabetical sweep
3. Be idempotent: running `--all` twice should produce the same result (no duplicate annotations)

### Idempotency Checks

Before every write operation, check if the content already exists:
- Before adding "Cited By" entry: `grep -c "PaperDirName" notes.md`
- Before adding "See also": `grep -c "PaperDirName" affected_notes.md`
- Before moving a lead: check if "Now in Collection" subsection already lists it

---

## Do NOT:
- Create or modify `papers/AGENTS.md` entries (that's paper-reader's job)
- Delete or overwrite existing notes content (only append/update cross-reference sections)
- Modify the paper's core notes sections (Summary, Parameters, Equations, etc.)
- Output full notes content to conversation (just the reconciliation summary)
