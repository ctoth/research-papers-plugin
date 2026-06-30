#!/usr/bin/env python3
"""Schema linter for the paper database.

This is a read-only mechanical linter over papers/ that enforces:
  - canonical notes.md frontmatter fields
  - required file presence
  - canonical description.md tag frontmatter
  - cross-reference section status
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_paper_corpus import (
    PaperAudit,
    collect_audits,
    extract_frontmatter_keys,
    read_text,
)
from paper_db_manifest import load_paper_db_manifest
from build_keymap import validate_cite_key_first, derive_cite_key
from _textutil import find_em_dashes

CONTENT_MD_FILES = ("notes.md", "description.md", "abstract.md", "citations.md")
ABSTRACT_REQUIRED_SECTIONS = ("Original Text (Verbatim)", "Our Interpretation")


def resolve_project_root() -> Path:
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).resolve()
    return Path(__file__).resolve().parent.parent


PROJECT_ROOT = resolve_project_root()
PAPERS_DIR = PROJECT_ROOT / "papers"


@dataclass(frozen=True)
class Violation:
    code: str
    paper: str
    detail: str = ""


def notes_frontmatter_keys(notes_path: Path) -> tuple[str, ...]:
    if not notes_path.exists():
        return ()
    return extract_frontmatter_keys(read_text(notes_path))


def lint_paper(audit: PaperAudit, papers_root: Path) -> list[Violation]:
    violations: list[Violation] = []
    paper_dir = papers_root / audit.name
    notes_path = paper_dir / "notes.md"
    manifest = load_paper_db_manifest(papers_root.parent)
    canonical_keys = set(
        manifest.canonical_notes_required
        + manifest.canonical_notes_recommended
        + manifest.canonical_notes_optional
    )

    if not audit.has_notes:
        violations.append(Violation("NOTES_MISSING", audit.name))
        return violations

    if not audit.has_description:
        violations.append(Violation("DESCRIPTION_MISSING", audit.name))
    if not audit.has_abstract:
        violations.append(Violation("ABSTRACT_MISSING", audit.name))
    if not audit.has_citations:
        violations.append(Violation("CITATIONS_MISSING", audit.name))
    if not audit.has_pdf and not audit.has_pngs:
        violations.append(Violation("SOURCE_MISSING", audit.name))

    # F4: a paper folder name must equal its bibtex cite_key. Directory identity
    # and cite key were deliberately decoupled under B5; that decision is
    # overturned (2026-06-30) -- dir == cite_key is now a required invariant.
    meta_path = paper_dir / "metadata.json"
    if meta_path.exists():
        try:
            metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        except (ValueError, json.JSONDecodeError):
            metadata = None
        if metadata is not None:
            cite_key = derive_cite_key(metadata, audit.name)
            if cite_key != audit.name:
                violations.append(
                    Violation("DIR_KEY_MISMATCH", audit.name, f"cite_key={cite_key}")
                )

    keys = notes_frontmatter_keys(notes_path)
    key_set = set(keys)

    for required in manifest.canonical_notes_required:
        if required not in key_set:
            violations.append(Violation("NOTES_REQUIRED_MISSING", audit.name, required))

    for alias, canonical in sorted(manifest.legacy_aliases.items()):
        if alias in key_set:
            violations.append(Violation("NOTES_FIELD_ALIAS", audit.name, f"{alias}->{canonical}"))

    for key in sorted(key_set):
        if key not in canonical_keys and key not in manifest.legacy_aliases:
            violations.append(Violation("NOTES_UNKNOWN_FIELD", audit.name, key))

    if audit.description_style != "yaml-frontmatter":
        violations.append(Violation("DESCRIPTION_TAGS_MISSING", audit.name, audit.description_style))

    crossref_status = audit.crossref_status
    if crossref_status == "missing-section":
        violations.append(Violation("CROSSREFS_MISSING", audit.name))
    elif crossref_status == "legacy-bold-refs":
        violations.append(Violation("CROSSREFS_LEGACY_BOLD_REFS", audit.name))

    return violations


def _collection_paper_dirs(papers_root: Path) -> list[Path]:
    return [
        d for d in sorted(papers_root.iterdir())
        if d.is_dir() and d.name != "tagged" and (d / "notes.md").exists()
    ]


def _canonical_tags(papers_root: Path) -> set[str] | None:
    """Canonical tag names from tags.yaml, or None to skip the registration check."""
    p = papers_root / "tags.yaml"
    if not p.exists():
        return None
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return set((data.get("tags") or {}).keys())


def _description_tags(desc_path: Path) -> list[str]:
    if not desc_path.exists():
        return []
    fm = re.match(r"^---\s*\n(.*?)\n---", desc_path.read_text(encoding="utf-8"), re.DOTALL)
    if not fm:
        return []
    inline = re.search(r"^tags:\s*\[([^\]]*)\]", fm.group(1), re.MULTILINE)
    if inline:
        return [t.strip() for t in inline.group(1).split(",") if t.strip()]
    block = re.search(r"^tags:\s*\n((?:\s*-\s*.+\n?)+)", fm.group(1), re.MULTILINE)
    if block:
        return [ln.strip().lstrip("- ").strip()
                for ln in block.group(1).splitlines() if ln.strip().startswith("-")]
    return []


def lint_collection(papers_root: Path) -> list[Violation]:
    """Cross-file collection invariants that per-paper lint does not cover (F8)."""
    violations: list[Violation] = []
    paper_dirs = _collection_paper_dirs(papers_root)
    dir_count = len(paper_dirs)

    # Count agreement: dirs == index entries == ledger lines.
    index_path = papers_root / "index.md"
    if index_path.exists():
        index_count = len(re.findall(r"(?m)^## ", index_path.read_text(encoding="utf-8")))
        if index_count != dir_count:
            violations.append(Violation("COUNT_MISMATCH", "(collection)",
                                        f"dirs={dir_count} index={index_count}"))
    ledger_path = papers_root / "_reader_done.tsv"
    if ledger_path.exists():
        ledger_count = len([ln for ln in ledger_path.read_text(encoding="utf-8").splitlines() if ln.strip()])
        if ledger_count != dir_count:
            violations.append(Violation("COUNT_MISMATCH", "(collection)",
                                        f"dirs={dir_count} ledger={ledger_count}"))

    canonical_tags = _canonical_tags(papers_root)

    for d in paper_dirs:
        meta = d / "metadata.json"
        if not meta.exists():
            violations.append(Violation("METADATA_MISSING", d.name))
        else:
            try:
                if not validate_cite_key_first(meta.read_text(encoding="utf-8")):
                    violations.append(Violation("CITE_KEY_NOT_FIRST", d.name))
            except (ValueError, json.JSONDecodeError):
                violations.append(Violation("METADATA_INVALID_JSON", d.name))

        abstract = d / "abstract.md"
        if abstract.exists():
            text = abstract.read_text(encoding="utf-8")
            if any(section not in text for section in ABSTRACT_REQUIRED_SECTIONS):
                violations.append(Violation("ABSTRACT_SECTIONS", d.name))

        for fname in CONTENT_MD_FILES:
            f = d / fname
            if f.exists():
                for line, col in find_em_dashes(f.read_text(encoding="utf-8")):
                    violations.append(Violation("EM_DASH", d.name, f"{fname}:{line}:{col}"))

        if canonical_tags is not None:
            for tag in _description_tags(d / "description.md"):
                if tag not in canonical_tags:
                    violations.append(Violation("TAG_NOT_REGISTERED", d.name, tag))

    return violations


def render_violations(violations: list[Violation]) -> str:
    by_code: dict[str, list[Violation]] = defaultdict(list)
    for violation in violations:
        by_code[violation.code].append(violation)

    summary = Counter(violation.code for violation in violations)
    affected_papers = {violation.paper for violation in violations}

    lines = [
        f"paper-schema-lint violations={len(violations)} papers={len(affected_papers)}",
        "",
        "Violation summary",
    ]
    for code, count in summary.most_common():
        lines.append(f"  {count:>4}  {code}")

    for code in sorted(by_code):
        lines.append("")
        lines.append(f"{code} ({len(by_code[code])})")
        for violation in sorted(by_code[code], key=lambda item: (item.paper, item.detail)):
            if violation.detail:
                lines.append(f"  - {violation.paper}: {violation.detail}")
            else:
                lines.append(f"  - {violation.paper}")

    return "\n".join(lines)


def main() -> int:
    audits = collect_audits(PAPERS_DIR)
    violations: list[Violation] = []
    for audit in audits:
        violations.extend(lint_paper(audit, PAPERS_DIR))
    violations.extend(lint_collection(PAPERS_DIR))

    print(render_violations(violations))
    return 0 if not violations else 2


if __name__ == "__main__":
    raise SystemExit(main())
