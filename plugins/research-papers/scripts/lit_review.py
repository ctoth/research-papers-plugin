#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Lit-review deliverable verify/build (F11).

Checks a draft against its self-contained citations.bibtex:
  - key symmetry in BOTH directions (missing: cited but not in bibtex; orphan:
    in bibtex but never cited),
  - citation-stripped word count ([@key] markers inflate raw counts),
  - em-dash compliance (via _textutil).

Regex-only; no bibtex library needed (we only need the entry keys).

Usage:
  uv run scripts/lit_review.py verify <folder> [--draft draft.md] [--bib citations.bibtex]
  uv run scripts/lit_review.py build  <folder>  # assemble citations.bibtex from draft keys
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _textutil import find_em_dashes  # noqa: E402

DRAFT_CITE_RE = re.compile(r"@([A-Za-z][\w:-]*)")
BIBTEX_KEY_RE = re.compile(r"@\w+\s*\{\s*([^,\s]+)\s*,")
# A whole [@key] / [@k1; @k2] marker, for stripping before word counting.
CITE_MARKER_RE = re.compile(r"\[@[^\]]*\]|@[A-Za-z][\w:-]*")


def draft_keys(draft_text: str) -> set[str]:
    return set(DRAFT_CITE_RE.findall(draft_text))


def bibtex_keys(bibtex_text: str) -> set[str]:
    return set(BIBTEX_KEY_RE.findall(bibtex_text))


def key_symmetry(draft_text: str, bibtex_text: str) -> dict[str, set[str]]:
    """{'missing': cited-not-in-bib, 'orphan': in-bib-not-cited}."""
    cited = draft_keys(draft_text)
    declared = bibtex_keys(bibtex_text)
    return {"missing": cited - declared, "orphan": declared - cited}


def citation_stripped_word_count(draft_text: str) -> int:
    """Word count after removing citation markers like [@key]."""
    stripped = CITE_MARKER_RE.sub(" ", draft_text)
    return len(stripped.split())


def verify(folder: Path, draft_name: str = "draft.md",
           bib_name: str = "citations.bibtex") -> dict:
    folder = Path(folder)
    draft_text = (folder / draft_name).read_text(encoding="utf-8")
    bibtex_text = (folder / bib_name).read_text(encoding="utf-8")
    sym = key_symmetry(draft_text, bibtex_text)
    return {
        "missing": sorted(sym["missing"]),
        "orphan": sorted(sym["orphan"]),
        "word_count": citation_stripped_word_count(draft_text),
        "em_dashes": find_em_dashes(draft_text),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Lit-review verify/build")
    sub = parser.add_subparsers(dest="command", required=True)
    p_v = sub.add_parser("verify")
    p_v.add_argument("folder")
    p_v.add_argument("--draft", default="draft.md")
    p_v.add_argument("--bib", default="citations.bibtex")
    p_b = sub.add_parser("build")
    p_b.add_argument("folder")
    p_b.add_argument("--draft", default="draft.md")

    args = parser.parse_args(argv)
    folder = Path(args.folder)
    if args.command == "verify":
        result = verify(folder, args.draft, args.bib)
        print(f"missing (cited, not in bibtex): {result['missing'] or '(none)'}")
        print(f"orphan (in bibtex, not cited): {result['orphan'] or '(none)'}")
        print(f"citation-stripped word count: {result['word_count']}")
        print(f"em-dashes: {len(result['em_dashes'])}")
        return 0 if not (result["missing"] or result["orphan"] or result["em_dashes"]) else 2
    elif args.command == "build":
        keys = sorted(draft_keys((folder / args.draft).read_text(encoding="utf-8")))
        print("\n".join(f"@misc{{{k},\n}}" for k in keys))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
