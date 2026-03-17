#!/usr/bin/env python3
"""Canonicalize paper tags in description.md files.

Reads a project-level tag map from papers/tag-canon.yaml, applies it to all
description.md files, rewrites tags in-place. Run generate-paper-index.py
afterward to rebuild the index.

The tag map file format is:
    # variant -> canonical
    F0: fundamental-frequency
    f0: fundamental-frequency
    ToBI: tobi
    stop-consonants: stops

Tags not in the map are left as-is. The map is applied transitively
(if A->B and B->C, then A->C).

Usage:
    python scripts/canonicalize-tags.py <project-root> [--dry-run]
"""

import re
import sys
from pathlib import Path

import yaml


def load_tag_map(papers_dir: Path) -> dict[str, str]:
    """Load tag canonicalization map from papers/tag-canon.yaml."""
    canon_path = papers_dir / "tag-canon.yaml"
    if not canon_path.exists():
        print(f"No tag-canon.yaml found at {canon_path}")
        print("Create one with entries like:  F0: fundamental-frequency")
        sys.exit(1)
    with open(canon_path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if not isinstance(raw, dict):
        print(f"tag-canon.yaml must be a YAML mapping, got {type(raw).__name__}")
        sys.exit(1)
    return {str(k): str(v) for k, v in raw.items()}


def canonicalize(tag: str, tag_map: dict[str, str]) -> str:
    """Return canonical form of a tag, applying the map transitively."""
    seen = set()
    while tag in tag_map and tag not in seen:
        seen.add(tag)
        tag = tag_map[tag]
    return tag


def process_file(
    desc_path: Path, tag_map: dict[str, str], dry_run: bool
) -> tuple[int, list[str]]:
    """Process one description.md. Returns (changes_made, list_of_changes)."""
    text = desc_path.read_text(encoding="utf-8")
    fm = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not fm:
        return 0, []

    frontmatter = fm.group(1)

    # Try inline format: tags: [tag1, tag2]
    inline = re.search(r"^tags:\s*\[([^\]]*)\]", frontmatter, re.MULTILINE)
    # Try list format: tags:\n- tag1\n- tag2
    list_match = re.search(
        r"^tags:\s*\n((?:\s*-\s*.+\n?)+)", frontmatter, re.MULTILINE
    )

    if inline:
        raw_tags = [t.strip() for t in inline.group(1).split(",") if t.strip()]
    elif list_match:
        raw_tags = [
            line.strip().lstrip("- ").strip()
            for line in list_match.group(1).splitlines()
            if line.strip().startswith("-")
        ]
    else:
        return 0, []

    new_tags = []
    changes = []
    for t in raw_tags:
        c = canonicalize(t, tag_map)
        if c != t:
            changes.append(f"  {t} -> {c}")
        if c not in new_tags:  # deduplicate after canonicalization
            new_tags.append(c)

    if not changes:
        return 0, []

    # Always rewrite as inline format for consistency
    new_tags_str = ", ".join(new_tags)
    new_line = f"tags: [{new_tags_str}]"

    if inline:
        old_match = inline.group(0)
    else:
        old_match = list_match.group(0).rstrip("\n")

    if not dry_run:
        new_text = text.replace(old_match, new_line, 1)
        desc_path.write_text(new_text, encoding="utf-8")

    return len(changes), changes


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("Usage: canonicalize-tags.py <project-root> [--dry-run]")
        sys.exit(0)

    project_root = Path(sys.argv[1]).resolve()
    papers_dir = project_root / "papers"
    dry_run = "--dry-run" in sys.argv

    if not papers_dir.is_dir():
        print(f"No papers/ directory at {papers_dir}")
        sys.exit(1)

    tag_map = load_tag_map(papers_dir)
    print(f"Loaded {len(tag_map)} tag mappings from tag-canon.yaml")

    total_files = 0
    total_changes = 0
    all_changes = []

    for desc in sorted(papers_dir.glob("*/description.md")):
        n, changes = process_file(desc, tag_map, dry_run)
        if n:
            total_files += 1
            total_changes += n
            paper = desc.parent.name
            all_changes.append((paper, changes))

    mode = "DRY RUN" if dry_run else "APPLIED"
    print(f"[{mode}] {total_changes} tag changes across {total_files} files\n")
    for paper, changes in all_changes:
        print(f"{paper}:")
        for c in changes:
            print(c)
        print()


if __name__ == "__main__":
    main()
