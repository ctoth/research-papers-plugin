# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Sync a paper directory into propstore's source-oriented CLI surface.

Usage:
    uv run scripts/sync_propstore_source.py <paper-dir> [--finalize] [--promote] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


def infer_source_name(paper_dir: Path) -> str:
    """Use the paper directory name as the propstore source name."""
    return paper_dir.resolve().name


def load_metadata(paper_dir: Path) -> dict[str, Any]:
    """Load metadata.json when present, else return an empty mapping."""
    metadata_path = paper_dir / "metadata.json"
    if not metadata_path.exists():
        return {}
    loaded = json.loads(metadata_path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def infer_origin(paper_dir: Path, metadata: dict[str, Any]) -> tuple[str, str]:
    """Infer the best source origin from metadata or on-disk artifacts."""
    for key in ("doi", "DOI"):
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return "doi", value.strip()
    for key in ("arxiv_id", "arxiv", "arxivId"):
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return "arxiv", value.strip()
    for key in ("url", "pdf_url", "source_url"):
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return "url", value.strip()
    paper_pdf = paper_dir / "paper.pdf"
    if paper_pdf.exists():
        return "file", str(paper_pdf.resolve())
    return "manual", infer_source_name(paper_dir)


def load_concept_inventory(paper_dir: Path) -> list[dict[str, str]]:
    """Load paper-local concept proposals from concepts.yaml when present."""
    concepts_path = paper_dir / "concepts.yaml"
    if not concepts_path.exists():
        return []
    loaded = yaml.safe_load(concepts_path.read_text(encoding="utf-8")) or {}
    concepts = loaded.get("concepts", [])
    if not isinstance(concepts, list):
        raise ValueError(f"{concepts_path} has non-list 'concepts'")
    result: list[dict[str, str]] = []
    for index, entry in enumerate(concepts, start=1):
        if not isinstance(entry, dict):
            raise ValueError(f"{concepts_path} concept #{index} must be a mapping")
        local_name = entry.get("local_name") or entry.get("proposed_name")
        definition = entry.get("definition")
        form = entry.get("form")
        if not all(isinstance(value, str) and value.strip() for value in (local_name, definition, form)):
            raise ValueError(f"{concepts_path} concept #{index} is missing local_name/definition/form")
        result.append(
            {
                "local_name": str(local_name).strip(),
                "definition": str(definition).strip(),
                "form": str(form).strip(),
            }
        )
    return result


def build_sync_commands(
    paper_dir: Path,
    *,
    finalize: bool = False,
    promote: bool = False,
) -> list[list[str]]:
    """Build the `pks source *` command sequence for a paper directory."""
    paper_dir = paper_dir.resolve()
    source_name = infer_source_name(paper_dir)
    metadata = load_metadata(paper_dir)
    origin_type, origin_value = infer_origin(paper_dir, metadata)

    commands: list[list[str]] = [
        [
            "pks",
            "source",
            "init",
            source_name,
            "--kind",
            "academic_paper",
            "--origin-type",
            origin_type,
            "--origin-value",
            origin_value,
        ]
    ]

    notes_path = paper_dir / "notes.md"
    if notes_path.exists():
        commands.append(
            ["pks", "source", "write-notes", source_name, "--file", str(notes_path)]
        )

    metadata_path = paper_dir / "metadata.json"
    if metadata_path.exists():
        commands.append(
            ["pks", "source", "write-metadata", source_name, "--file", str(metadata_path)]
        )

    for concept in load_concept_inventory(paper_dir):
        commands.append(
            [
                "pks",
                "source",
                "propose-concept",
                source_name,
                "--name",
                concept["local_name"],
                "--definition",
                concept["definition"],
                "--form",
                concept["form"],
            ]
        )

    claims_path = paper_dir / "claims.yaml"
    if claims_path.exists():
        commands.append(
            ["pks", "source", "add-claim", source_name, "--batch", str(claims_path)]
        )

    justifications_path = paper_dir / "justifications.yaml"
    if justifications_path.exists():
        commands.append(
            [
                "pks",
                "source",
                "add-justification",
                source_name,
                "--batch",
                str(justifications_path),
            ]
        )

    stances_path = paper_dir / "stances.yaml"
    if stances_path.exists():
        commands.append(
            ["pks", "source", "add-stance", source_name, "--batch", str(stances_path)]
        )

    if finalize or promote:
        commands.append(["pks", "source", "finalize", source_name])
    if promote:
        commands.append(["pks", "source", "promote", source_name])
    return commands


def run_sync_commands(commands: list[list[str]], *, dry_run: bool = False) -> None:
    """Execute or print the planned command sequence."""
    for command in commands:
        if dry_run:
            print(" ".join(command))
            continue
        subprocess.run(command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync a paper directory into propstore source branches."
    )
    parser.add_argument("paper_dir", type=Path, help="Paper directory containing extracted artifacts")
    parser.add_argument("--finalize", action="store_true", help="Run pks source finalize at the end")
    parser.add_argument("--promote", action="store_true", help="Run finalize and promote at the end")
    parser.add_argument("--dry-run", action="store_true", help="Print commands instead of executing them")
    args = parser.parse_args()

    paper_dir = args.paper_dir.resolve()
    if not paper_dir.is_dir():
        print(f"Error: {paper_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    commands = build_sync_commands(
        paper_dir,
        finalize=args.finalize,
        promote=args.promote,
    )
    run_sync_commands(commands, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
