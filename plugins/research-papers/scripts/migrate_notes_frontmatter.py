#!/usr/bin/env python3
"""Migrate notes.md title/metadata blocks into YAML frontmatter.

This is a mechanical migration:
  - extracts the leading `# Title`
  - extracts leading `**Key:** Value` metadata lines before the first section
  - writes canonical YAML frontmatter using normalized snake_case keys
  - removes the old metadata block from the body

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


def normalize_key(key: str) -> str:
    key = key.strip().lower()
    key = re.sub(r"[^a-z0-9]+", "_", key)
    return key.strip("_")


def yaml_scalar(value: object) -> str:
    if isinstance(value, int):
        return str(value)
    text = str(value)
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def strip_existing_frontmatter(text: str) -> tuple[str, bool]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.DOTALL)
    if not match:
        return text, False
    return text[match.end():], True


def extract_notes_metadata(text: str) -> tuple[dict[str, object], str]:
    body, _ = strip_existing_frontmatter(text)
    lines = body.splitlines()

    metadata: dict[str, object] = {}
    i = 0

    while i < len(lines) and not lines[i].strip():
        i += 1

    if i < len(lines) and lines[i].startswith("# "):
        metadata["title"] = lines[i][2:].strip()
        i += 1

    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("## "):
            break
        match = re.match(r"^\*\*([^*]+):\*\*\s*(.+)$", line)
        if not match:
            break
        key = normalize_key(match.group(1))
        value_text = match.group(2).strip()
        if key == "year" and re.fullmatch(r"\d{4}", value_text):
            metadata[key] = int(value_text)
        else:
            metadata[key] = value_text
        i += 1

    remaining_lines = lines[i:]
    while remaining_lines and not remaining_lines[0].strip():
        remaining_lines.pop(0)
    remaining_body = "\n".join(remaining_lines).rstrip()
    if remaining_body:
        remaining_body = f"{remaining_body}\n"
    return metadata, remaining_body


def build_frontmatter(metadata: dict[str, object]) -> str:
    ordered_keys = ["title", "authors", "author", "year", "venue"]
    other_keys = sorted(key for key in metadata if key not in ordered_keys)
    keys = [key for key in ordered_keys if key in metadata] + other_keys
    lines = ["---"]
    for key in keys:
        lines.append(f"{key}: {yaml_scalar(metadata[key])}")
    lines.append("---")
    return "\n".join(lines)


def migrate_notes_text(text: str) -> tuple[str, bool]:
    body, had_frontmatter = strip_existing_frontmatter(text)
    metadata, remaining_body = extract_notes_metadata(body)
    if had_frontmatter or "title" not in metadata:
        return text, False

    frontmatter = build_frontmatter(metadata)
    title_line = f"# {metadata['title']}"
    pieces = [frontmatter, "", title_line]
    if remaining_body:
        pieces.extend(["", remaining_body.rstrip()])
    migrated = "\n".join(pieces).rstrip() + "\n"
    if migrated == text:
        return text, False
    return migrated, True


def migrate_notes_file(notes_path: Path) -> bool:
    if not notes_path.exists():
        return False
    original = notes_path.read_text(encoding="utf-8")
    migrated, changed = migrate_notes_text(original)
    if changed:
        notes_path.write_text(migrated, encoding="utf-8")
    return changed


def main() -> int:
    if not PAPERS_DIR.is_dir():
        print(f"No papers/ directory found at {PAPERS_DIR}")
        return 1

    migrated_count = 0
    for paper_dir in sorted(PAPERS_DIR.iterdir()):
        if not paper_dir.is_dir() or paper_dir.name == "tagged":
            continue
        if migrate_notes_file(paper_dir / "notes.md"):
            migrated_count += 1
            print(f"  {paper_dir.name}: migrated notes.md metadata -> frontmatter")

    print(f"\nMigrated {migrated_count} notes.md files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
