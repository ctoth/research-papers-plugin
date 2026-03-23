#!/usr/bin/env python3
"""Schema linter for the paper database.

This is a read-only mechanical linter over papers/ that enforces:
  - canonical notes.md frontmatter fields
  - required file presence
  - canonical description.md tag frontmatter
  - cross-reference section status
"""

from __future__ import annotations

import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_paper_corpus import (
    PaperAudit,
    collect_audits,
    extract_frontmatter_keys,
    read_text,
)
from paper_db_manifest import load_paper_db_manifest


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

    print(render_violations(violations))
    return 0 if not violations else 2


if __name__ == "__main__":
    raise SystemExit(main())
