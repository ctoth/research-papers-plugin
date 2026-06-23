#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""PDF adoption helpers (F2/F3/F6).

- F6: ``compare_identity`` checks a rendered title page against the expected
  title/DOI so a wrong PDF is not processed silently (the reader HALTs on a
  mismatch).
- F3: ``synced_root`` reads ``.research-papers.toml`` ``[sync] synced_root`` so
  skills can switch on cloud-sync-safe behavior (copy-verify-then-remove, capped
  parallel mutators, single-writer reconcile).

Usage:
  uv run scripts/pdf_adoption.py identity --expected "<title>" --page0 page-000.txt
"""
from __future__ import annotations

import argparse
import re
import tomllib
from pathlib import Path

_WORD = re.compile(r"\w+")
_IDENTITY_THRESHOLD = 0.5


def _tokens(text: str) -> set[str]:
    return set(_WORD.findall(text.lower()))


def compare_identity(expected: str, page0_text: str, threshold: float = _IDENTITY_THRESHOLD) -> bool:
    """True if enough of the expected title's words appear on the rendered title page.

    A DOI present in both is an immediate match.
    """
    expected_doi = re.search(r"10\.\d{4,9}/\S+", expected)
    if expected_doi and expected_doi.group(0).lower() in page0_text.lower():
        return True
    expected_tokens = _tokens(expected)
    if not expected_tokens:
        return False
    overlap = len(expected_tokens & _tokens(page0_text)) / len(expected_tokens)
    return overlap >= threshold


def _load_config(root) -> dict:
    if root is None:
        return {}
    cfg = Path(root) / ".research-papers.toml"
    if not cfg.exists():
        return {}
    return tomllib.loads(cfg.read_text(encoding="utf-8"))


def synced_root(root=None) -> bool:
    """Whether papers/ lives in a cloud-synced folder (copy-not-move, single-writer)."""
    cfg = _load_config(root)
    return bool(cfg.get("sync", {}).get("synced_root", cfg.get("synced_root", False)))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="PDF adoption identity check")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("identity")
    p.add_argument("--expected", required=True)
    p.add_argument("--page0", required=True, help="text extracted from page-000")
    args = parser.parse_args(argv)
    page0_text = Path(args.page0).read_text(encoding="utf-8")
    ok = compare_identity(args.expected, page0_text)
    print("MATCH" if ok else "MISMATCH")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
