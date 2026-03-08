#!/usr/bin/env python3
"""Migrate existing paper collection to new format.

Handles two mechanical conversions:
1. description.md: "Tags: x, y" line → YAML frontmatter tags: [x, y]
2. notes.md cross-references: **PaperName** → [[PaperName]] in Collection Cross-References sections

Safe to run multiple times (idempotent).
"""

import re
import sys
from pathlib import Path


def resolve_papers_dir() -> Path:
    """Resolve papers directory from CLI arg or default to plugin-relative path."""
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).resolve() / "papers"
    return Path(__file__).resolve().parent.parent / "papers"


PAPERS_DIR = resolve_papers_dir()


def migrate_description_tags(desc_path: Path) -> bool:
    """Convert legacy Tags: line to YAML frontmatter. Returns True if changed."""
    if not desc_path.exists():
        return False

    text = desc_path.read_text(encoding="utf-8")

    # Already has frontmatter with tags — nothing to do
    fm_match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if fm_match and "tags:" in fm_match.group(1):
        return False

    # Find legacy Tags: line
    tags_match = re.search(r"^Tags:\s*(.+)$", text, re.MULTILINE)
    if not tags_match:
        return False

    tags = [t.strip() for t in tags_match.group(1).split(",") if t.strip()]
    if not tags:
        return False

    # Remove the Tags: line (and any preceding blank line)
    body = re.sub(r"\n?\nTags:\s*.+$", "", text, flags=re.MULTILINE).strip()

    # Remove existing empty frontmatter if present
    body = re.sub(r"^---\s*\n---\s*\n?", "", body)

    # Prepend frontmatter
    tag_list = ", ".join(tags)
    new_text = f"---\ntags: [{tag_list}]\n---\n{body}\n"
    desc_path.write_text(new_text, encoding="utf-8")
    return True


def migrate_crossref_links(notes_path: Path) -> int:
    """Convert **PaperDir** → [[PaperDir]] in cross-reference sections. Returns count."""
    if not notes_path.exists():
        return 0

    text = notes_path.read_text(encoding="utf-8")
    if "## Collection Cross-References" not in text:
        return 0

    # Only convert in the cross-references section (from that heading to end of file)
    idx = text.index("## Collection Cross-References")
    before = text[:idx]
    section = text[idx:]

    # Match **Author_Year_Something** patterns (typical dirname format)
    # But not **See also:** or other non-dirname bold text
    count = 0

    def replace_bold_dirname(m):
        nonlocal count
        name = m.group(1)
        # Only convert if it looks like a dirname (has underscores, starts with capital)
        if "_" in name and name[0].isupper() and not name.startswith("See"):
            count += 1
            return f"[[{name}]]"
        return m.group(0)

    new_section = re.sub(r"\*\*([A-Z][A-Za-z0-9_]+)\*\*", replace_bold_dirname, section)

    if count > 0:
        notes_path.write_text(before + new_section, encoding="utf-8")
    return count


def main():
    if not PAPERS_DIR.is_dir():
        print(f"No papers/ directory found at {PAPERS_DIR}")
        return

    tags_migrated = 0
    links_migrated = 0

    for d in sorted(PAPERS_DIR.iterdir()):
        if not d.is_dir():
            continue

        if migrate_description_tags(d / "description.md"):
            tags_migrated += 1
            print(f"  {d.name}: migrated Tags → frontmatter")

        n = migrate_crossref_links(d / "notes.md")
        if n > 0:
            links_migrated += 1
            print(f"  {d.name}: converted {n} bold refs → wikilinks")

    print(f"\nMigrated {tags_migrated} description.md files (Tags → frontmatter)")
    print(f"Migrated {links_migrated} notes.md files (bold → wikilinks)")


if __name__ == "__main__":
    main()
