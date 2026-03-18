# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Propose concept definitions from claims.yaml files.

Extracts unique concept names from paper claims, infers form and domain,
and creates propstore concept YAML files.

Usage:
    uv run propose_concepts.py <papers-dir> --output-dir <concepts-dir> [--forms-dir <forms-dir>]
"""
from __future__ import annotations

import argparse
import os
import re
from datetime import date
from pathlib import Path
from typing import Any

import yaml


# ── Unit → form inference ────────────────────────────────────────────

_UNIT_TO_FORM: dict[str, str] = {
    # Frequency
    "Hz": "frequency",
    "kHz": "frequency",
    # Time
    "s": "time",
    "ms": "time",
    "msec": "time",
    "sec": "time",
    # Pressure
    "Pa": "pressure",
    "kPa": "pressure",
    "cmH2O": "pressure",
    "hPa": "pressure",
    # Flow / volume
    "cm3/s": "flow",
    "L/s": "flow",
    "mL": "structural",  # volume, not flow rate
    "cm3/s2": "flow_derivative",
    # Level
    "dB": "level",
    "dB SPL": "level",
    "dB/oct": "level",
    "dB/octave": "level",
    "SD": "level",
    # Dimensionless
    "ratio": "amplitude_ratio",
    "dimensionless": "dimensionless_compound",
    "%": "amplitude_ratio",
    # Length → structural (no dedicated length form)
    "cm": "structural",
    "mm": "structural",
    "m": "structural",
    "mm²": "structural",
    # Counts → structural
    "count": "structural",
    "samples": "structural",
    "bits": "structural",
    "frames": "structural",
    "points": "structural",
    "degrees": "structural",
}

# Concept name patterns → form
_NAME_PATTERNS: list[tuple[re.Pattern, str]] = [
    # Exact matches for common short names
    (re.compile(r"^(f[0-6]|b[1-6]|bandwidth_[0-9]+)$", re.I), "frequency"),
    (re.compile(r"^(h[1-4]|oq|sq|cq)$", re.I), "amplitude_ratio"),
    # Pattern matches
    (re.compile(r"(^|_)(f[0-9]+|frequency|f0|pitch|bandwidth|formant)(_|$)", re.I), "frequency"),
    (re.compile(r"(^|_)(duration|time|period|onset|offset|latency|vot|closure)(_|$)", re.I), "time"),
    (re.compile(r"(^|_)(pressure|subglottal|psub)(_|$)", re.I), "pressure"),
    (re.compile(r"(^|_)(flow|airflow|ug)(_|$)", re.I), "flow"),
    (re.compile(r"(^|_)(level|intensity|spl|loudness|amplitude_of)(_|$)", re.I), "level"),
    (re.compile(r"(^|_)(ratio|quotient|oq|sq|cq|naq)(_|$)", re.I), "amplitude_ratio"),
    (re.compile(r"(^|_)(jitter|shimmer|hnr|snr|h1.*h2|spectral_tilt)(_|$)", re.I), "level"),
    (re.compile(r"(^|_)(rate|speed|velocity|speaking_rate)(_|$)", re.I), "frequency"),
    (re.compile(r"(^|_)(area|cross_section)(_|$)", re.I), "structural"),
    (re.compile(r"(^|_)(length|width|height|depth|radius|diameter|distance|thickness|volume|mass|density|stiffness)(_|$)", re.I), "structural"),
    (re.compile(r"(^|_)(coefficient|asymmetry|quotient|efficiency|factor)(_|$)", re.I), "amplitude_ratio"),
    (re.compile(r"(^|_)(number|count|size|samples|resolution)(_|$)", re.I), "structural"),
]


def infer_form(concept_name: str, units: dict[str, int]) -> str | None:
    """Infer a form from unit strings and concept name patterns.

    Args:
        concept_name: The concept's canonical name.
        units: Mapping of unit string -> occurrence count.
    """
    # Try unit-based inference, preferring the most common unit
    form_votes: dict[str, int] = {}
    for unit, count in units.items():
        form = _UNIT_TO_FORM.get(unit)
        if form:
            form_votes[form] = form_votes.get(form, 0) + count

    if form_votes:
        return max(form_votes, key=lambda f: form_votes[f])

    # Try name pattern matching
    for pattern, form_name in _NAME_PATTERNS:
        if pattern.search(concept_name):
            return form_name

    return None


def extract_concepts(papers_dir: Path) -> dict[str, dict[str, Any]]:
    """Extract unique concept names with metadata from claims.yaml files.

    Returns {concept_name: {"units": set, "count": int, "papers": set}}.
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
            except Exception:
                continue

            if not data or "claims" not in data:
                continue

            for claim in data["claims"]:
                if not isinstance(claim, dict):
                    continue

                # Collect concept references
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

                unit = claim.get("unit", "")

                for name in names:
                    if name not in concepts:
                        concepts[name] = {"units": {}, "count": 0, "papers": set()}
                    concepts[name]["count"] += 1
                    concepts[name]["papers"].add(paper_name)
                    if unit:
                        concepts[name]["units"][unit] = concepts[name]["units"].get(unit, 0) + 1

    return concepts


_KNOWN_SHORT_NAMES = frozenset({
    "f0", "f1", "f2", "f3", "f4", "f5", "f6",
    "b1", "b2", "b3", "b4", "b5", "b6",
    "h1", "h2", "h4",
    "oq", "sq", "cq",
})


def is_junk_name(name: str) -> bool:
    """Filter out names that are clearly not real concept names."""
    if name in _KNOWN_SHORT_NAMES:
        return False
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


def load_available_forms(forms_dir: Path | None) -> set[str]:
    """Load available form names from a forms directory."""
    if not forms_dir or not forms_dir.exists():
        return set()
    return {f.stem for f in forms_dir.iterdir() if f.suffix == ".yaml"}


def propose(
    papers_dir: Path,
    output_dir: Path,
    forms_dir: Path | None = None,
    domain: str = "speech",
    dry_run: bool = False,
) -> dict[str, Any]:
    """Generate proposed concept YAML files from claims.

    Returns stats dict.
    """
    raw_concepts = extract_concepts(papers_dir)
    available_forms = load_available_forms(forms_dir)

    # Filter junk
    concepts = {
        name: meta for name, meta in raw_concepts.items()
        if not is_junk_name(name)
    }

    # Read existing concepts to avoid duplicates
    existing_names: set[str] = set()
    existing_aliases: set[str] = set()
    next_counter = 1

    if output_dir.exists():
        for entry in sorted(output_dir.iterdir()):
            if entry.is_file() and entry.suffix == ".yaml":
                try:
                    data = yaml.safe_load(entry.read_text(encoding="utf-8"))
                except Exception:
                    continue
                if not data:
                    continue
                cn = data.get("canonical_name")
                if cn:
                    existing_names.add(cn)
                for alias in data.get("aliases", []) or []:
                    if isinstance(alias, dict) and alias.get("name"):
                        existing_aliases.add(alias["name"])
                cid = data.get("id", "")
                if isinstance(cid, str) and cid.startswith("concept"):
                    try:
                        num = int(cid[len("concept"):])
                        next_counter = max(next_counter, num + 1)
                    except ValueError:
                        pass

    # Also check counter file
    counters_dir = output_dir.parent / "counters"
    counter_file = counters_dir / "global.next"
    if counter_file.exists():
        try:
            file_counter = int(counter_file.read_text().strip())
            next_counter = max(next_counter, file_counter)
        except ValueError:
            pass

    stats = {"created": 0, "skipped_existing": 0, "skipped_junk": 0,
             "skipped_no_form": 0, "total_raw": len(raw_concepts)}

    stats["skipped_junk"] = len(raw_concepts) - len(concepts)

    if dry_run:
        for name in sorted(concepts.keys()):
            if name in existing_names:
                stats["skipped_existing"] += 1
                continue
            form = infer_form(name, concepts[name]["units"])
            if form and form not in available_forms and available_forms:
                form = None
            if not form:
                stats["skipped_no_form"] += 1
                continue
            print(f"  Would create: {name} (form={form}, refs={concepts[name]['count']})")
            stats["created"] += 1
        return stats

    output_dir.mkdir(parents=True, exist_ok=True)

    for name in sorted(concepts.keys()):
        if name in existing_names:
            stats["skipped_existing"] += 1
            continue

        meta = concepts[name]
        form = infer_form(name, meta["units"])

        # Validate form exists
        if form and form not in available_forms and available_forms:
            form = None
        if not form:
            stats["skipped_no_form"] += 1
            continue

        cid = f"concept{next_counter}"
        next_counter += 1

        data = {
            "id": cid,
            "canonical_name": name,
            "status": "proposed",
            "definition": f"Auto-proposed from {meta['count']} claim(s) across {len(meta['papers'])} paper(s).",
            "domain": domain,
            "created_date": str(date.today()),
            "form": form,
        }

        filepath = output_dir / f"{name}.yaml"
        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        stats["created"] += 1

    # Update counter file
    counters_dir.mkdir(parents=True, exist_ok=True)
    counter_file.write_text(f"{next_counter}\n")

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Propose concept definitions from claims.yaml files"
    )
    parser.add_argument("papers_dir", type=Path,
                        help="Directory containing paper subdirs with claims.yaml")
    parser.add_argument("--output-dir", "-o", type=Path, required=True,
                        help="Output directory for concept YAML files")
    parser.add_argument("--forms-dir", type=Path, default=None,
                        help="Forms directory to validate form references")
    parser.add_argument("--domain", default="speech",
                        help="Domain prefix for all concepts (default: speech)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be created without writing")
    args = parser.parse_args()

    stats = propose(
        papers_dir=args.papers_dir.resolve(),
        output_dir=args.output_dir.resolve(),
        forms_dir=args.forms_dir.resolve() if args.forms_dir else None,
        domain=args.domain,
        dry_run=args.dry_run,
    )

    print(f"\nResults:")
    print(f"  Total raw concept names: {stats['total_raw']}")
    print(f"  Skipped (junk names):    {stats['skipped_junk']}")
    print(f"  Skipped (existing):      {stats['skipped_existing']}")
    print(f"  Skipped (no form match): {stats['skipped_no_form']}")
    print(f"  Created:                 {stats['created']}")


if __name__ == "__main__":
    main()
