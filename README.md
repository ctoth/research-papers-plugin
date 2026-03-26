# research-papers

A plugin for managing annotated research paper collections. Works with Claude Code, Codex CLI, and Gemini CLI.

## What it does

This plugin provides skills for retrieving, reading, and annotating scientific papers into a structured, cross-referenced collection. Each paper gets:

- **notes.md** — Implementation-focused extraction (equations, parameters, algorithms)
- **description.md** — Three-sentence summary
- **abstract.md** — Verbatim abstract + interpretation
- **citations.md** — Full reference list + key citations for follow-up
- **papers/index.md** — Auto-generated list of paper directories in the collection

## Skills

| Skill | Description |
|-------|-------------|
| `paper-retriever` | Download a paper PDF from arxiv, DOI, ACL Anthology, or sci-hub |
| `paper-reader` | Read a paper and extract structured notes (handles small/medium/large papers) |
| `paper-process` | Combined retrieve + read in one step |
| `lint-paper` | Audit paper directories for completeness and format compliance |
| `reconcile` | Cross-reference a paper against the collection bidirectionally |
| `tag-papers` | Add tags to untagged papers using their existing notes |
| `research` | Web research on a topic, structured findings report |
| `extract-claims` | Extract/enrich propositional claims from a paper into claims.yaml |
| `make-skill` | Create new skills from prompt files |

## Scripts

| Script | Description |
|--------|-------------|
| `lint_skill_frontmatter.py` | Parse every `SKILL.md` frontmatter block and fail on invalid YAML |
| `generate-paper-index.py` | Rebuild papers/index.md and tagged-papers/ symlinks |
| `cross-reference-papers.py` | Find cross-references between papers in the collection |
| `migrate-format.py` | Convert legacy Tags: lines → YAML frontmatter, bold refs → wikilinks |
| `generate_claims.py` | Parse notes.md and generate claims.yaml for a single paper |
| `batch_generate_claims.py` | Generate claims.yaml for all papers in a directory |
| `bootstrap_concepts.py` | Deduplicate and group concept names from claims files |

## Claims Extraction Pipeline

The claims pipeline extracts machine-readable propositional claims from paper notes. The typical workflow:

1. **`generate_claims.py`** — Parses `notes.md` (parameter tables, equations, key findings) and produces a draft `claims.yaml` marked with `stage: draft`. Fast, deterministic, no LLM needed.
2. **`extract-claims` skill** — LLM-powered enrichment of the draft claims (adds context, fixes types, fills gaps). Can also create claims from scratch if no draft exists.
3. **`batch_generate_claims.py`** — Runs step 1 across an entire papers directory. Use `--skip-existing` to avoid re-processing.
4. **`bootstrap_concepts.py`** — Collects concept names from all claims files, deduplicates similar names, and outputs a unified concepts list.

```bash
# Single paper: generate draft, then enrich with LLM
uv run scripts/generate_claims.py papers/Author_2024_Title
$extract-claims papers/Author_2024_Title

# Batch: generate drafts for all papers missing claims.yaml
uv run scripts/batch_generate_claims.py papers/ --skip-existing

# After batch: deduplicate concepts across all claims
uv run scripts/bootstrap_concepts.py papers/ --output concepts.yaml
```

## Installation

Clone the repo, then run one installer command:

```bash
uv run scripts/install_skills.py install
```

That does three things:

- discovers all skill directories under `plugins/*/skills/*` for Codex and Gemini
- discovers the Claude marketplace manifest at `.claude-plugin/marketplace.json`
- installs everything at user scope

For Claude Code specifically, the installer now prefers the native CLI path:

```bash
claude plugin marketplace add <this-repo> --scope user
claude plugin install research-papers@research-papers-marketplace --scope user
```

The Python installer runs that for you. It does not install Claude by writing directly into a Claude skills directory.

Useful variants:

```bash
uv run scripts/install_skills.py doctor
uv run scripts/lint_skill_frontmatter.py
uv run scripts/install_skills.py install --platform codex
uv run scripts/install_skills.py install --platform claude
uv run scripts/install_skills.py uninstall
```

For Codex and Gemini, the installer prefers whole-directory symlinks and falls back to copying if symlinks are unavailable.

### Project setup

Your project needs this structure:

```
your-project/
├── papers/
│   ├── index.md     # Paper listing with tags (auto-generated)
│   ├── tagged/       # Symlinks organized by tag (auto-generated)
│   │   ├── acoustics/
│   │   │   └── Fant_1985_LFModel -> ../../Fant_1985_LFModel
│   │   └── voice-quality/
├── reports/          # Research output
└── prompts/          # Prompt templates for large papers
```

Copy `templates/papers-gitignore` content into your `.gitignore` to exclude PDFs from git.

## Usage

### Claude Code

After install:

```
/research-papers:paper-process https://arxiv.org/abs/2104.01005
/research-papers:research screen reader accessibility
/research-papers:paper-reader papers/Mack_2021_AccessibilityResearch/paper.pdf
```

### Codex CLI

Run Codex from the project repo that contains your `papers/` directory, then invoke the skills explicitly:

```bash
$paper-process https://arxiv.org/abs/2104.01005
$research screen-reader accessibility
$paper-reader papers/Mack_2021_AccessibilityResearch/paper.pdf
$extract-claims papers/Author_2024_Title
```

Some skill command examples use `scripts/...` paths. Those are skill-local paths relative to the installed skill directory, not paths relative to the user's project repo.

Codex can also auto-select these skills from a natural-language prompt, but explicit `$skill-name` invocation is the most reliable way to verify the install.

## Requirements

- An agent CLI: Claude Code 1.0.33+, Codex CLI, or Gemini CLI
- `curl` for downloading papers
- ImageMagick (`magick`) for large paper PDF-to-image conversion
- Python 3 for cross-reference script
- Playwright MCP server for paywalled papers (optional, works on all platforms):
  - Claude Code: `claude mcp add playwright -- npx @playwright/mcp@latest`
  - Codex CLI: add `[mcp_servers.playwright]` to `~/.codex/config.toml`
  - Gemini CLI: add to `~/.gemini/settings.json` mcpServers
