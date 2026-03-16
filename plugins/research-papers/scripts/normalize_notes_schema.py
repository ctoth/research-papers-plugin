#!/usr/bin/env python3
"""Normalize notes.md frontmatter to the canonical paper schema.

Mechanical transformations only:
  - alias keys -> canonical keys
  - fill missing `year` from paper directory name
  - reorder keys canonically
  - preserve unknown keys and body text

Safe to run multiple times (idempotent).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def resolve_papers_dir() -> Path:
    """Resolve papers directory from CLI arg or default to plugin-relative path."""
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).resolve() / "papers"
    return Path(__file__).resolve().parent.parent / "papers"


PAPERS_DIR = resolve_papers_dir()

ALIASES = {
    "author": "authors",
    "doi": "doi_url",
    "url": "doi_url",
    "journal": "venue",
    "type": "venue",
    "paper": "title",
}

CANONICAL_ORDER = [
    "title",
    "authors",
    "year",
    "venue",
    "doi_url",
    "pages",
    "affiliation",
    "affiliations",
    "institution",
    "publisher",
    "supervisor",
    "supervisors",
    "funding",
    "pacs",
    "note",
    "correction_doi",
    "citation",
]


def strip_frontmatter(text: str) -> tuple[str, str | None]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.DOTALL)
    if not match:
        return text, None
    return text[match.end():], match.group(1)


def parse_frontmatter(frontmatter_text: str) -> dict[str, object]:
    metadata: dict[str, object] = {}
    for line in frontmatter_text.splitlines():
        if not line or line.startswith(" ") or line.startswith("\t"):
            continue
        match = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", line)
        if not match:
            continue
        key = match.group(1)
        value = match.group(2).strip()
        if value.startswith('"') and value.endswith('"') and len(value) >= 2:
            value = value[1:-1].replace('\\"', '"').replace("\\\\", "\\")
        if key == "year" and re.fullmatch(r"\d{4}", value):
            metadata[key] = int(value)
        else:
            metadata[key] = value
    return metadata


def yaml_scalar(value: object) -> str:
    if isinstance(value, int):
        return str(value)
    text = str(value)
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def year_from_dirname(dirname: str) -> int | None:
    match = re.search(r"_(18|19|20)\d{2}(?:_|$)", dirname)
    if not match:
        return None
    return int(match.group(0).strip("_"))


def normalize_metadata(metadata: dict[str, object], paper_name: str) -> tuple[dict[str, object], bool]:
    normalized = dict(metadata)
    changed = False

    for alias, canonical in ALIASES.items():
        if alias not in normalized:
            continue
        if canonical not in normalized:
            normalized[canonical] = normalized[alias]
        del normalized[alias]
        changed = True

    if "year" not in normalized:
        inferred_year = year_from_dirname(paper_name)
        if inferred_year is not None:
            normalized["year"] = inferred_year
            changed = True

    return normalized, changed


def build_frontmatter(metadata: dict[str, object]) -> str:
    ordered_keys = [key for key in CANONICAL_ORDER if key in metadata]
    remaining_keys = sorted(key for key in metadata if key not in CANONICAL_ORDER)
    lines = ["---"]
    for key in [*ordered_keys, *remaining_keys]:
        lines.append(f"{key}: {yaml_scalar(metadata[key])}")
    lines.append("---")
    return "\n".join(lines)


def normalize_notes_text(text: str, paper_name: str) -> tuple[str, bool]:
    body, frontmatter_text = strip_frontmatter(text)
    if frontmatter_text is None:
        return text, False

    metadata = parse_frontmatter(frontmatter_text)
    normalized, changed = normalize_metadata(metadata, paper_name)
    frontmatter = build_frontmatter(normalized)
    normalized_text = f"{frontmatter}\n\n{body.lstrip()}".rstrip() + "\n"

    if normalized_text != text:
        changed = True
    return normalized_text, changed


def normalize_notes_file(notes_path: Path, paper_name: str) -> bool:
    if not notes_path.exists():
        return False
    original = notes_path.read_text(encoding="utf-8")
    normalized, changed = normalize_notes_text(original, paper_name)
    if changed:
        notes_path.write_text(normalized, encoding="utf-8")
    return changed


def main() -> int:
    if not PAPERS_DIR.is_dir():
        print(f"No papers/ directory found at {PAPERS_DIR}")
        return 1

    changed_count = 0
    for paper_dir in sorted(PAPERS_DIR.iterdir()):
        if not paper_dir.is_dir() or paper_dir.name == "tagged":
            continue
        if normalize_notes_file(paper_dir / "notes.md", paper_dir.name):
            changed_count += 1
            print(f"  {paper_dir.name}: normalized notes.md schema")

    print(f"\nNormalized {changed_count} notes.md files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
