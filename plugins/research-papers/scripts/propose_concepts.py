# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Extract concept names from claims.yaml files.

Collects unique concept references from paper claims. Does NOT infer forms
or assign domain knowledge — that is the LLM agent's job during
register-concepts. This script is mechanical extraction only.

Usage:
    uv run propose_concepts.py multi <papers-dir> --output-dir <concepts-dir>
    uv run propose_concepts.py pks-batch <paper-dir> [--registry-dir <dir>] [--output <path>]
"""
from __future__ import annotations

import argparse
import logging
import os
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

import yaml


def extract_concepts(papers_dir: Path) -> dict[str, dict[str, Any]]:
    """Extract unique concept names with metadata from claims.yaml files.

    Returns {concept_name: {"units": {unit: count}, "count": int, "papers": set}}.
    """
    concepts: dict[str, dict[str, Any]] = {}

    for dirpath, _, filenames in os.walk(papers_dir):
        for fname in filenames:
            if fname != "claims.yaml":
                continue
            fpath = Path(dirpath) / fname
            paper_name = Path(dirpath).name
            try:
                with open(fpath, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
            except Exception as exc:
                logger.warning("Failed to load %s: %s", fpath, exc)
                continue

            if not data or "claims" not in data:
                continue

            for claim in data["claims"]:
                if not isinstance(claim, dict):
                    continue

                names: list[str] = []
                c = claim.get("concept")
                if c and isinstance(c, str):
                    names.append(c)
                tc = claim.get("target_concept")
                if tc and isinstance(tc, str):
                    names.append(tc)
                cs = claim.get("concepts")
                if isinstance(cs, list):
                    for item in cs:
                        if isinstance(item, str):
                            names.append(item)
                # equation claims: variables[].concept
                variables = claim.get("variables")
                if isinstance(variables, list):
                    for entry in variables:
                        if isinstance(entry, dict):
                            vc = entry.get("concept")
                            if isinstance(vc, str) and vc:
                                names.append(vc)
                # model claims: parameters[].concept
                parameters = claim.get("parameters")
                if isinstance(parameters, list):
                    for entry in parameters:
                        if isinstance(entry, dict):
                            pc = entry.get("concept")
                            if isinstance(pc, str) and pc:
                                names.append(pc)

                unit = claim.get("unit", "")

                for name in names:
                    if name not in concepts:
                        concepts[name] = {"units": {}, "count": 0, "papers": set()}
                    concepts[name]["count"] += 1
                    concepts[name]["papers"].add(paper_name)
                    if unit:
                        concepts[name]["units"][unit] = concepts[name]["units"].get(unit, 0) + 1

    return concepts


def is_junk_name(name: str) -> bool:
    """Filter out names that are clearly not real concept names."""
    # Pure numbers
    if re.match(r'^[\d._]+$', name):
        return True
    # Single character
    if len(name) == 1:
        return True
    # Very short numeric-ish strings
    if len(name) <= 2 and re.match(r'^[a-z]?\d+$', name):
        return True
    return False


def _load_registry_names(registry_dir: Path | None) -> set[str]:
    """Load canonical concept names from a registry directory."""
    if not registry_dir or not registry_dir.exists():
        return set()
    names: set[str] = set()
    for entry in registry_dir.iterdir():
        if entry.is_file() and entry.suffix == ".yaml":
            try:
                data = yaml.safe_load(entry.read_text(encoding="utf-8"))
            except Exception:
                continue
            if data and isinstance(data, dict):
                cn = data.get("canonical_name")
                if cn:
                    names.add(cn)
    return names


def _extract_concepts_single_paper(paper_dir: Path) -> dict[str, dict[str, Any]]:
    """Extract concepts from a single paper's claims.yaml."""
    concepts: dict[str, dict[str, Any]] = {}
    claims_path = paper_dir / "claims.yaml"
    if not claims_path.exists():
        return concepts

    try:
        with open(claims_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception:
        return concepts

    if not data or "claims" not in data:
        return concepts

    for claim in data["claims"]:
        if not isinstance(claim, dict):
            continue

        names: list[str] = []
        c = claim.get("concept")
        if c and isinstance(c, str):
            names.append(c)
        tc = claim.get("target_concept")
        if tc and isinstance(tc, str):
            names.append(tc)
        cs = claim.get("concepts")
        if isinstance(cs, list):
            for item in cs:
                if isinstance(item, str):
                    names.append(item)
        # equation claims: variables[].concept
        variables = claim.get("variables")
        if isinstance(variables, list):
            for entry in variables:
                if isinstance(entry, dict):
                    vc = entry.get("concept")
                    if isinstance(vc, str) and vc:
                        names.append(vc)
        # model claims: parameters[].concept
        parameters = claim.get("parameters")
        if isinstance(parameters, list):
            for entry in parameters:
                if isinstance(entry, dict):
                    pc = entry.get("concept")
                    if isinstance(pc, str) and pc:
                        names.append(pc)

        unit = claim.get("unit", "")

        for name in names:
            if name not in concepts:
                concepts[name] = {"units": {}, "count": 0}
            concepts[name]["count"] += 1
            if unit:
                concepts[name]["units"][unit] = concepts[name]["units"].get(unit, 0) + 1

    return concepts


def propose_pks_batch(
    paper_dir: Path,
    registry_dir: Path | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Produce a pks-batch-format concepts.yaml for a single paper.

    Extracts concept names and units from claims.yaml. Does NOT assign forms —
    the LLM agent does that during register-concepts enrichment.

    Returns the batch dict with a 'concepts' list. If output_path is given,
    also writes it to disk.
    """
    raw_concepts = _extract_concepts_single_paper(paper_dir)
    registry_names = _load_registry_names(registry_dir)

    concepts_list: list[dict[str, Any]] = []
    for name in sorted(raw_concepts.keys()):
        if is_junk_name(name):
            continue

        meta = raw_concepts[name]

        entry: dict[str, Any] = {
            "local_name": name,
            "proposed_name": name,
            "definition": f"Auto-proposed from {meta['count']} claim(s).",
            "form": "structural",  # placeholder — agent enriches this
            "units_observed": dict(meta["units"]) if meta["units"] else {},
            "in_registry": name in registry_names,
        }

        concepts_list.append(entry)

    result: dict[str, Any] = {"concepts": concepts_list}

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(result, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract concept names from claims.yaml files"
    )
    subparsers = parser.add_subparsers(dest="command")

    # Multi-paper mode (list all concepts across a collection)
    multi = subparsers.add_parser("multi", help="List concepts across all papers")
    multi.add_argument("papers_dir", type=Path,
                       help="Directory containing paper subdirs with claims.yaml")

    # Single-paper pks-batch mode
    batch = subparsers.add_parser("pks-batch", help="Produce pks-batch concepts.yaml for one paper")
    batch.add_argument("paper_dir", type=Path,
                       help="Single paper directory with claims.yaml")
    batch.add_argument("--registry-dir", type=Path, default=None,
                       help="Existing concept registry for dedup checking")
    batch.add_argument("--output", "-o", type=Path, default=None,
                       help="Output path (default: <paper_dir>/concepts.yaml)")

    args = parser.parse_args()

    if args.command == "pks-batch":
        paper_dir = args.paper_dir.resolve()
        output_path = args.output.resolve() if args.output else paper_dir / "concepts.yaml"
        result = propose_pks_batch(
            paper_dir=paper_dir,
            registry_dir=args.registry_dir.resolve() if args.registry_dir else None,
            output_path=output_path,
        )
        print(f"Wrote {len(result['concepts'])} concepts to {output_path}")
    elif args.command == "multi":
        concepts = extract_concepts(args.papers_dir.resolve())
        for name in sorted(concepts.keys()):
            if is_junk_name(name):
                continue
            meta = concepts[name]
            units_str = ", ".join(f"{u}({c})" for u, c in meta["units"].items()) if meta["units"] else "none"
            print(f"  {name}: {meta['count']} refs across {len(meta['papers'])} papers, units: {units_str}")
        print(f"\nTotal: {len(concepts)} unique concept names")
    else:
        parser.print_help()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
