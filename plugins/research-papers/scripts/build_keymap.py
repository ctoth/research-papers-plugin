#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Build and maintain papers/keymap.tsv and backfill cite_key (B5, F4).

cite_key must be the first key of every metadata.json. As of F4 (overturning the
original B5 decoupling) a paper's directory name must equal its cite_key
(`dir == cite_key`); ``rename_to_cite_key.py`` migrates any divergent folders and
``lint_paper_schema.py`` enforces the invariant (`DIR_KEY_MISMATCH`). ``keymap.tsv``
maps ``cite_key<TAB>dir`` and is therefore now an identity cache, kept for reliable
@key -> directory resolution downstream (F8 verify, F10 citation audit, F13 adopt).

Usage:
  uv run scripts/build_keymap.py build   [--papers-dir papers/] [-o papers/keymap.tsv]
  uv run scripts/build_keymap.py backfill [--papers-dir papers/] [--write]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

# Reuse the canonical citation-key generator instead of inventing a parallel one.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from export_bibtex import _citation_key  # noqa: E402

BIBTEX_KEY_RE = re.compile(r"@\w+\s*\{\s*([^,\s]+)\s*,")


def extract_bibtex_key(blob: str) -> str | None:
    """Return the key of the first @entry in a BibTeX blob, or None."""
    if not blob:
        return None
    m = BIBTEX_KEY_RE.search(blob)
    return m.group(1) if m else None


def derive_cite_key(metadata: dict, dirname: str) -> str:
    """Resolve a cite_key: existing field, else embedded bibtex key, else generated."""
    existing = metadata.get("cite_key")
    if existing:
        return existing
    key = extract_bibtex_key(metadata.get("bibtex", ""))
    if key:
        return key
    return _citation_key(metadata, dirname)


def validate_cite_key_first(metadata) -> bool:
    """True iff cite_key is present AND the first key of the metadata mapping.

    Accepts a dict or a JSON string (insertion order is significant).
    """
    if isinstance(metadata, str):
        metadata = json.loads(metadata)
    keys = list(metadata.keys())
    return bool(keys) and keys[0] == "cite_key"


def keymap_entries(papers_dir: Path) -> list[tuple[str, str]]:
    """Return sorted (cite_key, dirname) pairs for every metadata.json."""
    papers_dir = Path(papers_dir)
    entries: list[tuple[str, str]] = []
    for meta_path in sorted(papers_dir.glob("*/metadata.json")):
        dirname = meta_path.parent.name
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        entries.append((derive_cite_key(metadata, dirname), dirname))
    return sorted(entries)


def build_keymap(papers_dir: Path) -> str:
    """Render keymap.tsv text (cite_key<TAB>dir, one per line, sorted by key)."""
    return "".join(f"{key}\t{d}\n" for key, d in keymap_entries(papers_dir))


def load_keymap(papers_dir: Path) -> dict[str, str]:
    """Return {cite_key: dir}, reading papers/keymap.tsv if present, else building it."""
    papers_dir = Path(papers_dir)
    tsv = papers_dir / "keymap.tsv"
    if tsv.exists():
        out: dict[str, str] = {}
        for line in tsv.read_text(encoding="utf-8").splitlines():
            if "\t" in line:
                key, d = line.split("\t", 1)
                out[key.strip()] = d.strip()
        return out
    return {key: d for key, d in keymap_entries(papers_dir)}


def backfill(papers_dir: Path, write: bool = False) -> list[str]:
    """Ensure cite_key is present and first in each metadata.json.

    Returns the list of changed directory names. With write=False it is a dry run.
    """
    papers_dir = Path(papers_dir)
    changed: list[str] = []
    for meta_path in sorted(papers_dir.glob("*/metadata.json")):
        dirname = meta_path.parent.name
        text = meta_path.read_text(encoding="utf-8")
        metadata = json.loads(text)
        if validate_cite_key_first(metadata):
            continue
        cite_key = derive_cite_key(metadata, dirname)
        reordered = {"cite_key": cite_key}
        for k, v in metadata.items():
            if k != "cite_key":
                reordered[k] = v
        changed.append(dirname)
        if write:
            meta_path.write_text(json.dumps(reordered, indent=2) + "\n", encoding="utf-8")
    return changed


def main(argv=None) -> int:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--papers-dir", default="papers/")

    parser = argparse.ArgumentParser(description="Build keymap.tsv / backfill cite_key")
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", parents=[common], help="Write/print keymap.tsv")
    p_build.add_argument("-o", "--output", default=None)

    sub.add_parser("backfill", parents=[common],
                   help="Insert cite_key first where missing").add_argument(
        "--write", action="store_true", help="Rewrite metadata.json (default: dry run)")

    args = parser.parse_args(argv)
    papers_dir = Path(args.papers_dir)

    if args.command == "build":
        tsv = build_keymap(papers_dir)
        if args.output:
            Path(args.output).write_text(tsv, encoding="utf-8")
            print(f"Wrote {args.output}", file=sys.stderr)
        else:
            print(tsv, end="")
    elif args.command == "backfill":
        changed = backfill(papers_dir, write=args.write)
        verb = "Updated" if args.write else "Would update"
        print(f"{verb} {len(changed)} metadata.json: {', '.join(changed) or '(none)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
