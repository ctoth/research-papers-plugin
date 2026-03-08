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
| `reconcile` | Cross-reference a paper against the collection bidirectionally |
| `research` | Web research on a topic, structured findings report |
| `make-skill` | Create new skills from prompt files |

## Scripts

| Script | Description |
|--------|-------------|
| `generate-paper-index.py` | Rebuild papers/index.md from paper directories |
| `cross-reference-papers.py` | Find cross-references between papers in the collection |

## Installation

### From GitHub (recommended)

Add this repo as a marketplace, then install the plugin:

```bash
claude plugin marketplace add ctoth/research-papers-plugin
claude plugin install research-papers@research-papers-marketplace
```

### From local path (development)

```bash
claude plugin marketplace add /path/to/research-papers-plugin
claude plugin install research-papers@research-papers-marketplace
```

### For Codex CLI

Create symlinks so Codex discovers the skills:

```bash
mkdir -p .agents/skills
ln -s ../../plugins/research-papers/skills/* .agents/skills/
```

### For Gemini CLI

Create symlinks so Gemini discovers the skills:

```bash
mkdir -p .gemini/skills
ln -s ../../plugins/research-papers/skills/* .gemini/skills/
```

### Project setup

Your project needs this structure:

```
your-project/
├── papers/
│   ├── AGENTS.md    # Static instructions for agents (how to use the collection)
│   ├── index.md     # Paper directory listing (auto-generated)
│   ├── CLAUDE.md    # Contains: @AGENTS.md
│   └── GEMINI.md    # Contains: @AGENTS.md
├── reports/          # Research output
└── prompts/          # Prompt templates for large papers
```

Copy `templates/papers-gitignore` content into your `.gitignore` to exclude PDFs from git.

## Usage

```
/research-papers:paper-process https://arxiv.org/abs/2104.01005
/research-papers:research screen reader accessibility
/research-papers:paper-reader papers/Mack_2021_AccessibilityResearch/paper.pdf
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
