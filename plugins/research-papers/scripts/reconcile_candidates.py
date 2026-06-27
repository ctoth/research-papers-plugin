#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Candidate-pool reconcile / graduation detection (F12).

A candidate is, by definition, a key in the candidate pool but NOT cited in the
draft. When the draft is rewritten, former candidates "graduate" to cited and
must be removed from the pool .bibtex and the pool .md prose counts fixed. This
keeps that invariant mechanical instead of hand-reconciled every pass.

Usage:
  uv run scripts/reconcile_candidates.py <draft.md> <candidate.bibtex> [--write] [--pool-md candidate.md]
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

DRAFT_CITE_RE = re.compile(r"@([A-Za-z][\w:-]*)")
BIBTEX_ENTRY_RE = re.compile(r"@\w+\s*\{\s*([^,\s]+)\s*,")


def draft_keys(draft_text: str) -> set[str]:
    return set(DRAFT_CITE_RE.findall(draft_text))


def extract_keys(bibtex_text: str) -> set[str]:
    return set(BIBTEX_ENTRY_RE.findall(bibtex_text))


def _remove_entries(bibtex_text: str, keys: set[str]) -> str:
    """Drop whole @entry{...} blocks whose key is in keys (brace-balanced)."""
    out: list[str] = []
    i = 0
    n = len(bibtex_text)
    entry_start = re.compile(r"@\w+\s*\{\s*([^,\s]+)\s*,")
    while i < n:
        m = entry_start.search(bibtex_text, i)
        if not m:
            out.append(bibtex_text[i:])
            break
        out.append(bibtex_text[i:m.start()])
        # Find the matching closing brace for this entry.
        depth = 0
        j = bibtex_text.index("{", m.start())
        k = j
        while k < n:
            if bibtex_text[k] == "{":
                depth += 1
            elif bibtex_text[k] == "}":
                depth -= 1
                if depth == 0:
                    break
            k += 1
        entry_text = bibtex_text[m.start():k + 1]
        if m.group(1) not in keys:
            out.append(entry_text)
        i = k + 1
    return "".join(out)


def reconcile_candidates(candidate_bibtex: str, draft_text: str) -> tuple[str, set[str]]:
    """Return (pruned_bibtex, graduated_keys) — graduates are candidates now cited."""
    graduated = extract_keys(candidate_bibtex) & draft_keys(draft_text)
    return _remove_entries(candidate_bibtex, graduated), graduated


def fix_pool_count(pool_md: str, count: int) -> str:
    """Replace the integer preceding 'works' in the pool prose with `count`."""
    return re.sub(r"\d+(?=\s+works)", str(count), pool_md, count=1)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Candidate-pool reconcile against a draft")
    parser.add_argument("draft")
    parser.add_argument("bibtex")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--pool-md", default=None)
    args = parser.parse_args(argv)

    draft_text = Path(args.draft).read_text(encoding="utf-8")
    bib_path = Path(args.bibtex)
    new_bib, graduated = reconcile_candidates(bib_path.read_text(encoding="utf-8"), draft_text)
    remaining = len(extract_keys(new_bib))
    print(f"Graduated {len(graduated)}: {', '.join(sorted(graduated)) or '(none)'}")
    print(f"Remaining candidates: {remaining}")

    if args.write:
        bib_path.write_text(new_bib, encoding="utf-8")
        if args.pool_md:
            md_path = Path(args.pool_md)
            md_path.write_text(fix_pool_count(md_path.read_text(encoding="utf-8"), remaining),
                               encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
