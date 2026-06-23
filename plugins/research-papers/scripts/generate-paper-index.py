#!/usr/bin/env python3
"""Generate papers/index.md and tagged-papers/ symlinks from paper directories."""

import os
import re
import shutil
import sys
from pathlib import Path

import yaml


def resolve_project_root() -> Path:
    """Resolve project root from the first positional CLI arg (skipping flags)."""
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("--insert", "--refresh"):
            i += 2  # skip the flag and its value
            continue
        if a.startswith("-"):
            i += 1
            continue
        return Path(a).resolve()
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


def load_notes_title(notes_path: Path) -> str:
    """Read the pretty `title:` from a notes.md YAML frontmatter (empty if absent)."""
    if not notes_path.exists():
        return ""
    text = notes_path.read_text(encoding="utf-8")
    fm = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not fm:
        return ""
    m = re.search(r"^title:\s*(.+)$", fm.group(1), re.MULTILINE)
    if not m:
        return ""
    return m.group(1).strip().strip('"').strip("'")


def render_index_header(name: str, title: str, tags: list[str]) -> str:
    """Build a linked index header: ``## [title](name/notes.md)  (tags)``.

    The header text is a markdown link to the paper's notes.md (not the bare
    directory name), with two spaces before the tag parenthesis. Falls back to
    the directory name when no pretty title is available.
    """
    display = title or name
    tag_str = f"  ({', '.join(tags)})" if tags else ""
    return f"## [{display}]({name}/notes.md){tag_str}"


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
            warnings.append(f"Tag '{tag}' is an alias for '{aliases[tag]}' - consider updating")
        else:
            warnings.append(f"Tag '{tag}' is not in tags.yaml - consider adding it")
    return warnings


def parse_index_entries(text: str) -> tuple[str, list[tuple[str | None, str]]]:
    """Split index.md into (preamble, [(dir_name, verbatim_block), ...]).

    Each block runs from one ``## `` header to the next (or EOF) and is kept
    byte-for-byte so untouched entries are never reformatted.
    """
    matches = list(re.finditer(r"(?m)^## ", text))
    if not matches:
        return text, []
    preamble = text[: matches[0].start()]
    entries: list[tuple[str | None, str]] = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[start:end]
        nm = re.search(r"^## \[.*?\]\(([^/]+)/notes\.md\)", block)
        entries.append((nm.group(1) if nm else None, block))
    return preamble, entries


def render_entry_block(name: str, title: str, tags: list[str], desc: str = "") -> str:
    """Render one index entry block (header + optional desc + trailing blank)."""
    header = render_index_header(name, title, tags)
    if desc:
        return f"{header}\n{desc}\n\n"
    return f"{header}\n\n"


def insert_entry(index_text: str, name: str, title: str,
                 tags: list[str], desc: str = "") -> str:
    """Insert or replace one entry in place, sorted by dir name (case-sensitive).

    Every other entry's bytes are preserved exactly.
    """
    preamble, entries = parse_index_entries(index_text)
    entries = [(n, b) for (n, b) in entries if n != name]
    entries.append((name, render_entry_block(name, title, tags, desc)))
    entries.sort(key=lambda nb: nb[0] or "")
    return preamble + "".join(b for _, b in entries)


def bump_tag_counts(tags_yaml_text: str, tags: list[str], delta: int = 1) -> str:
    """Increment per-tag `count:` for each tag, registering new tags in sort order."""
    data = yaml.safe_load(tags_yaml_text) or {}
    tagmap = dict(data.get("tags") or {})
    for tag in tags:
        entry = tagmap.get(tag)
        if isinstance(entry, dict):
            entry = dict(entry)
            entry["count"] = int(entry.get("count", 0)) + delta
            tagmap[tag] = entry
        else:
            tagmap[tag] = {"count": delta}
    data["tags"] = {k: tagmap[k] for k in sorted(tagmap)}
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)


def insert_paper(papers_dir: Path, name: str) -> None:
    """Idempotently insert/refresh one paper's index entry and bump tag counts.

    Does NOT rebuild the tagged/ tree.
    """
    papers_dir = Path(papers_dir)
    d = papers_dir / name
    title = load_notes_title(d / "notes.md")
    desc = read_description_body(d / "description.md")
    tags = parse_tags(d / "description.md")

    index_path = papers_dir / "index.md"
    index_text = index_path.read_text(encoding="utf-8") if index_path.exists() else ""
    index_path.write_text(insert_entry(index_text, name, title, tags, desc), encoding="utf-8")

    tags_path = papers_dir / "tags.yaml"
    if tags_path.exists() and tags:
        tags_path.write_text(
            bump_tag_counts(tags_path.read_text(encoding="utf-8"), tags), encoding="utf-8")


def main():
    argv = sys.argv[1:]
    insert_dir = None
    rebuild_tagged = False
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--insert", "--refresh"):
            insert_dir = argv[i + 1] if i + 1 < len(argv) else None
            i += 2
            continue
        if a == "--rebuild-tagged":
            rebuild_tagged = True
            i += 1
            continue
        i += 1

    if insert_dir:
        insert_paper(PAPERS_DIR, insert_dir)
        print(f"Updated index entry for {insert_dir}")
        return

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

    # Write index.md (linked headers: ## [title](dir/notes.md)  (tags))
    lines = []
    for name, desc, tags in papers:
        title = load_notes_title(PAPERS_DIR / name / "notes.md")
        lines.append(render_index_header(name, title, tags))
        if desc:
            lines.append(desc)
        lines.append("")
    INDEX_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Build tagged-papers/ symlink tree only when explicitly requested.
    # The unconditional rmtree+recreate is destructive, and symlink creation is
    # unreliable on Windows; not all collections use the tagged/ tree (B2/F5).
    if rebuild_tagged:
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
    if rebuild_tagged:
        print(f"Generated tagged-papers/ with {len(tag_map)} tags")
    for tag in sorted(tag_map):
        print(f"  {tag}: {len(tag_map[tag])} papers")
    if untagged:
        print(f"\nUntagged ({len(untagged)} papers — run tag-papers --all):")
        for name in untagged:
            print(f"  - {name}")


if __name__ == "__main__":
    main()
