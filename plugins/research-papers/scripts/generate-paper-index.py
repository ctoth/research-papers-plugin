#!/usr/bin/env python3
"""Generate papers/index.md from paper directories."""

from pathlib import Path

PAPERS_DIR = Path(__file__).resolve().parent.parent / "papers"
INDEX_MD = PAPERS_DIR / "index.md"


def main():
    if not PAPERS_DIR.is_dir():
        print(f"No papers/ directory found at {PAPERS_DIR}")
        return

    entries = sorted(
        d.name
        for d in PAPERS_DIR.iterdir()
        if d.is_dir() and (d / "notes.md").exists()
    )

    INDEX_MD.write_text(
        "\n".join(f"- {name}" for name in entries) + "\n",
        encoding="utf-8",
    )

    print(f"Generated papers/index.md with {len(entries)} paper entries")


if __name__ == "__main__":
    main()
