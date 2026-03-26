# research-papers

A plugin for managing annotated research paper collections. Works with Claude Code, Codex CLI, and Gemini CLI.

This repo supports two distribution models:

- **Claude Code marketplace repo** via `.claude-plugin/marketplace.json`
- **Script-based skill installer** for Codex CLI and Gemini CLI via `scripts/install_skills.py`

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

Repository-level installer utilities live in `scripts/`. Paper-collection helper scripts live in `plugins/research-papers/scripts/`.

| Script | Description |
|--------|-------------|
| `lint_skill_frontmatter.py` | Parse every `SKILL.md` frontmatter block and fail on invalid YAML |
| `generate-paper-index.py` | Rebuild papers/index.md and papers/tagged/ symlinks |
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
uv run plugins/research-papers/scripts/generate_claims.py papers/Author_2024_Title
$extract-claims papers/Author_2024_Title

# Batch: generate drafts for all papers missing claims.yaml
uv run plugins/research-papers/scripts/batch_generate_claims.py papers/ --skip-existing

# After batch: deduplicate concepts across all claims
uv run plugins/research-papers/scripts/bootstrap_concepts.py papers/ --output concepts.yaml
```

## Installation

### Claude Code marketplace

Use the repo itself as a Claude Code marketplace source. The marketplace manifest lives at `.claude-plugin/marketplace.json` and currently exposes the plugin ID `research-papers@research-papers-marketplace`.

```bash
git clone https://github.com/ctoth/research-papers-plugin
cd research-papers-plugin
claude plugin marketplace add . --scope user
claude plugin install research-papers@research-papers-marketplace --scope user
```

If your clone already exists somewhere else, replace `.` with that repo path.

### Script-based installer for Codex CLI and Gemini CLI

Use the bundled installer when you want the skills installed into Codex and/or Gemini user skill directories:

```bash
uv run scripts/install_skills.py doctor
uv run scripts/install_skills.py install --platform codex --platform gemini
```

What the installer does:

- discovers every skill directory under `plugins/*/skills/*`
- installs Codex skills into `~/.agents/skills`
- installs Gemini skills into `~/.gemini/skills`
- prefers whole-directory symlinks and falls back to copying if symlinks are unavailable

Useful variants:

```bash
uv run scripts/lint_skill_frontmatter.py
uv run scripts/install_skills.py install
uv run scripts/install_skills.py install --platform codex
uv run scripts/install_skills.py install --platform gemini
uv run scripts/install_skills.py install --platform claude
uv run scripts/install_skills.py uninstall
```

`install --platform claude` uses Claude's native `claude plugin marketplace add/install` flow under the hood. Omitting `--platform` installs all supported targets.

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

Copy `plugins/research-papers/templates/papers-gitignore` into your `.gitignore` to exclude PDFs from git.

## Usage

### Claude Code

After marketplace install:

```
/research-papers:paper-process https://arxiv.org/abs/2104.01005
/research-papers:research screen reader accessibility
/research-papers:paper-reader papers/Mack_2021_AccessibilityResearch/paper.pdf
```

### Codex CLI

Run Codex from the project repo that contains your `papers/` directory, then invoke the installed skills explicitly:

```bash
$paper-process https://arxiv.org/abs/2104.01005
$research screen-reader accessibility
$paper-reader papers/Mack_2021_AccessibilityResearch/paper.pdf
$extract-claims papers/Author_2024_Title
```

Some skill command examples use `scripts/...` paths. Those are skill-local paths relative to the installed skill directory, not paths relative to the user's project repo.

Codex can also auto-select these skills from a natural-language prompt, but explicit `$skill-name` invocation is the most reliable way to verify the install.

### Gemini CLI

Run Gemini from the project repo that contains your `papers/` directory. Gemini loads the installed skills from `~/.gemini/skills`; unlike Codex, it does not use `$skill-name` command syntax, so invoke the skill by name in your prompt:

```text
Use the paper-process skill on https://arxiv.org/abs/2104.01005
Use the research skill to investigate screen reader accessibility
Use the paper-reader skill on papers/Mack_2021_AccessibilityResearch/paper.pdf
```

## Requirements

- An agent CLI: Claude Code 1.0.33+, Codex CLI, or Gemini CLI
- `curl` for downloading papers
- ImageMagick (`magick`) for large paper PDF-to-image conversion
- Python 3 for cross-reference script
- Playwright MCP server for paywalled papers (optional, works on all platforms):
  - Claude Code: `claude mcp add playwright -- npx @playwright/mcp@latest`
  - Codex CLI: add `[mcp_servers.playwright]` to `~/.codex/config.toml`
  - Gemini CLI: add to `~/.gemini/settings.json` mcpServers
