#!/usr/bin/env python3
"""Generate papers/index.md and tagged-papers/ symlinks from paper directories."""

import os
import re
import shutil
import sys
from pathlib import Path

import yaml


def resolve_project_root() -> Path:
    """Resolve project root from CLI arg or default to plugin-relative path."""
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).resolve()
    return Path(__file__).resolve().parent.parent


PROJECT_ROOT = resolve_project_root()
PAPERS_DIR = PROJECT_ROOT / "papers"
INDEX_MD = PAPERS_DIR / "index.md"
TAGGED_DIR = PAPERS_DIR / "tagged"


def read_description_body(description_path: Path) -> str:
    """Read description.md and return the body text (without YAML frontmatter)."""
    if not description_path.exists():
        return ""
    text = description_path.read_text(encoding="utf-8").strip()
    # Strip YAML frontmatter if present
    fm_match = re.match(r"^---\s*\n.*?\n---\s*\n?", text, re.DOTALL)
    if fm_match:
        text = text[fm_match.end():]
    # Strip legacy Tags: line
    text = re.sub(r"\n?Tags:\s*.+$", "", text, flags=re.MULTILINE)
    return text.strip()


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


def load_tag_registry(papers_dir: Path) -> tuple[set[str], dict[str, str]]:
    """Load canonical tags and alias map from papers/tags.yaml.

    Returns (canonical_tags, alias_map) where alias_map maps variant -> canonical.
    Returns (set(), {}) if tags.yaml doesn't exist.
    """
    tags_path = papers_dir / "tags.yaml"
    if not tags_path.exists():
        return set(), {}

    with open(tags_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict) or "tags" not in data:
        return set(), {}

    canonical = set()
    aliases = {}
    for tag_name, tag_info in data["tags"].items():
        canonical.add(tag_name)
        if isinstance(tag_info, dict) and "aliases" in tag_info:
            for alias in tag_info["aliases"]:
                aliases[alias] = tag_name

    return canonical, aliases


def canonicalize_tag(tag: str, aliases: dict[str, str]) -> str:
    """Return canonical form of a tag, resolving aliases."""
    return aliases.get(tag, tag)


def validate_tags(
    tags: list[str],
    canonical: set[str],
    aliases: dict[str, str],
) -> list[str]:
    """Validate tags against the registry. Returns list of warning strings."""
    if not canonical and not aliases:
        return []  # No registry loaded, skip validation
    warnings = []
    for tag in tags:
        if tag in canonical:
            continue
        if tag in aliases:
            warnings.append(f"Tag '{tag}' is an alias for '{aliases[tag]}' — consider updating")
        else:
            warnings.append(f"Tag '{tag}' is not in tags.yaml — consider adding it")
    return warnings


def main():
    if not PAPERS_DIR.is_dir():
        print(f"No papers/ directory found at {PAPERS_DIR}")
        return

    # Collect papers, descriptions, and tags
    papers: list[tuple[str, str, list[str]]] = []
    tag_map: dict[str, list[str]] = {}

    for d in sorted(PAPERS_DIR.iterdir()):
        if not d.is_dir() or d.name == "tagged" or not (d / "notes.md").exists():
            continue
        desc_path = d / "description.md"
        desc = read_description_body(desc_path)
        tags = parse_tags(desc_path)
        papers.append((d.name, desc, tags))
        for tag in tags:
            tag_map.setdefault(tag, []).append(d.name)

    # Load tag registry and validate/canonicalize
    canonical_tags, tag_aliases = load_tag_registry(PAPERS_DIR)
    if canonical_tags:
        all_warnings = []
        new_tag_map: dict[str, list[str]] = {}
        for i, (name, desc, tags) in enumerate(papers):
            canonicalized = [canonicalize_tag(t, tag_aliases) for t in tags]
            for tag in tags:
                warnings = validate_tags([tag], canonical_tags, tag_aliases)
                all_warnings.extend(f"  {name}: {w}" for w in warnings)
            if canonicalized != tags:
                papers[i] = (name, desc, canonicalized)
            for tag in canonicalized:
                new_tag_map.setdefault(tag, []).append(name)
        tag_map = new_tag_map
        if all_warnings:
            print(f"\nTag warnings ({len(all_warnings)}):")
            for w in all_warnings:
                print(w)

    # Write index.md
    lines = []
    for name, desc, tags in papers:
        tag_str = f"  ({', '.join(tags)})" if tags else ""
        lines.append(f"## {name}{tag_str}")
        if desc:
            lines.append(desc)
        lines.append("")
    INDEX_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Build tagged-papers/ symlink tree
    if TAGGED_DIR.exists():
        shutil.rmtree(TAGGED_DIR)
    TAGGED_DIR.mkdir()

    for tag, dirnames in sorted(tag_map.items()):
        tag_dir = TAGGED_DIR / tag
        tag_dir.mkdir(exist_ok=True)
        for dirname in sorted(dirnames):
            link = tag_dir / dirname
            target = os.path.relpath(PAPERS_DIR / dirname, tag_dir)
            link.symlink_to(target, target_is_directory=True)

    # Report
    untagged = [name for name, _, tags in papers if not tags]
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
