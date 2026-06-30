#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Migrate paper directories so each folder name equals its bibtex cite_key (F4).

Under B5, directory names and cite keys were intentionally decoupled (the dir
encoded the preprint/first-seen year while the published key used the published
year). That decision is overturned (2026-06-30): ``dir == cite_key`` is now a
required corpus invariant. This script renames every mismatched paper directory
to its cite_key and rewrites all references to the old name -- ``papers/index.md``,
``papers/_reader_done.tsv``, ``papers/keymap.tsv``, and the relative cross-links
(``../<Dir>/notes.md``) and wikilinks (``[[<Dir>]]``) in sibling notes/citations.

Run ``build_keymap.py backfill --write`` first so every metadata.json carries a
cite_key; otherwise derive_cite_key falls back to a generated key.

Usage:
  uv run scripts/rename_to_cite_key.py [--papers-dir papers/]            # dry run
  uv run scripts/rename_to_cite_key.py --papers-dir papers/ --write      # apply
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_keymap import derive_cite_key  # noqa: E402

# Files at the collection root whose text references paper directory names.
ROOT_REF_FILES = ("index.md", "_reader_done.tsv", "keymap.tsv")
# Per-paper files that may carry cross-links to other paper directories.
PAPER_REF_FILES = ("notes.md", "citations.md")


def plan_renames(papers_dir: Path) -> list[tuple[str, str]]:
    """Return sorted (old_dir, new_dir) pairs for dirs whose name != cite_key."""
    papers_dir = Path(papers_dir)
    renames: list[tuple[str, str]] = []
    for meta_path in sorted(papers_dir.glob("*/metadata.json")):
        dirname = meta_path.parent.name
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        cite_key = derive_cite_key(metadata, dirname)
        if cite_key != dirname:
            renames.append((dirname, cite_key))
    return sorted(renames)


def _rename_regex(old_names: list[str]) -> re.Pattern[str]:
    """Whole-token matcher for any old directory name (longest-first)."""
    ordered = sorted(old_names, key=len, reverse=True)
    return re.compile(r"\b(" + "|".join(re.escape(n) for n in ordered) + r")\b")


def rewrite_text(text: str, rename_map: dict[str, str], pattern: re.Pattern[str]) -> str:
    """Replace every whole-token occurrence of an old dir name with its new name."""
    return pattern.sub(lambda m: rename_map.get(m.group(1), m.group(1)), text)


def _rewrite_file(path: Path, rename_map: dict[str, str], pattern: re.Pattern[str]) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    new_text = rewrite_text(text, rename_map, pattern)
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
        return True
    return False


def apply_renames(papers_dir: Path, write: bool = False) -> list[tuple[str, str]]:
    """Plan renames; with write=True, rewrite references then rename directories.

    Returns the (old, new) pairs that were (or would be) renamed.
    """
    papers_dir = Path(papers_dir)
    renames = plan_renames(papers_dir)
    if not write or not renames:
        return renames

    targets = [t for t, _ in renames]
    collisions = [new for _, new in renames if (papers_dir / new).exists() and new not in targets]
    if collisions:
        raise FileExistsError(f"rename target(s) already exist: {', '.join(sorted(collisions))}")

    rename_map = dict(renames)
    pattern = _rename_regex(list(rename_map))

    # 1. Rewrite references first (while directories are still under old names).
    for fname in ROOT_REF_FILES:
        _rewrite_file(papers_dir / fname, rename_map, pattern)
    for paper_dir in sorted(papers_dir.iterdir()):
        if not paper_dir.is_dir():
            continue
        for fname in PAPER_REF_FILES:
            _rewrite_file(paper_dir / fname, rename_map, pattern)

    # 2. Rename directories. Longest-first avoids any path-prefix clashes.
    for old, new in sorted(renames, key=lambda r: len(r[0]), reverse=True):
        (papers_dir / old).rename(papers_dir / new)

    return renames


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Rename paper dirs to their cite_key (F4)")
    parser.add_argument("--papers-dir", default="papers/")
    parser.add_argument("--write", action="store_true",
                        help="Apply renames + rewrite references (default: dry run)")
    args = parser.parse_args(argv)

    papers_dir = Path(args.papers_dir)
    renames = apply_renames(papers_dir, write=args.write)
    verb = "Renamed" if args.write else "Would rename"
    print(f"{verb} {len(renames)} director{'y' if len(renames) == 1 else 'ies'}:")
    for old, new in renames:
        print(f"  {old} -> {new}")
    if not renames:
        print("  (none — every folder already equals its cite_key)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
