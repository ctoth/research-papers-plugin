#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""Lit-review deliverable verify/build/gate (F11, F2).

Checks a draft against its self-contained citations.bibtex:
  - key symmetry in BOTH directions (missing: cited but not in bibtex; orphan:
    in bibtex but never cited),
  - citation-stripped word count ([@key] markers inflate raw counts),
  - em-dash compliance (via _textutil).

The `gate` subcommand (F2) is the blocking presence check: every key cited in the
draft must be present in BOTH citations.bibtex AND papers/ (resolves to a paper
directory that passes the F3 completeness gate). Exits 2 if any key is missing.

Regex-only for bibtex/draft parsing; `pyyaml` is pulled in transitively by the F3
linter the gate delegates to.

Usage:
  uv run scripts/lit_review.py verify <folder> [--draft draft.md] [--bib citations.bibtex]
  uv run scripts/lit_review.py build  <folder>  # assemble citations.bibtex from draft keys
  uv run scripts/lit_review.py gate   <folder> [--draft draft.md] [--bib citations.bibtex] [--papers-dir papers/]
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _textutil import find_em_dashes  # noqa: E402
from build_keymap import load_keymap  # noqa: E402
from verify_citations import extract_citations  # noqa: E402

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


def _dir_passes_f3(paper_dir: Path, papers_root: Path) -> bool:
    """True iff a single paper directory passes the F3 completeness gate.

    Delegates to the mechanical linter: zero per-paper violations (required files
    incl. abstract.md, notes frontmatter, dir == cite_key) AND abstract.md carries
    both the verbatim and interpretation sections. Imported lazily so `verify`/
    `build` keep their dependency-free, stdlib-only footprint.
    """
    if not paper_dir.is_dir():
        return False
    from audit_paper_corpus import audit_paper_dir  # noqa: PLC0415
    import lint_paper_schema as lps  # noqa: PLC0415

    audit = audit_paper_dir(paper_dir)
    if lps.lint_paper(audit, papers_root):
        return False
    abstract = paper_dir / "abstract.md"
    if abstract.exists():
        text = abstract.read_text(encoding="utf-8")
        if any(section not in text for section in lps.ABSTRACT_REQUIRED_SECTIONS):
            return False
    return True


def presence_gate(folder: Path, draft_name: str = "draft.md",
                  bib_name: str = "citations.bibtex", papers_dir="papers/") -> dict:
    """F2: classify each cited key as missing-from-bibtex / missing-from-papers.

    A key is "present in papers/" only if it resolves to a directory AND that
    directory passes the F3 completeness gate (2026-06-30 decision).
    """
    folder = Path(folder)
    papers_dir = Path(papers_dir)
    draft_text = (folder / draft_name).read_text(encoding="utf-8")
    bib_path = folder / bib_name
    bibtex_text = bib_path.read_text(encoding="utf-8") if bib_path.exists() else ""

    cited = draft_keys(draft_text)
    declared = bibtex_keys(bibtex_text)
    citing = extract_citations(draft_text)
    keymap = load_keymap(papers_dir)

    missing_from_bibtex = sorted(cited - declared)
    missing_from_papers = []
    for key in sorted(cited):
        resolved = keymap.get(key)
        if resolved is None or not _dir_passes_f3(papers_dir / resolved, papers_dir):
            missing_from_papers.append(key)
    return {
        "missing_from_bibtex": missing_from_bibtex,
        "missing_from_papers": missing_from_papers,
        "citing": citing,
    }


def _render_gate_bucket(code: str, keys: list[str], citing: dict[str, list[str]]) -> list[str]:
    lines = [f"{code} ({len(keys)})"]
    for key in keys:
        sentence = citing.get(key, [""])[0]
        lines.append(f"  - @{key}: {sentence}" if sentence else f"  - @{key}")
    return lines


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Lit-review verify/build/gate")
    sub = parser.add_subparsers(dest="command", required=True)
    p_v = sub.add_parser("verify")
    p_v.add_argument("folder")
    p_v.add_argument("--draft", default="draft.md")
    p_v.add_argument("--bib", default="citations.bibtex")
    p_b = sub.add_parser("build")
    p_b.add_argument("folder")
    p_b.add_argument("--draft", default="draft.md")
    p_g = sub.add_parser("gate", help="F2 blocking presence check (bibtex AND papers/)")
    p_g.add_argument("folder")
    p_g.add_argument("--draft", default="draft.md")
    p_g.add_argument("--bib", default="citations.bibtex")
    p_g.add_argument("--papers-dir", default="papers/")

    args = parser.parse_args(argv)
    folder = Path(args.folder)
    if args.command == "gate":
        result = presence_gate(folder, args.draft, args.bib, args.papers_dir)
        mb, mp = result["missing_from_bibtex"], result["missing_from_papers"]
        if mb:
            print("\n".join(_render_gate_bucket("MISSING_FROM_BIBTEX", mb, result["citing"])))
        if mp:
            print("\n".join(_render_gate_bucket("MISSING_FROM_PAPERS", mp, result["citing"])))
        if mb or mp:
            print(f"gate: BLOCKED ({len(mb)} missing from bibtex, {len(mp)} missing from papers)")
            return 2
        print("gate: OK (every cited key is in citations.bibtex and papers/)")
        return 0
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
