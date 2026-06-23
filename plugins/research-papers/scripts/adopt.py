#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6"]
# ///
"""Adopt a cross-collection paper into a collection (F13).

Promotes a "link-not-copy" main-bib paper to a full collection member, composing
the three primitives this op is built from:
  - F3: copy-verify the whole paper directory (cloud-sync-safe, never a move),
  - F5: insert the index entry in place + bump tags.yaml counts,
  - F12: remove the adopted key from the candidate pool.

Usage:
  uv run scripts/adopt.py <main-bib-dir> --into <collection-root> [--pool candidate.bibtex]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _fsutil import copy_verify  # noqa: E402
from reconcile_candidates import _remove_entries  # noqa: E402


def _load_gpi():
    """Load the hyphenated generate-paper-index.py module for its F5 helpers."""
    path = Path(__file__).resolve().parent / "generate-paper-index.py"
    spec = importlib.util.spec_from_file_location("generate_paper_index", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def copy_dir_verify(src_dir: Path, dest_dir: Path) -> None:
    """Copy every file under src_dir into dest_dir, integrity-verifying each."""
    src_dir = Path(src_dir)
    for f in sorted(src_dir.rglob("*")):
        if f.is_file():
            copy_verify(f, dest_dir / f.relative_to(src_dir))


def _cite_key_of(paper_dir: Path) -> str | None:
    meta = paper_dir / "metadata.json"
    if not meta.exists():
        return None
    return json.loads(meta.read_text(encoding="utf-8")).get("cite_key")


def adopt(src_dir, project_root, candidate_bibtex=None) -> Path:
    """Adopt src_dir into project_root/papers/: copy-verify, index/tags insert, pool removal."""
    src_dir = Path(src_dir)
    papers_dir = Path(project_root) / "papers"
    name = src_dir.name
    dest = papers_dir / name

    copy_dir_verify(src_dir, dest)

    gpi = _load_gpi()
    gpi.insert_paper(papers_dir, name)

    cite_key = _cite_key_of(dest)
    if candidate_bibtex and cite_key:
        pool = Path(candidate_bibtex)
        if pool.exists():
            pool.write_text(_remove_entries(pool.read_text(encoding="utf-8"), {cite_key}),
                            encoding="utf-8")
    return dest


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Adopt a cross-collection paper into a collection")
    parser.add_argument("src_dir", help="The main-bib paper directory to adopt")
    parser.add_argument("--into", required=True, help="Collection project root (contains papers/)")
    parser.add_argument("--pool", default=None, help="Candidate-pool .bibtex to prune")
    args = parser.parse_args(argv)
    dest = adopt(args.src_dir, args.into, candidate_bibtex=args.pool)
    print(f"Adopted {Path(args.src_dir).name} -> {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
