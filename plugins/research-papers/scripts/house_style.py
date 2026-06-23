#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""House-style helpers (F4): em-dash lint over content .md + cross-ref separator.

The em-dash scan is scoped to *content* markdown only (notes/description/
abstract/citations + the collection index.md). The skills' own SKILL.md files
and scripts legitimately contain em-dashes and must never be flagged. The
cross-reference separator is configurable via `.research-papers.toml`
`[house_style] separator` (default ` - `, never a typographic dash).

Usage:
  uv run scripts/house_style.py emdash [--papers-dir papers/]
"""
from __future__ import annotations

import argparse
import os
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _textutil import find_em_dashes  # noqa: E402

CONTENT_MD = ("notes.md", "description.md", "abstract.md", "citations.md")
DEFAULT_SEPARATOR = " - "


def find_content_em_dashes(papers_dir) -> list[tuple[str, int, int]]:
    """Return (relpath, line, col) of every em-dash in content .md only."""
    papers_dir = Path(papers_dir)
    hits: list[tuple[str, int, int]] = []
    index = papers_dir / "index.md"
    if index.exists():
        for line, col in find_em_dashes(index.read_text(encoding="utf-8")):
            hits.append(("index.md", line, col))
    for d in sorted(papers_dir.iterdir()):
        if not d.is_dir() or d.name == "tagged":
            continue
        for fname in CONTENT_MD:
            f = d / fname
            if f.exists():
                for line, col in find_em_dashes(f.read_text(encoding="utf-8")):
                    hits.append((f"{d.name}/{fname}", line, col))
    return hits


def _load_config(root) -> dict:
    if root is None:
        return {}
    cfg = Path(root) / ".research-papers.toml"
    if not cfg.exists():
        return {}
    return tomllib.loads(cfg.read_text(encoding="utf-8"))


def separator(root=None) -> str:
    """Cross-reference separator: `[house_style] separator` or the ` - ` default."""
    return _load_config(root).get("house_style", {}).get("separator", DEFAULT_SEPARATOR)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="House-style em-dash lint")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("emdash")
    p.add_argument("--papers-dir", default="papers/")
    args = parser.parse_args(argv)
    hits = find_content_em_dashes(args.papers_dir)
    for relpath, line, col in hits:
        print(f"{relpath}:{line}:{col}  em-dash (U+2014)")
    print(f"em-dash violations: {len(hits)}")
    return 0 if not hits else 2


if __name__ == "__main__":
    raise SystemExit(main())
