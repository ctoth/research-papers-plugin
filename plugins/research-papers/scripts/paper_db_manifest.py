#!/usr/bin/env python3
"""Load the paper database manifest from papers/db.yaml."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


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


def load_paper_db_manifest(project_root: Path) -> PaperDbManifest:
    manifest_path = project_root / "papers" / "db.yaml"
    if not manifest_path.exists():
        return DEFAULT_MANIFEST

    raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return DEFAULT_MANIFEST

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
