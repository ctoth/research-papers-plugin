#!/usr/bin/env python3
"""Audit the papers/ corpus for format drift and database-shape inconsistencies.

This is a read-only mechanical audit. It reports:
  - required/recommended file coverage
  - notes.md format families
  - notes.md metadata key signatures
  - description.md tag/frontmatter styles
  - cross-reference status
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


def resolve_project_root() -> Path:
    """Resolve project root from CLI arg or default to plugin-relative path."""
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).resolve()
    return Path(__file__).resolve().parent.parent


PROJECT_ROOT = resolve_project_root()
PAPERS_DIR = PROJECT_ROOT / "papers"
PAPER_MARKER_FILES = (
    "notes.md",
    "description.md",
    "abstract.md",
    "citations.md",
    "paper.pdf",
)


@dataclass(frozen=True)
class NotesFormat:
    family: str
    metadata_keys: tuple[str, ...]
    has_frontmatter: bool
    has_title: bool


@dataclass(frozen=True)
class PaperAudit:
    name: str
    has_notes: bool
    has_description: bool
    has_abstract: bool
    has_citations: bool
    has_pdf: bool
    has_pngs: bool
    description_style: str
    has_tags: bool
    crossref_status: str
    notes_format: NotesFormat | None


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def strip_frontmatter(text: str) -> tuple[str, bool]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.DOTALL)
    if not match:
        return text, False
    return text[match.end():], True


def extract_frontmatter_keys(text: str) -> tuple[str, ...]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.DOTALL)
    if not match:
        return ()

    keys: list[str] = []
    for line in match.group(1).splitlines():
        if not line or line.startswith(" ") or line.startswith("\t"):
            continue
        key_match = re.match(r"^([A-Za-z0-9_]+):", line)
        if key_match:
            keys.append(key_match.group(1))
    return tuple(keys)


def analyze_notes_format(notes_text: str) -> NotesFormat:
    frontmatter_keys = extract_frontmatter_keys(notes_text)
    body, has_frontmatter = strip_frontmatter(notes_text)
    lines = body.splitlines()

    title_line = ""
    metadata_keys: list[str] = list(frontmatter_keys)
    seen_title = False

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("## "):
            break
        if not seen_title and line.startswith("# "):
            title_line = line
            seen_title = True
            continue
        match = re.match(r"^\*\*([^*]+):\*\*\s*(.+)$", line)
        if match and not has_frontmatter:
            metadata_keys.append(match.group(1).strip())

    has_title = bool(title_line)
    has_metadata = bool(metadata_keys)

    if has_frontmatter and has_title and has_metadata:
        family = "frontmatter+title+metadata-block"
    elif has_frontmatter and has_title:
        family = "frontmatter+title"
    elif has_title and has_metadata:
        family = "title+metadata-block"
    elif has_title:
        family = "title-only"
    elif has_frontmatter:
        family = "frontmatter-only"
    else:
        family = "other"

    return NotesFormat(
        family=family,
        metadata_keys=tuple(metadata_keys),
        has_frontmatter=has_frontmatter,
        has_title=has_title,
    )


def analyze_description_style(description_text: str) -> tuple[str, bool]:
    frontmatter_match = re.match(r"^---\s*\n(.*?)\n---", description_text, re.DOTALL)
    if frontmatter_match:
        frontmatter = frontmatter_match.group(1)
        has_tags = bool(
            re.search(r"^tags:\s*\[[^\]]*\]", frontmatter, re.MULTILINE)
            or re.search(r"^tags:\s*\n(?:\s*-\s*.+\n?)+", frontmatter, re.MULTILINE)
        )
        return ("yaml-frontmatter" if has_tags else "frontmatter-no-tags", has_tags)

    legacy_tags = re.search(r"^Tags:\s*(.+)$", description_text, re.MULTILINE)
    if legacy_tags:
        return ("legacy-tags-line", True)

    return ("plain-body", False)


def analyze_crossrefs(notes_text: str) -> str:
    if "## Collection Cross-References" not in notes_text:
        return "missing-section"
    if re.search(r"\*\*[A-Z][A-Za-z0-9_]*_\d{4}[A-Za-z0-9_]*\*\*", notes_text):
        return "legacy-bold-refs"
    return "wikilinks-or-empty"


def looks_like_paper_dir(paper_dir: Path) -> bool:
    if not paper_dir.is_dir() or paper_dir.name == "tagged":
        return False
    if any((paper_dir / name).exists() for name in PAPER_MARKER_FILES):
        return True
    return (paper_dir / "pngs").is_dir()


def audit_paper_dir(paper_dir: Path) -> PaperAudit:
    notes_path = paper_dir / "notes.md"
    description_path = paper_dir / "description.md"
    abstract_path = paper_dir / "abstract.md"
    citations_path = paper_dir / "citations.md"
    pdf_path = paper_dir / "paper.pdf"
    pngs_path = paper_dir / "pngs"

    notes_text = read_text(notes_path) if notes_path.exists() else ""
    description_text = read_text(description_path) if description_path.exists() else ""

    notes_format = analyze_notes_format(notes_text) if notes_text else None
    description_style, has_tags = (
        analyze_description_style(description_text) if description_text else ("missing", False)
    )
    crossref_status = analyze_crossrefs(notes_text) if notes_text else "missing-notes"

    return PaperAudit(
        name=paper_dir.name,
        has_notes=notes_path.exists(),
        has_description=description_path.exists(),
        has_abstract=abstract_path.exists(),
        has_citations=citations_path.exists(),
        has_pdf=pdf_path.exists(),
        has_pngs=pngs_path.is_dir(),
        description_style=description_style,
        has_tags=has_tags,
        crossref_status=crossref_status,
        notes_format=notes_format,
    )


def collect_audits(papers_dir: Path) -> list[PaperAudit]:
    audits: list[PaperAudit] = []
    for paper_dir in sorted(papers_dir.iterdir()):
        if not looks_like_paper_dir(paper_dir):
            continue
        audits.append(audit_paper_dir(paper_dir))
    return audits


def signature_for_keys(keys: tuple[str, ...]) -> str:
    return "|".join(keys) if keys else "(none)"


def format_counter(title: str, counter: Counter[str], limit: int | None = None) -> list[str]:
    lines = [title]
    items = counter.most_common(limit)
    if not items:
        lines.append("  <none>")
        return lines
    for key, count in items:
        lines.append(f"  {count:>4}  {key}")
    return lines


def format_named_list(title: str, names: list[str], limit: int = 20) -> list[str]:
    lines = [f"{title} ({len(names)})"]
    if not names:
        lines.append("  <none>")
        return lines
    for name in names[:limit]:
        lines.append(f"  - {name}")
    if len(names) > limit:
        lines.append(f"  ... {len(names) - limit} more")
    return lines


def render_report(audits: list[PaperAudit]) -> str:
    total = len(audits)
    notes_family_counts = Counter(
        audit.notes_format.family if audit.notes_format else "missing-notes"
        for audit in audits
    )
    metadata_signature_counts = Counter(
        signature_for_keys(audit.notes_format.metadata_keys)
        for audit in audits
        if audit.notes_format is not None
    )
    description_style_counts = Counter(audit.description_style for audit in audits)
    crossref_counts = Counter(audit.crossref_status for audit in audits)

    notes_missing = [audit.name for audit in audits if not audit.has_notes]
    description_missing = [audit.name for audit in audits if not audit.has_description]
    notes_frontmatter = [audit.name for audit in audits if audit.notes_format and audit.notes_format.has_frontmatter]
    notes_no_structured_metadata = [
        audit.name
        for audit in audits
        if audit.notes_format is not None and len(audit.notes_format.metadata_keys) == 0
    ]
    description_without_tags = [audit.name for audit in audits if audit.has_description and not audit.has_tags]
    citations_missing = [audit.name for audit in audits if not audit.has_citations]
    abstract_missing = [audit.name for audit in audits if not audit.has_abstract]
    source_missing = [audit.name for audit in audits if not audit.has_pdf and not audit.has_pngs]

    lines = [
        f"paper-corpus-audit total={total}",
        "",
        *format_counter("Notes format families", notes_family_counts),
        "",
        *format_counter("Notes metadata key signatures", metadata_signature_counts, limit=20),
        "",
        *format_counter("Description styles", description_style_counts),
        "",
        *format_counter("Cross-reference status", crossref_counts),
        "",
        *format_named_list("Notes.md missing", notes_missing),
        "",
        *format_named_list("Description.md missing", description_missing),
        "",
        *format_named_list("Notes with YAML frontmatter", notes_frontmatter),
        "",
        *format_named_list("Notes without structured metadata keys", notes_no_structured_metadata),
        "",
        *format_named_list("Description without tags", description_without_tags),
        "",
        *format_named_list("Abstract missing", abstract_missing),
        "",
        *format_named_list("Citations missing", citations_missing),
        "",
        *format_named_list("No paper.pdf and no pngs/", source_missing),
    ]
    return "\n".join(lines)


def main() -> int:
    if not PAPERS_DIR.is_dir():
        print(f"No papers/ directory found at {PAPERS_DIR}")
        return 1

    audits = collect_audits(PAPERS_DIR)
    print(render_report(audits))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
