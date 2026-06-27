#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Citation-claim verification harness (F10).

Deterministic core only: extract each @key and the sentence(s) that cite it,
resolve @key -> paper directory via the B5 keymap, and serialize a per-claim
grade report. The actual grading (SUPPORTED / PARTIAL / UNSUPPORTED /
MISATTRIBUTED) is performed by subagents reading each cited paper's
notes.md/abstract.md, one subagent per cited paper (see the verify-citations
skill); this module never invents a verdict.

Usage:
  uv run scripts/verify_citations.py extract <draft.md>
  uv run scripts/verify_citations.py resolve <draft.md> [--papers-dir papers/]
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_keymap import load_keymap  # noqa: E402

VERDICTS = ("SUPPORTED", "PARTIAL", "UNSUPPORTED", "MISATTRIBUTED")
CITE_RE = re.compile(r"@([A-Za-z][\w:-]*)")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def extract_citations(draft_text: str) -> dict[str, list[str]]:
    """Map each cited @key to the list of sentences that cite it."""
    out: dict[str, list[str]] = {}
    for sentence in _SENTENCE_SPLIT.split(draft_text.strip()):
        for key in CITE_RE.findall(sentence):
            out.setdefault(key, []).append(sentence.strip())
    return out


def resolve_key(key: str, papers_dir) -> str | None:
    """Resolve a cite_key to its paper directory via the keymap (None if unknown)."""
    return load_keymap(Path(papers_dir)).get(key)


@dataclass
class GradeReport:
    key: str
    verdict: str
    snippet: str = ""
    fix: str = ""
    citing_sentences: list[str] = field(default_factory=list)


def render_report(reports: list[GradeReport]) -> str:
    """Serialize grade reports. Raises ValueError on an unknown verdict label."""
    lines: list[str] = []
    for r in reports:
        if r.verdict not in VERDICTS:
            raise ValueError(f"unknown verdict {r.verdict!r}; expected one of {VERDICTS}")
        lines.append(f"## {r.key} - {r.verdict}")
        if r.snippet:
            lines.append(f"snippet: {r.snippet}")
        if r.fix:
            lines.append(f"fix: {r.fix}")
        lines.append("")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Citation-claim verification harness")
    sub = parser.add_subparsers(dest="command", required=True)
    p_ex = sub.add_parser("extract", help="List @key -> citing sentences")
    p_ex.add_argument("draft")
    p_res = sub.add_parser("resolve", help="Resolve cited @keys to paper dirs")
    p_res.add_argument("draft")
    p_res.add_argument("--papers-dir", default="papers/")

    args = parser.parse_args(argv)
    draft_text = Path(args.draft).read_text(encoding="utf-8")
    citations = extract_citations(draft_text)

    if args.command == "extract":
        for key, sents in sorted(citations.items()):
            print(f"@{key} ({len(sents)} citing sentence(s))")
    elif args.command == "resolve":
        for key in sorted(citations):
            d = resolve_key(key, args.papers_dir)
            print(f"@{key}\t{d or 'UNRESOLVED'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
