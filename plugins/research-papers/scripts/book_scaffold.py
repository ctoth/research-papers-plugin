#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Scaffolding helpers for processing a book as per-chapter papers (F1).

A book directory holds the whole-book paper plus a ``chapters/`` subdirectory of
per-chapter paper directories. These helpers create a chapter paper directory with
a born-compliant ``metadata.json`` (``cite_key`` first per B5, ``dir == cite_key``
per F4, ``document_type: book_chapter`` and ``parent_book`` per F1) and render the
book-level ``index.md`` chapter map. The chapter's notes/abstract/citations are
written by ``paper-reader`` against the chapter's page range; this module only lays
down the directory and metadata skeleton and the navigation surface.

Usage (from the book-process skill):
  uv run scripts/book_scaffold.py index papers/<Book>/   # print the chapter index.md
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CHAPTERS_SUBDIR = "chapters"


def chapter_paper_dir(book_dir: Path, chapter_cite_key: str) -> Path:
    """Path of a chapter paper dir under the book (dir name == chapter cite_key)."""
    return Path(book_dir) / CHAPTERS_SUBDIR / chapter_cite_key


def scaffold_chapter(book_dir: Path, chapter_cite_key: str,
                     metadata: dict | None = None) -> Path:
    """Create ``<book>/chapters/<cite_key>/`` and write its metadata.json skeleton.

    ``cite_key`` is written first; ``document_type`` defaults to ``book_chapter`` and
    ``parent_book`` is set to the book directory name. Extra fields (title, year,
    pages, container_title, publisher, address) are merged in after cite_key.
    """
    book_dir = Path(book_dir)
    d = chapter_paper_dir(book_dir, chapter_cite_key)
    d.mkdir(parents=True, exist_ok=True)

    meta: dict = {"cite_key": chapter_cite_key}
    for key, value in (metadata or {}).items():
        if key != "cite_key":
            meta[key] = value
    meta.setdefault("document_type", "book_chapter")
    meta["parent_book"] = book_dir.name

    (d / "metadata.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return d


def select_chapters(chapters: list, topic: str | None = None) -> list:
    """Default to all chapters when no topic is given.

    Topic-driven relevance selection is a judgment step the book-process skill
    performs while reading the TOC; the mechanical default here is "all chapters".
    """
    return list(chapters)


def _chapter_oneliner(chapter_dir: Path) -> str:
    """A one-line description for a chapter: description.md body, else notes title."""
    desc = chapter_dir / "description.md"
    if desc.exists():
        text = desc.read_text(encoding="utf-8")
        text = re.sub(r"^---\s*\n.*?\n---\s*\n?", "", text, flags=re.DOTALL)
        for line in text.splitlines():
            if line.strip():
                return line.strip()
    notes = chapter_dir / "notes.md"
    if notes.exists():
        fm = re.match(r"^---\s*\n(.*?)\n---", notes.read_text(encoding="utf-8"), re.DOTALL)
        if fm:
            m = re.search(r"^title:\s*(.+)$", fm.group(1), re.MULTILINE)
            if m:
                return m.group(1).strip().strip('"').strip("'")
    return ""


def generate_book_index(book_dir: Path) -> str:
    """Render the book-level index.md: one linked row per chapter with a one-liner."""
    book_dir = Path(book_dir)
    chapters_dir = book_dir / CHAPTERS_SUBDIR
    lines = [f"# {book_dir.name}: chapters", "",
             "Per-chapter papers processed from this book. Each links to its own notes.",
             ""]
    if chapters_dir.is_dir():
        for chapter in sorted(chapters_dir.iterdir()):
            if not chapter.is_dir():
                continue
            lines.append(f"## [{chapter.name}](chapters/{chapter.name}/notes.md)")
            oneliner = _chapter_oneliner(chapter)
            if oneliner:
                lines.append(oneliner)
            lines.append("")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) >= 2 and argv[0] == "index":
        print(generate_book_index(Path(argv[1])), end="")
        return 0
    print("usage: book_scaffold.py index <book-dir>", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
