# research-papers

A Claude Code plugin for managing annotated research paper collections.

## What it does

This plugin provides skills for retrieving, reading, and annotating scientific papers into a structured, cross-referenced collection. Each paper gets:

- **notes.md** — Implementation-focused extraction (equations, parameters, algorithms)
- **description.md** — Three-sentence summary
- **abstract.md** — Verbatim abstract + interpretation
- **citations.md** — Full reference list + key citations for follow-up
- **papers/CLAUDE.md** — Auto-generated index so Claude knows what's in the collection

## Skills

| Skill | Description |
|-------|-------------|
| `paper-retriever` | Download a paper PDF from arxiv, DOI, ACL Anthology, or sci-hub |
| `paper-reader` | Read a paper and extract structured notes (handles small/medium/large papers) |
| `paper-process` | Combined retrieve + read in one step |
| `research` | Web research on a topic, structured findings report |
| `make-skill` | Create new skills from prompt files |

## Scripts

| Script | Description |
|--------|-------------|
| `generate-paper-claude-md.sh` | Rebuild papers/CLAUDE.md index from all description.md files |
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

### Project setup

Your project needs this structure:

```
your-project/
├── papers/
│   └── CLAUDE.md    # Paper index (auto-generated)
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

- Claude Code 1.0.33+
- `curl` for downloading papers
- ImageMagick (`magick`) for large paper PDF-to-image conversion
- Python 3 for cross-reference script
- Chrome + claude-in-chrome MCP server for paywalled papers (optional)
