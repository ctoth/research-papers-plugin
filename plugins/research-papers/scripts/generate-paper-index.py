#!/usr/bin/env python3
"""Generate papers/index.md and tagged-papers/ symlinks from paper directories."""

import os
import re
import shutil
import sys
from pathlib import Path


def resolve_project_root() -> Path:
    """Resolve project root from CLI arg or default to plugin-relative path."""
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).resolve()
    return Path(__file__).resolve().parent.parent


PROJECT_ROOT = resolve_project_root()
PAPERS_DIR = PROJECT_ROOT / "papers"
INDEX_MD = PAPERS_DIR / "index.md"
TAGGED_DIR = PAPERS_DIR / "tagged"


def parse_tags(description_path: Path) -> list[str]:
    """Extract tags from YAML frontmatter or legacy Tags: line in description.md."""
    if not description_path.exists():
        return []
    text = description_path.read_text(encoding="utf-8")

    # YAML frontmatter: tags: [tag1, tag2] or tags:\n- tag1\n- tag2
    fm_match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if fm_match:
        frontmatter = fm_match.group(1)
        # Inline: tags: [tag1, tag2]
        inline = re.search(r"^tags:\s*\[([^\]]*)\]", frontmatter, re.MULTILINE)
        if inline:
            return [t.strip() for t in inline.group(1).split(",") if t.strip()]
        # List: tags:\n- tag1\n- tag2
        list_match = re.search(r"^tags:\s*\n((?:\s*-\s*.+\n?)+)", frontmatter, re.MULTILINE)
        if list_match:
            return [
                line.strip().lstrip("- ").strip()
                for line in list_match.group(1).splitlines()
                if line.strip().startswith("-")
            ]

    # Legacy fallback: Tags: tag1, tag2
    for line in text.splitlines():
        if line.startswith("Tags:"):
            return [t.strip() for t in line[5:].split(",") if t.strip()]

    return []


def main():
    if not PAPERS_DIR.is_dir():
        print(f"No papers/ directory found at {PAPERS_DIR}")
        return

    # Collect papers and their tags
    papers: list[tuple[str, list[str]]] = []
    tag_map: dict[str, list[str]] = {}

    for d in sorted(PAPERS_DIR.iterdir()):
        if not d.is_dir() or d.name == "tagged" or not (d / "notes.md").exists():
            continue
        tags = parse_tags(d / "description.md")
        papers.append((d.name, tags))
        for tag in tags:
            tag_map.setdefault(tag, []).append(d.name)

    # Write index.md
    lines = []
    for name, tags in papers:
        tag_str = f"  ({', '.join(tags)})" if tags else ""
        lines.append(f"- {name}{tag_str}")
    INDEX_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Build tagged-papers/ symlink tree
    if TAGGED_DIR.exists():
        shutil.rmtree(TAGGED_DIR)
    TAGGED_DIR.mkdir()

    for tag, dirnames in sorted(tag_map.items()):
        tag_dir = TAGGED_DIR / tag
        tag_dir.mkdir()
        for dirname in sorted(dirnames):
            link = tag_dir / dirname
            target = os.path.relpath(PAPERS_DIR / dirname, tag_dir)
            link.symlink_to(target, target_is_directory=True)

    # Report
    untagged = [name for name, tags in papers if not tags]
    print(f"Generated papers/index.md with {len(papers)} papers")
    print(f"Generated tagged-papers/ with {len(tag_map)} tags")
    for tag in sorted(tag_map):
        print(f"  {tag}: {len(tag_map[tag])} papers")
    if untagged:
        print(f"\nUntagged ({len(untagged)} papers — run tag-papers --all):")
        for name in untagged:
            print(f"  - {name}")


if __name__ == "__main__":
    main()
