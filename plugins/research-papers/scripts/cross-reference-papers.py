#!/usr/bin/env python3
"""
Cross-reference all papers in the collection.

For each paper with citations.md, finds which cited papers are already
in our collection and which are new leads. Appends a "Collection
Cross-References" section to each paper's notes.md.

Phase 1: mechanical matching only (author+year string matching).
"""

import re
from pathlib import Path

PAPERS_DIR = Path(__file__).parent.parent / "papers"
CLAUDE_MD = PAPERS_DIR / "CLAUDE.md"


def parse_collection_index():
    """Extract (dirname, author, year) tuples from papers/CLAUDE.md headers."""
    text = CLAUDE_MD.read_text(encoding="utf-8")
    entries = []
    for match in re.finditer(r"^## (\S+)", text, re.MULTILINE):
        dirname = match.group(1)
        # Parse author and year from dirname like "Fant_1985_LFModelGlottalFlow"
        parts = dirname.split("_")
        author = parts[0]
        # Find the year (4-digit number)
        year = None
        for p in parts[1:]:
            if re.match(r"^\d{4}$", p):
                year = p
                break
        entries.append({
            "dirname": dirname,
            "author": author,
            "year": year,
            "dir_path": PAPERS_DIR / dirname,
        })
    return entries


def search_citations_for_match(citations_text, author, year):
    """Check if a citations.md text references a given author+year."""
    if not year:
        return False
    # Look for author name near the year (within ~100 chars)
    # Common patterns: "Author (year)", "Author, year", "Author et al. (year)"
    # Also handle "Author and Coauthor (year)"

    # Normalize for case-insensitive matching
    author_lower = author.lower()

    # Simple approach: both author and year appear in the same line or nearby
    lines = citations_text.split("\n")
    for line in lines:
        line_lower = line.lower()
        if author_lower in line_lower and year in line:
            return True

    return False


def parse_key_citations(citations_text):
    """Extract the 'Key Citations for Follow-up' section."""
    # Find the section
    match = re.search(
        r"##\s*Key Citations.*?\n(.*?)(?:\n##|\n---|\Z)",
        citations_text,
        re.DOTALL | re.IGNORECASE,
    )
    if match:
        return match.group(1).strip()
    return ""


def already_has_crossrefs(notes_path):
    """Check if notes.md already has cross-references."""
    if not notes_path.exists():
        return True  # No notes.md to update
    text = notes_path.read_text(encoding="utf-8")
    return "## Collection Cross-References" in text


def build_crossref_section(found_in_collection, key_citations_not_found):
    """Build the markdown cross-reference section."""
    lines = ["\n---\n", "## Collection Cross-References\n"]

    if found_in_collection:
        lines.append("### Already in Collection")
        for entry in sorted(found_in_collection, key=lambda e: e["dirname"]):
            lines.append(f"- **{entry['dirname']}**")
        lines.append("")
    else:
        lines.append("### Already in Collection")
        lines.append("- (none found)")
        lines.append("")

    if key_citations_not_found:
        lines.append("### New Leads (Not Yet in Collection)")
        for citation in key_citations_not_found:
            lines.append(f"- {citation}")
        lines.append("")

    return "\n".join(lines)


def process_paper(paper_dir, collection):
    """Process one paper: find cross-references and update notes.md."""
    dirname = paper_dir.name
    citations_path = paper_dir / "citations.md"
    notes_path = paper_dir / "notes.md"

    if not citations_path.exists():
        return None, "no citations.md"

    if not notes_path.exists():
        return None, "no notes.md"

    if already_has_crossrefs(notes_path):
        return None, "already has cross-refs"

    citations_text = citations_path.read_text(encoding="utf-8")

    # Find which collection papers are cited
    found_in_collection = []
    for entry in collection:
        # Don't match self
        if entry["dirname"] == dirname:
            continue
        if search_citations_for_match(citations_text, entry["author"], entry["year"]):
            found_in_collection.append(entry)

    # Find key citations not in collection
    key_section = parse_key_citations(citations_text)
    key_citations_not_found = []
    if key_section:
        for line in key_section.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Check if any collection paper matches this line
            matched = False
            for entry in collection:
                if entry["author"].lower() in line.lower() and entry["year"] and entry["year"] in line:
                    matched = True
                    break
            if not matched and len(line) > 5:
                # Clean up the line (remove leading -, *, numbers)
                line = re.sub(r"^[-*\d.)\]]+\s*", "", line)
                if line:
                    key_citations_not_found.append(line)

    # Build and append section
    section = build_crossref_section(found_in_collection, key_citations_not_found)

    with open(notes_path, "a", encoding="utf-8") as f:
        f.write(section)

    return found_in_collection, f"OK: {len(found_in_collection)} in collection"


def main():
    collection = parse_collection_index()
    print(f"Collection index: {len(collection)} papers\n")

    # Get all paper directories
    paper_dirs = sorted([
        d for d in PAPERS_DIR.iterdir()
        if d.is_dir() and (d / "citations.md").exists()
    ])

    print(f"Papers with citations.md: {len(paper_dirs)}\n")

    total_updated = 0
    total_skipped = 0
    total_links = 0

    for paper_dir in paper_dirs:
        result, status = process_paper(paper_dir, collection)
        if result is not None:
            total_updated += 1
            total_links += len(result)
            found_names = [e["dirname"] for e in result]
            print(f"  {paper_dir.name}: {len(result)} cross-refs")
            if found_names:
                for name in sorted(found_names):
                    print(f"    -> {name}")
        else:
            total_skipped += 1
            print(f"  {paper_dir.name}: SKIP ({status})")

    print(f"\n--- Summary ---")
    print(f"Updated: {total_updated}")
    print(f"Skipped: {total_skipped}")
    print(f"Total cross-reference links: {total_links}")


if __name__ == "__main__":
    main()
