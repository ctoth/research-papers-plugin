#!/usr/bin/env python3
"""Load the paper database manifest from papers/db.yaml."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class PaperDbManifest:
    schema_version: int
    database_kind: str
    notes_format: str
    description_format: str
    required_files: tuple[str, ...]
    recommended_files: tuple[str, ...]
    canonical_notes_required: tuple[str, ...]
    canonical_notes_recommended: tuple[str, ...]
    canonical_notes_optional: tuple[str, ...]
    legacy_aliases: dict[str, str]


DEFAULT_MANIFEST = PaperDbManifest(
    schema_version=1,
    database_kind="research-papers",
    notes_format="notes-frontmatter-v1",
    description_format="description-frontmatter-tags-v1",
    required_files=("notes.md", "description.md"),
    recommended_files=("abstract.md", "citations.md"),
    canonical_notes_required=("title", "year"),
    canonical_notes_recommended=("authors", "venue", "doi_url"),
    canonical_notes_optional=(
        "pages",
        "affiliation",
        "affiliations",
        "institution",
        "publisher",
        "supervisor",
        "supervisors",
        "funding",
        "pacs",
        "note",
        "correction_doi",
        "citation",
    ),
    legacy_aliases={
        "author": "authors",
        "doi": "doi_url",
        "url": "doi_url",
        "journal": "venue",
        "type": "venue",
        "paper": "title",
    },
)


def parse_inline_list(value: str) -> tuple[str, ...]:
    value = value.strip()
    if not value.startswith("[") or not value.endswith("]"):
        return ()
    inner = value[1:-1].strip()
    if not inner:
        return ()
    return tuple(part.strip() for part in inner.split(",") if part.strip())


def parse_scalar(value: str):
    value = value.strip()
    if re.fullmatch(r"\d+", value):
        return int(value)
    if value.startswith('"') and value.endswith('"') and len(value) >= 2:
        return value[1:-1]
    return value


def load_paper_db_manifest(project_root: Path) -> PaperDbManifest:
    manifest_path = project_root / "papers" / "db.yaml"
    if not manifest_path.exists():
        return DEFAULT_MANIFEST

    raw: dict[str, object] = {}
    nested_key: str | None = None

    for raw_line in manifest_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue

        if line.startswith("  ") and nested_key is not None:
            match = re.match(r"^\s{2}([A-Za-z0-9_]+):\s*(.+)$", line)
            if not match:
                continue
            nested = raw.setdefault(nested_key, {})
            assert isinstance(nested, dict)
            nested[match.group(1)] = parse_scalar(match.group(2))
            continue

        match = re.match(r"^([A-Za-z0-9_]+):(?:\s*(.+))?$", line)
        if not match:
            continue
        key = match.group(1)
        value = match.group(2)
        if value is None or value == "":
            raw[key] = {}
            nested_key = key
            continue

        nested_key = None
        if value.strip().startswith("["):
            raw[key] = parse_inline_list(value)
        else:
            raw[key] = parse_scalar(value)

    return PaperDbManifest(
        schema_version=int(raw.get("schema_version", DEFAULT_MANIFEST.schema_version)),
        database_kind=str(raw.get("database_kind", DEFAULT_MANIFEST.database_kind)),
        notes_format=str(raw.get("notes_format", DEFAULT_MANIFEST.notes_format)),
        description_format=str(raw.get("description_format", DEFAULT_MANIFEST.description_format)),
        required_files=tuple(raw.get("required_files", DEFAULT_MANIFEST.required_files)),
        recommended_files=tuple(raw.get("recommended_files", DEFAULT_MANIFEST.recommended_files)),
        canonical_notes_required=tuple(
            raw.get("canonical_notes_required", DEFAULT_MANIFEST.canonical_notes_required)
        ),
        canonical_notes_recommended=tuple(
            raw.get("canonical_notes_recommended", DEFAULT_MANIFEST.canonical_notes_recommended)
        ),
        canonical_notes_optional=tuple(
            raw.get("canonical_notes_optional", DEFAULT_MANIFEST.canonical_notes_optional)
        ),
        legacy_aliases=dict(raw.get("legacy_aliases", DEFAULT_MANIFEST.legacy_aliases)),
    )
