# Cross-LLM Skills Research Notes

## Goal
Research what's needed to make these skills usable by Claude, Codex, and Gemini.

## Findings

### Platform Comparison: SKILL.md Support

| Feature | Claude Code | Codex CLI | Gemini CLI |
|---------|------------|-----------|------------|
| File format | SKILL.md + YAML frontmatter | SKILL.md + YAML frontmatter | SKILL.md + YAML frontmatter |
| Required frontmatter | `name`, `description` (recommended) | `name`, `description` (required) | `name`, `description` (required) |
| Extra frontmatter | `argument-hint`, `disable-model-invocation`, `user-invocable`, `allowed-tools`, `model`, `context`, `agent`, `hooks` | None (use `agents/openai.yaml` for extras) | None |
| Skill directory | `.claude/skills/` | `.agents/skills/` | `.gemini/skills/` |
| User-level skills | `~/.claude/skills/` | `~/.agents/skills/` | `~/.gemini/skills/` |
| $ARGUMENTS | Yes | Not documented | Not documented |
| Subagent dispatch | `Task()` tool, `context: fork` | No built-in equivalent | No built-in equivalent |
| Skill chaining | `Skill()` tool | No equivalent | No equivalent |
| Unknown frontmatter | Ignored | Ignored | Ignored |
| Tool references | Named tools: Read, Write, Edit, Glob, Grep, Bash, WebSearch, WebFetch, Task, Skill | Shell commands | Shell commands |

### Key Insight: Convergence on Agent Skills Standard

All three platforms converge on the same base format (SKILL.md with name+description frontmatter).
Gemini and Codex explicitly ignore unknown frontmatter fields. The body is "just markdown" —
all three treat it as prompt instructions.

**Search results confirm:** "If you already have Claude Code Skills set up, you can reuse them
directly in Gemini CLI without modification."

### Claude-Specific Constructs in THIS Repo

1. **Skill() tool** — paper-process chains paper-retriever → paper-reader via `Skill(skill: "...")`
2. **Task() tool** — paper-reader dispatches parallel subagents: chunk readers, abstract extractor, citations extractor
3. **model: haiku** — paper-reader uses haiku for cheap extraction tasks
4. **allowed-tools** — make-skill restricts tools
5. **context: fork / agent:** — research skill runs in forked context
6. **$ARGUMENTS** — used everywhere
7. **Named tool references** — Read, Write, Edit, Glob, Grep, Bash, WebSearch, WebFetch throughout
8. **MCP tool references** — `mcp__claude-in-chrome__*` in paper-retriever
9. **disable-model-invocation** — in paper-process

### The Real Problem

Frontmatter compatibility is a non-issue (extra fields get ignored).
The problem is the **body content**:

- Instructions that say "Use the Task tool" or "Use the Skill tool" are meaningless to Codex/Gemini
- Instructions referencing specific tool names (Read, Write, Glob) are Claude-specific
- Subagent parallelism patterns (the foreman protocol for large papers) have no equivalent
- Model selection (haiku for cheap tasks) is Claude-specific

### Approaches Considered

**A. Platform-neutral instructions (rewrite bodies)**
- Replace "Use Read tool" → "Read the file"
- Replace "Use Task() to dispatch" → "Process this section" (loses parallelism)
- Pro: One skill works everywhere
- Con: Loses Claude's most powerful features (subagents, parallelism, tool restrictions)

**B. Conditional sections**
- Add "## For Claude Code" / "## For Codex" / "## For Gemini" sections
- Each LLM reads the relevant section
- Pro: Keeps Claude features, provides alternatives
- Con: Skills become 2-3x longer, maintenance burden, LLMs may read wrong section

**C. Platform adapters (build step)**
- Write a "source" skill in a neutral format
- Generate platform-specific SKILL.md files for each `.claude/`, `.agents/`, `.gemini/`
- Pro: Clean separation, each platform gets optimized version
- Con: Build tooling complexity, three things to maintain

**D. Write neutral + accept degradation (RECOMMENDED)**
- Keep `name` + `description` in frontmatter (universal)
- Add Claude-specific frontmatter (ignored by others, no harm)
- Write body instructions in natural language that any LLM understands
- For Claude-specific power features (subagents, parallelism), use phrasing like:
  "If you can dispatch parallel subagents, do so for each chunk. Otherwise, process sequentially."
- Accept that Codex/Gemini won't parallelize but will still complete the task
- Pro: Single source of truth, graceful degradation, no build step
- Con: Slightly less optimized for Claude (more verbose), Codex/Gemini won't get parallelism

### Infrastructure for Multi-Platform

1. **Symlinks**: `.agents/skills/ → .claude/skills/` and `.gemini/skills/ → .claude/skills/`
   - OR: canonical location + symlinks to all three
2. **Plugin structure**: Keep current plugin structure, add symlink setup to install script
3. **AGENTS.md**: Consider adding AGENTS.md alongside/instead of CLAUDE.md for the papers/ index

### $ARGUMENTS Support

- Claude Code: native `$ARGUMENTS` substitution + `$ARGUMENTS[N]` / `$N`
- Codex: YES — supports `$ARGUMENTS` and `$1...$9` (confirmed in docs)
- Gemini CLI: NO — skills activate via `activate_skill` tool, no argument substitution.
  Skills get injected as context alongside the user's request. The model sees the
  user's original message + skill instructions, but there's no `$ARGUMENTS` placeholder.
- This is a meaningful gap: Gemini skills are "expertise injection" not "parameterized commands"

### Agent Skills Open Standard (agentskills.io)

The official spec defines:
- Required: `name`, `description`
- Optional: `license`, `compatibility`, `metadata` (arbitrary k/v), `allowed-tools` (experimental)
- NO `$ARGUMENTS` in the spec — that's a platform extension
- NO `context`, `agent`, `model`, `disable-model-invocation` — all platform extensions
- Body: "no format restrictions, write whatever helps agents perform the task"
- Progressive disclosure: metadata loaded at startup, body loaded on activation, resources on demand
- Recommended body <500 lines, <5000 tokens

Claude Code explicitly states it follows this standard and extends it.
Codex follows it and extends it (with agents/openai.yaml).
Gemini follows it with minimal extensions.

### Severity Assessment of Each Claude-Specific Feature

| Feature | Used in | Severity for cross-LLM | Workaround |
|---------|---------|----------------------|------------|
| `$ARGUMENTS` | All skills | LOW — Codex supports it; Gemini gets user request as context anyway |  |
| `Skill()` chaining | paper-process | MEDIUM — rewrite as "follow these steps" natural language | Just describe the workflow |
| `Task()` subagents | paper-reader | HIGH — parallel chunk reading for >100pg papers has no equivalent | Accept sequential fallback |
| `model: haiku` | paper-reader | LOW — just don't specify model, use whatever's available | Remove model hint |
| Named tools (Read, Write) | All skills | LOW — Codex/Gemini understand "read the file", "write to file" | Use natural language |
| `context: fork` | research | LOW — just means "do this in isolation" — others do this naturally | Remove or leave (ignored) |
| `allowed-tools` | make-skill | LOW — in open standard as experimental; ignored if unsupported | Leave in frontmatter |
| `disable-model-invocation` | paper-process | LOW — Claude-specific invocation control, ignored by others | Leave in frontmatter |
| MCP tools | paper-retriever | MEDIUM — Chrome automation for sci-hub is Claude-ecosystem specific | Provide fallback instructions |

### Recommended Strategy

**Approach D (neutral body + Claude frontmatter extensions) with targeted rewrites:**

1. **Frontmatter**: Keep all Claude-specific fields. They're harmless — ignored by Codex/Gemini.
   Add `compatibility: "Works with Claude Code, Codex CLI, Gemini CLI"` per the open standard.

2. **Body rewrites** — three tiers:
   - **Easy** (research, make-skill, paper-retriever): Mostly natural language already.
     Replace `Read tool` → "read the file", `Write tool` → "write to file". Done.
   - **Medium** (paper-process, reconcile): Replace `Skill()` chaining with inline instructions
     or "invoke the paper-retriever workflow described in [skill]". For reconcile, it's already
     mostly bash + natural language.
   - **Hard** (paper-reader): The foreman protocol for >100pg papers is deeply tied to Task().
     Options: (a) write it as "if you can dispatch parallel workers, do so; otherwise read
     sequentially" or (b) accept this skill degrades to sequential on non-Claude platforms.

3. **Skill discovery**: Use symlinks OR a canonical skill location.
   Best option: keep skills in `plugins/research-papers/skills/` (current location),
   and have the install process create symlinks:
   - `.claude/skills/paper-reader/ → ../../plugins/research-papers/skills/paper-reader/`
   - `.agents/skills/paper-reader/ → ../../plugins/research-papers/skills/paper-reader/`
   - `.gemini/skills/paper-reader/ → ../../plugins/research-papers/skills/paper-reader/`

4. **Context files: the @AGENTS.md pattern**

   All three platforms support `@file.md` imports in their context files:
   - Codex reads `AGENTS.md` natively
   - Claude Code reads `CLAUDE.md`, supports `@path` imports
   - Gemini CLI reads `GEMINI.md`, supports `@file.md` imports (.md only)

   **Pattern**: Make `AGENTS.md` the canonical file. Create thin wrappers:

   ```
   papers/
   ├── AGENTS.md     # THE canonical content (paper index, etc.)
   ├── CLAUDE.md     # contains: @AGENTS.md
   └── GEMINI.md     # contains: @AGENTS.md
   ```

   One source of truth, three consumers. Works for any directory that needs
   a context file (project root, papers/, etc.).

   This also applies at the project root level — if the project has a
   root-level CLAUDE.md with project instructions, it can be restructured
   the same way.

### What NOT to Do

- Don't maintain three copies of each skill
- Don't add conditional sections ("If you're Claude...", "If you're Codex...")
  — LLMs might misread which section applies
- Don't strip Claude-specific frontmatter — it's harmless and valuable when Claude uses it
- Don't try to replicate Task() parallelism in other platforms — accept graceful degradation

---

## Precise Changelist

### Principle

Every instruction that currently says "use the X tool" becomes a natural-language instruction
that any agent can follow with whatever tools it has. Claude still gets its power features
via frontmatter (which others ignore). The body never names a Claude-specific tool — it
describes what to DO, and each agent figures out HOW.

### Infrastructure Changes

#### 1. Context files: @AGENTS.md pattern

**papers/AGENTS.md** — rename `papers/CLAUDE.md` → `papers/AGENTS.md`
**papers/CLAUDE.md** — new file, contents: `@AGENTS.md`
**papers/GEMINI.md** — new file, contents: `@AGENTS.md`

The generate-paper-claude-md.sh script needs updating to write to `papers/AGENTS.md`
instead of `papers/CLAUDE.md`.

Step 8 in paper-reader ("Update papers/CLAUDE.md") must change to "Update papers/AGENTS.md".

#### 2. Skill discovery symlinks

Add to README install instructions (or a setup script):
```bash
# For Codex
mkdir -p .agents/skills
ln -s ../../plugins/research-papers/skills/* .agents/skills/

# For Gemini
mkdir -p .gemini/skills
ln -s ../../plugins/research-papers/skills/* .gemini/skills/
```

Claude already discovers via the plugin system, no change needed there.

---

### Skill-by-Skill Changes

#### reconcile/SKILL.md — NO CHANGES NEEDED
Already platform-neutral. No tool-specific references. All bash + natural language.

#### research/SKILL.md — 3 changes

| Line | Current | Change to |
|------|---------|-----------|
| 24 | `Use WebSearch to find:` | `Search the web to find:` |
| 30 | `Use WebFetch to:` | `Fetch and read these pages to:` |
| 86 | `Read the file again with Read tool` | `Read the file again` |

Frontmatter (`context: fork`, `agent: general-purpose`): KEEP. Claude uses them.
Others ignore them. No harm.

#### make-skill/SKILL.md — 3 changes

| Line | Current | Change to |
|------|---------|-----------|
| 26 | `Read all matching prompt files using the Read tool.` | `Read all matching prompt files.` |
| 76 | `allowed-tools: Read, WebSearch, WebFetch, Glob, Grep` | `allowed-tools: Read, WebSearch, WebFetch, Glob, Grep` (KEEP — in open standard as experimental) |
| 116, 197 | `Read the file again with Read tool` | `Read the file again` |

#### paper-retriever/SKILL.md — 6 changes

| Line | Current | Change to |
|------|---------|-----------|
| 45-46 | `The Read tool CANNOT parse most arxiv PDFs... Instead, fetch metadata from the arxiv abstract page using WebFetch:` | `Most arxiv PDFs can't be parsed directly (often report "password-protected" falsely). Instead, fetch metadata from the arxiv abstract page:` |
| 49 | `WebFetch(url: "https://arxiv.org/abs/XXXX.XXXXX", prompt: "Extract: ...")` | `Fetch https://arxiv.org/abs/XXXX.XXXXX and extract: 1) Full paper title, 2) All author names, 3) Year of publication, 4) Venue/conference if mentioned, 5) Abstract text` |
| 62 | `Fetch metadata from the abstract page with WebFetch too.` | `Fetch metadata from the abstract page too.` |
| 69-95 | `mcp__claude-in-chrome__navigate`, `mcp__claude-in-chrome__form_input`, etc. | Rewrite as platform-neutral browser automation instructions (see below) |
| 159 | `Read the file again with Read tool` | `Read the file again` |

**The MCP/Chrome block (lines 69-95)** becomes Playwright MCP (universal across all three platforms):

```markdown
### Case C: Other URL or DOI (paywalled)

Use browser automation to navigate to sci-hub and download the PDF.

**Try browser tools in this order:**

#### Option 1: Playwright MCP (preferred — works on all platforms)

If Playwright MCP tools are available (`browser_navigate`, `browser_click`, etc.):

1. `browser_navigate` → `https://sci-hub.st/`
2. `browser_snapshot` → find the input field
3. `browser_type` → enter the URL/DOI in the search field
4. `browser_click` → the submit/open button
5. `browser_snapshot` → look for an iframe or embed with a PDF URL
6. If needed, `browser_evaluate` →
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

1. `mcp__claude-in-chrome__navigate` → `https://sci-hub.st/`
2. `mcp__claude-in-chrome__form_input` → enter the URL/DOI
3. `mcp__claude-in-chrome__computer` → click submit
4. `mcp__claude-in-chrome__javascript_tool` → extract PDF URL (same JS as above)
5. Download: `curl -L -o "./papers/temp_IDENTIFIER.pdf" "EXTRACTED_URL" 2>&1`

#### Option 3: No browser automation

Report the DOI/URL and ask the user to download the PDF manually to `./papers/`.
```

**Playwright MCP setup (add to README):**

All three platforms use the same `@playwright/mcp` server:

| Platform | Config file | Setup |
|----------|------------|-------|
| Claude Code | `claude mcp add` | `claude mcp add playwright -- npx @playwright/mcp@latest` |
| Codex CLI | `~/.codex/config.toml` | `[mcp_servers.playwright]`<br>`command = "npx"`<br>`args = ["@playwright/mcp@latest"]` |
| Gemini CLI | `~/.gemini/settings.json` | `{"mcpServers": {"playwright": {"command": "npx", "args": ["@playwright/mcp@latest"]}}}` |

#### paper-process/SKILL.md — 2 changes (medium)

| Line | Current | Change to |
|------|---------|-----------|
| 14-18 | `Use the Skill tool to invoke the paper-retriever skill:\n\nSkill(skill: "research-papers:paper-retriever", args: "$ARGUMENTS")` | `Invoke the **paper-retriever** skill with: $ARGUMENTS\n\nIf skill invocation is available (e.g., /research-papers:paper-retriever), use it. Otherwise, follow the paper-retriever SKILL.md instructions directly.` |
| 24-28 | `Use the Skill tool to invoke the paper-reader skill...\n\nSkill(skill: "research-papers:paper-reader", args: "...")` | `Invoke the **paper-reader** skill with the path from Step 1.\n\nIf skill invocation is available, use it. Otherwise, follow the paper-reader SKILL.md instructions directly.` |

#### paper-reader/SKILL.md — THE BIG ONE (11 changes)

**Category 1: Simple tool name references (4 changes)**

| Line | Current | Change to |
|------|---------|-----------|
| 146 | `Read the PDF directly with Read tool` | `Read the PDF directly` |
| 169 | `Read each page image sequentially using Read tool` | `Read each page image sequentially` |
| 231 | `Read each page image in your range using the Read tool.` | `Read each page image in your range.` |

**Category 2: Task() for gap-filling agents (lines 62-115) — 2 dispatch sites**

Current (line 62):
```
Task(subagent_type: general-purpose, model: haiku)
prompt: "Extract the abstract from this paper..."
```

Change to:
```
### Extract abstract

If you can dispatch a subagent, delegate this task:

> Extract the abstract from this paper and write abstract.md
> [rest of prompt unchanged]

Otherwise, do this yourself: read the first page and write abstract.md
following the format below.
```

Same pattern for the citations Task() at line 91.

**Category 3: Foreman protocol for >100pg papers (lines 177-293) — HARDEST**

Current: References `Task tool` to launch parallel chunk readers, each as a
subagent with a prompt. This is deeply Claude-specific.

Change to:
```markdown
## Step 2C: Large Paper Protocol (>100 pages)

For papers >100 pages, split into chunks and process each one.

### 2C.1-2C.3: [UNCHANGED — metadata extraction, directory creation, image conversion]

### 2C.4: Count Pages and Calculate Chunks
[UNCHANGED]

### 2C.5: Write Chunk Reader Prompt
[UNCHANGED — writing the template to ./prompts/ is agent-neutral]

### 2C.6: Process All Chunks

**If you can dispatch parallel subagents**, launch one per chunk simultaneously:
each subagent reads its page range and writes to
`./papers/Author_Year_ShortTitle/chunks/chunk-START-END.md`.

**If parallel dispatch is not available**, process each chunk sequentially:
for each chunk range, read the pages and write the chunk file yourself.

[Keep the prompt template as-is — it's just markdown instructions regardless
of whether a subagent or the main agent reads it]

### 2C.7-2C.9: [UNCHANGED — synthesis, already natural language]
```

**Category 4: Haiku model references for abstract/citations extraction (lines 456-596)**

Current (line 456-459):
```
Use Task tool with `model: haiku`:
Task(subagent_type: general-purpose, model: haiku)
```

Change to:
```
If you can dispatch a subagent for this extraction, do so (use a fast/cheap
model if available). Otherwise, do it yourself.
```

Apply this pattern at lines 456, 459, 517, 520, 591, 596.

**Category 5: Step 7.5 reconcile invocation (line 556-557)**

Current:
```
/research-papers:reconcile papers/FirstAuthor_Year_ShortTitle
```

This is already a slash-command invocation, which is fairly neutral.
Change to:
```
Invoke the **reconcile** skill on `papers/FirstAuthor_Year_ShortTitle`.
If skill invocation is available (e.g., /research-papers:reconcile), use it.
Otherwise, follow the reconcile SKILL.md instructions directly.
```

**Category 6: Step 8 CLAUDE.md → AGENTS.md (line 569-578)**

Change all references from `papers/CLAUDE.md` to `papers/AGENTS.md`.

---

### Summary: Total Changes

| Skill | Changes | Difficulty |
|-------|---------|-----------|
| reconcile | 0 | Done |
| research | 3 word-level edits | Trivial |
| make-skill | 3 word-level edits | Trivial |
| paper-retriever | 6 edits (incl. MCP rewrite) | Medium |
| paper-process | 2 block rewrites | Easy |
| paper-reader | 11 edits (incl. foreman rewrite) | Medium-Hard |
| Infrastructure | 3 new files + script update + README | Easy |
| **Total** | ~25 edits + 3 new files | Half day of work |

### What Claude Keeps (via frontmatter, untouched)

- `context: fork` — Claude runs research in a subagent
- `agent: general-purpose` — Claude picks the right agent type
- `disable-model-invocation: true` — Claude won't auto-trigger paper-process
- `allowed-tools` — Claude restricts make-skill to read-only tools
- `argument-hint` — Claude shows autocomplete hints
- `$ARGUMENTS` — Claude and Codex do substitution; Gemini sees user's message directly

### What Degrades Gracefully on Non-Claude

- Parallel chunk processing → sequential (still works, just slower)
- Cheap model for extraction → uses whatever model the agent has
- Skill chaining → manual "follow these instructions" (still works)
- Tool restrictions → ignored (agent uses whatever it has)

### What Works Identically on All Three

- All bash commands (curl, magick, mkdir, etc.)
- Playwright MCP browser automation (same server, same tool names)
- File reading/writing (all agents can do this)
- Web search (all agents have some web access)
- $ARGUMENTS substitution (Claude + Codex; Gemini gets user message as context)

---

# Auto-Tagging Research: Keyword Extraction Without AI/LLM Calls

## Goal

Find lightweight Python methods to suggest 2-5 topical tags per paper from its
notes.md (sections: Summary, Key Contributions, Methodology, Key Equations,
Parameters, etc.). No LLM calls, no heavy deps (no spacy, no torch, no
transformers).

## Approaches Investigated

### 1. TF-IDF (scikit-learn)

**Library:** `scikit-learn` (`pip install scikit-learn`)
**Deps:** numpy, scipy, joblib. Medium footprint but widely installed already.

**How it works:** Term Frequency-Inverse Document Frequency scores words by how
frequent they are in one document vs. how rare they are across the whole corpus.
Words that appear a lot in one paper but rarely across papers get high scores.

**Corpus mode:** YES — this is TF-IDF's strength. You fit the vectorizer on ALL
paper notes.md files, then for each paper extract the top-N highest-scoring
terms. A paper about "glottal source modeling" will surface domain-specific terms
because they're rare across the collection.

**Code example:**

```python
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

# docs = list of all notes.md contents
# names = list of paper directory names
vectorizer = TfidfVectorizer(
    stop_words='english',
    max_df=0.85,       # ignore words in >85% of docs
    ngram_range=(1, 2), # unigrams + bigrams
    min_df=1,
)
tfidf_matrix = vectorizer.fit_transform(docs)
feature_names = vectorizer.get_feature_names_out()

def get_top_keywords(doc_index, n=5):
    row = tfidf_matrix[doc_index].toarray().flatten()
    top_indices = row.argsort()[-n:][::-1]
    return [(feature_names[i], row[i]) for i in top_indices if row[i] > 0]

# Per paper:
for i, name in enumerate(names):
    print(f"{name}: {get_top_keywords(i)}")
```

**Strengths for our use case:**
- Naturally surfaces domain-specific technical terms
- Works BETTER with more papers (IDF gets more meaningful)
- Bigrams catch phrases like "voice quality", "formant transition"
- `max_df` filters out terms common to ALL papers (e.g. "paper", "model")

**Weaknesses:**
- Raw terms need normalization to become tags (e.g. "glottal" -> "glottal-source")
- Single words may be too granular; bigrams can be noisy
- Needs the whole corpus at once (re-fit when adding papers, or use incremental)

**Scientific text performance:** Good. TF-IDF was designed for document retrieval
and performs well on technical text where domain-specific vocabulary naturally
differentiates documents.

---

### 2. RAKE (Rapid Automatic Keyword Extraction)

**Library:** `rake-nltk` (`pip install rake-nltk`)
**Deps:** NLTK (+ `nltk.download('stopwords')` one-time download, ~30KB)

**How it works:** Splits text at stopwords and punctuation to find candidate
phrases, scores them by word degree (co-occurrence) divided by word frequency.
Phrases with rare words that co-occur with many other words score high.

**Corpus mode:** NO — single-document only. Each document is scored independently.
No concept of "this word is rare across the collection."

**Code example:**

```python
from rake_nltk import Rake

r = Rake(
    min_length=1,      # min words in phrase
    max_length=3,      # max words in phrase
)

r.extract_keywords_from_text(notes_text)
# Returns phrases ranked by score (highest = most keyword-like)
phrases = r.get_ranked_phrases_with_scores()
for score, phrase in phrases[:10]:
    print(f"  {score:.1f}  {phrase}")
```

**Strengths:**
- Very fast (processes 2000 docs in ~2 seconds)
- Domain-independent — no training needed
- Good at multi-word phrases ("voice onset time", "linear prediction")
- Catches phrases with interior stopwords ("rate of change")

**Weaknesses:**
- No corpus awareness — can't distinguish "common across all papers" from
  "unique to this paper"
- Tends to produce long, overly specific phrases
- Scores are not comparable across documents
- Scientific text often has many technical noun phrases that all score similarly

**Scientific text performance:** Decent but noisy. Produces many candidate
phrases; needs post-filtering. The lack of corpus context means it can't tell
that "acoustic" is generic (appears in every paper) vs. "cepstral" is specific.

---

### 3. YAKE (Yet Another Keyword Extractor)

**Library:** `yake` (`pip install yake`)
**Deps:** jellyfish, segtok, regex, numpy, networkx. Moderate footprint.

**How it works:** Statistical approach using 5 features per term: Casing, Word
Position, Word Frequency, Word Relatedness to Context, Word DifSentence (how
many different sentences the word appears in). Lower score = more important
keyword. Also supports deduplication (Levenshtein, Jaro, sequence matching).

**Corpus mode:** NO — single-document only. But considers word position and
sentence distribution within the document, which is more sophisticated than RAKE.

**Code example:**

```python
import yake

kw_extractor = yake.KeywordExtractor(
    lan="en",
    n=2,              # max ngram size
    dedupLim=0.9,     # deduplication threshold
    dedupFunc='seqm', # sequence matching for dedup
    top=10,
)

keywords = kw_extractor.extract_keywords(notes_text)
for kw, score in keywords:
    print(f"  {score:.4f}  {kw}")
# NOTE: lower score = MORE important (inverse of RAKE)
```

**Strengths:**
- Best accuracy among unsupervised single-doc methods (benchmarked on 20 datasets)
- Handles scientific text well — tested on research papers
- Built-in deduplication (won't return both "glottal" and "glottal source")
- No training, no external corpus, no dictionaries needed
- Works on any text length (tweets to full papers)

**Weaknesses:**
- No corpus mode — same limitation as RAKE
- networkx + numpy dependencies add some weight
- Score interpretation is inverted (lower = better), can confuse

**Scientific text performance:** Best of the single-document methods. The
original YAKE paper evaluates on scientific corpora and outperforms RAKE, TF-IDF
(single-doc variant), and TextRank across multiple benchmarks.

---

### 4. Noun Phrase Extraction (TextBlob / NLTK)

**Library:** `textblob` (`pip install textblob`) or raw `nltk`
**Deps:** NLTK. TextBlob is a thin wrapper. Need `nltk.download('averaged_perceptron_tagger_eng')`.

**How it works:** POS-tags the text, then applies grammar rules to extract noun
phrases (sequences matching patterns like `JJ* NN+` — adjectives followed by
nouns).

**Corpus mode:** NO — just structural extraction, no scoring.

**Code example:**

```python
from textblob import TextBlob

blob = TextBlob(notes_text)
noun_phrases = blob.noun_phrases  # list of strings
# Returns things like: ['voice quality', 'fundamental frequency',
#                        'glottal flow', 'spectral tilt']

# Or with NLTK directly:
import nltk
tokens = nltk.word_tokenize(notes_text)
tagged = nltk.pos_tag(tokens)
grammar = "NP: {<JJ>*<NN.*>+}"
parser = nltk.RegexpParser(grammar)
tree = parser.parse(tagged)
nps = [" ".join(w for w, t in subtree.leaves())
       for subtree in tree.subtrees() if subtree.label() == 'NP']
```

**Strengths:**
- Extracts actual noun phrases — structurally valid tag candidates
- Good for scientific text (lots of noun phrases like "spectral envelope")
- Can be combined with TF-IDF: extract NPs, then rank by TF-IDF score

**Weaknesses:**
- No ranking — returns ALL noun phrases (could be hundreds)
- POS tagging accuracy on technical text is imperfect
- Need a separate scoring step to pick the best 2-5

**Scientific text performance:** Good at finding candidates, bad at ranking them.
Best used as a candidate generator fed into TF-IDF or frequency scoring.

---

### 5. Other Lightweight Options Considered

**PKE (Python Keyphrase Extraction):** Implements TextRank, TopicRank, YAKE, and
more. BUT requires spacy + language models. **REJECTED — violates no-spacy
constraint.**

**KeyBERT:** Best accuracy overall, but requires sentence-transformers/BERT.
There's a lightweight mode with `model2vec` instead of PyTorch, but still pulls
in significant deps. **REJECTED — too heavy.**

**Gensim TextRank:** Gensim's `summarize` module was removed in v4+. Would need
an older version. **REJECTED — deprecated.**

**phrasemachine:** NLTK-based, extracts multi-word phrases via POS patterns.
Similar to NLTK RegexpParser approach above. Lightweight but unmaintained.

---

## Corpus vs. Single-Document Comparison

| Method | Single-doc | Corpus-aware | Best for |
|--------|-----------|-------------|----------|
| TF-IDF (sklearn) | Yes (degenerate) | **YES** | Finding what's unique to THIS paper |
| RAKE | Yes | No | Fast candidate generation |
| YAKE | Yes | No | Best single-doc accuracy |
| Noun phrases | Yes | No | Candidate generation |

---

## Using Existing Tag Vocabulary as Priors/Seeds

This is the key question: can we bias extraction toward reusing existing tags
like `acoustics`, `voice-quality`, `glottal-source`?

### Approach A: Post-extraction matching (simplest)

1. Extract candidate keywords/phrases using any method above
2. Fuzzy-match each candidate against the existing tag list
3. If a candidate matches an existing tag, boost its rank / prefer it

```python
from difflib import SequenceMatcher

def match_to_existing_tags(candidates, existing_tags, threshold=0.6):
    matched = []
    novel = []
    for candidate in candidates:
        best_match = max(existing_tags,
                        key=lambda t: SequenceMatcher(None, candidate, t).ratio())
        score = SequenceMatcher(None, candidate, best_match).ratio()
        if score >= threshold:
            matched.append((best_match, score))
        else:
            novel.append(candidate)
    return matched, novel
```

This is entirely model-free. `difflib` is in the standard library.

### Approach B: TF-IDF vocabulary restriction

Force the TF-IDF vectorizer to only consider terms that appear in existing tags:

```python
# Build vocabulary from existing tags
tag_terms = set()
for tag in existing_tags:
    tag_terms.update(tag.replace('-', ' ').split())

vectorizer = TfidfVectorizer(vocabulary=tag_terms, ...)
```

This won't discover NEW tags but will reliably score which existing tags fit each
paper. Good for backfilling tags on untagged papers in an established collection.

### Approach C: Two-pass hybrid (RECOMMENDED)

1. **Pass 1 — Existing tags:** TF-IDF with vocabulary restricted to existing tag
   terms. Score how well each existing tag fits. Accept matches above threshold.
2. **Pass 2 — New discovery:** YAKE or unrestricted TF-IDF on the full text.
   Extract candidates NOT already covered by pass 1. These become suggested new
   tags (human approval needed).

```python
def suggest_tags(notes_text, all_docs, existing_tags, n_tags=4):
    # Pass 1: match existing tags
    tag_vocab = set()
    for tag in existing_tags:
        tag_vocab.update(tag.replace('-', ' ').split())

    restricted = TfidfVectorizer(vocabulary=list(tag_vocab), stop_words='english')
    restricted.fit(all_docs)
    scores = restricted.transform([notes_text]).toarray().flatten()
    features = restricted.get_feature_names_out()

    # Map scored terms back to full tags
    matched_tags = []
    for tag in existing_tags:
        tag_words = tag.replace('-', ' ').split()
        tag_score = sum(scores[list(features).index(w)]
                        for w in tag_words if w in features) / len(tag_words)
        if tag_score > 0.05:
            matched_tags.append((tag, tag_score))
    matched_tags.sort(key=lambda x: -x[1])

    # Pass 2: discover novel terms with YAKE
    import yake
    kw = yake.KeywordExtractor(n=2, top=20)
    candidates = kw.extract_keywords(notes_text)
    novel = [(phrase, score) for phrase, score in candidates
             if not any(phrase in tag for tag in existing_tags)]

    # Combine: prefer existing tags, fill remaining slots with novel
    result = [tag for tag, _ in matched_tags[:n_tags]]
    for phrase, _ in novel:
        if len(result) >= n_tags:
            break
        slug = phrase.lower().replace(' ', '-')
        if slug not in result:
            result.append(slug)
    return result
```

### Approach D: Embedding similarity (lightweight variant)

If we ever relax the "no models" constraint slightly, `model2vec` provides
distilled static embeddings (~30MB, no torch) that can compute cosine similarity
between a document and each existing tag. But this crosses the "no model" line.

---

## Recommendation

**For the tag-papers skill (automated, no LLM):**

Use the **two-pass hybrid** (Approach C above):

1. **Dependencies:** `scikit-learn` + `yake` (+ `rake-nltk` optionally for
   extra candidates). Total new deps: yake, jellyfish, segtok, networkx.
   scikit-learn is likely already available.

2. **Corpus TF-IDF** across all paper notes.md files surfaces what's unique to
   each paper. Restricted vocabulary mode matches existing tags.

3. **YAKE** on individual documents catches well-formed keyphrases that TF-IDF
   (which works on individual terms) might miss.

4. **Fuzzy matching** (stdlib `difflib`) maps extracted phrases to existing tags,
   preventing synonym proliferation ("voice-quality" vs "vocal-quality").

5. **Novel tag suggestions** from YAKE fill remaining slots when fewer than 2
   existing tags match, with human approval.

**What this looks like in practice:**

```
Paper: Fant_1995_GlottalSource
  Existing tags matched: glottal-source (0.42), voice-quality (0.18)
  Novel suggestions: lf-model, source-filter
  Final tags: [glottal-source, voice-quality, lf-model]

Paper: Stevens_1998_AcousticPhonetics
  Existing tags matched: acoustics (0.55), phonetics (0.31), formants (0.22)
  Novel suggestions: quantal-theory
  Final tags: [acoustics, phonetics, formants]
```

**Implementation complexity:** ~100 lines of Python. Could live in a standalone
script (`scripts/suggest-tags.py`) called by the tag-papers skill, or be
integrated directly into a Python-based tagging workflow.

---

## Dependency Summary

| Library | pip install | Key deps | Size | Purpose |
|---------|-----------|----------|------|---------|
| scikit-learn | `pip install scikit-learn` | numpy, scipy | ~30MB | TF-IDF corpus analysis |
| yake | `pip install yake` | jellyfish, segtok, networkx, numpy | ~5MB | Single-doc keyword extraction |
| rake-nltk | `pip install rake-nltk` | nltk | ~2MB (+stopwords) | Fast candidate generation |
| textblob | `pip install textblob` | nltk | ~2MB (+models) | Noun phrase extraction |
| difflib | stdlib | none | 0 | Fuzzy string matching |

Minimal viable: `scikit-learn` + `yake` + `difflib` (stdlib).
Add `rake-nltk` for extra candidate diversity. Skip `textblob` unless noun
phrase structure is specifically needed.
