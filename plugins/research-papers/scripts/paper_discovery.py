#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Centralized paper-directory discovery (F1).

A book is processed as a parent directory holding the whole-book paper plus a
``chapters/`` subdirectory of per-chapter papers:

    papers/Geertz_1973_Interpretation/        # whole book (document_type: book)
      metadata.json  notes.md  abstract.md  index.md
      chapters/
        Geertz_1973_ThickDescription/         # per-chapter paper (book_chapter)
          metadata.json  notes.md  abstract.md  citations.md
        Geertz_1973_DeepPlay/

Every keymap/bibtex/lint/index tool must find both the book dir and each nested
chapter dir exactly once, without double-counting the book or treating the
``chapters/`` container as a paper. This module is the single discovery seam so
those four tools stay consistent. A collection with no ``chapters/`` subdirs
yields exactly the one-level paper dirs, so the behavior is backward compatible.
"""
from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

CHAPTERS_SUBDIR = "chapters"
SKIP_DIRS = {"tagged", "tagged-papers"}


def candidate_paper_dirs(papers_root: Path) -> Iterator[Path]:
    """Yield each top-level paper dir and each of its ``chapters/<dir>`` children.

    The book dir and every chapter dir are yielded exactly once; the
    ``chapters/`` container itself is never yielded.
    """
    papers_root = Path(papers_root)
    if not papers_root.is_dir():
        return
    for top in sorted(papers_root.iterdir()):
        if not top.is_dir() or top.name in SKIP_DIRS:
            continue
        yield top
        chapters = top / CHAPTERS_SUBDIR
        if chapters.is_dir():
            for chapter in sorted(chapters.iterdir()):
                if chapter.is_dir():
                    yield chapter


def discover_metadata_dirs(papers_root: Path) -> list[Path]:
    """Discovered paper dirs that contain a metadata.json."""
    return [d for d in candidate_paper_dirs(papers_root) if (d / "metadata.json").exists()]


def discover_notes_dirs(papers_root: Path) -> list[Path]:
    """Discovered paper dirs that contain a notes.md."""
    return [d for d in candidate_paper_dirs(papers_root) if (d / "notes.md").exists()]


def relpath(paper_dir: Path, papers_root: Path) -> str:
    """Posix relative path of a paper dir under papers_root (identity map key).

    Top-level papers give a single component (e.g. ``Norm_2020_A``); chapters give
    ``Book/chapters/Chapter`` so ``papers_root / relpath`` resolves either one.
    """
    return Path(paper_dir).relative_to(papers_root).as_posix()


if __name__ == "__main__":
    import sys

    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("papers/")
    for d in discover_metadata_dirs(root):
        print(relpath(d, root))
