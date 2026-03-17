# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Generate claims.yaml from a paper's notes.md file.

Usage:
    uv run scripts/generate_claims.py <path-to-paper-dir> [--output claims.yaml]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any


def parse_parameter_table(text: str) -> list[dict[str, str]]:
    """Parse a markdown parameter table into a list of row dicts.

    Column headers become dict keys. Only non-empty values are included.
    """
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    if len(lines) < 2:
        return []

    # First line is the header
    header_line = lines[0]
    headers = [h.strip() for h in header_line.strip("|").split("|")]

    rows: list[dict[str, str]] = []
    for line in lines[2:]:  # skip header and separator
        if not line.startswith("|"):
            continue
        values = [v.strip() for v in line.strip("|").split("|")]
        row: dict[str, str] = {}
        for header, value in zip(headers, values):
            if header and value and value != "-":
                row[header] = value
        rows.append(row)

    return rows


def parse_range(range_str: str) -> dict[str, Any]:
    """Parse a range string into bounds or value.

    Formats:
        "55-110"  -> {"lower_bound": 55, "upper_bound": 110}
        "~0.5"    -> {"value": 0.5}
        "-"       -> {}
        "440"     -> {"value": 440}
    """
    s = range_str.strip()
    if s == "-" or not s:
        return {}

    # Approximate value: ~X
    if s.startswith("~"):
        val = s[1:]
        return {"value": _to_number(val)}

    # Range: X-Y (but not negative number)
    range_match = re.match(r"^(-?\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)$", s)
    if range_match:
        lo = _to_number(range_match.group(1))
        hi = _to_number(range_match.group(2))
        return {"lower_bound": lo, "upper_bound": hi}

    # Single value
    try:
        return {"value": _to_number(s)}
    except (ValueError, TypeError):
        return {}


def _to_number(s: str) -> int | float:
    """Convert string to int or float as appropriate."""
    s = s.strip()
    try:
        n = int(s)
        return n
    except ValueError:
        return float(s)


def parse_uncertainty(text: str) -> dict[str, Any]:
    """Parse uncertainty notation.

    Formats:
        "s.d. 0.29" -> {"uncertainty": 0.29, "uncertainty_type": "sd"}
        "s.e. 0.05" -> {"uncertainty": 0.05, "uncertainty_type": "se"}
    """
    text = text.strip()
    m = re.match(r"s\.d\.\s+(\d+(?:\.\d+)?)", text)
    if m:
        return {"uncertainty": float(m.group(1)), "uncertainty_type": "sd"}
    m = re.match(r"s\.e\.\s+(\d+(?:\.\d+)?)", text)
    if m:
        return {"uncertainty": float(m.group(1)), "uncertainty_type": "se"}
    return {}


def parse_equations(text: str) -> list[str]:
    """Extract $$...$$ delimited equation blocks from text."""
    # Match $$ ... $$ blocks (possibly multiline)
    pattern = re.compile(r"\$\$\s*\n(.*?)\n\s*\$\$", re.DOTALL)
    equations = []
    for m in pattern.finditer(text):
        eq = m.group(1).strip()
        if eq:
            equations.append(eq)
    return equations


def parse_testable_properties(text: str) -> list[str]:
    """Extract bullet items under 'Testable Properties' headers."""
    # Find sections starting with a heading containing "Testable Properties"
    lines = text.splitlines()
    in_section = False
    properties: list[str] = []

    for line in lines:
        stripped = line.strip()
        # Check for heading with "Testable Properties"
        if re.match(r"^#{1,6}\s+.*Testable Properties", stripped):
            in_section = True
            continue
        # Another heading ends the section
        if in_section and re.match(r"^#{1,6}\s+", stripped):
            in_section = False
            continue
        # Bullet item
        if in_section and re.match(r"^-\s+", stripped):
            prop = re.sub(r"^-\s+", "", stripped).strip()
            if prop:
                properties.append(prop)

    return properties


def _concept_name_from_param(name: str) -> str:
    """Derive a concept name from a parameter Name value."""
    return name.strip().lower().replace(" ", "_")


def generate_claims(paper_dir: Path) -> dict[str, Any]:
    """Generate a claims dict from a paper directory containing notes.md.

    Args:
        paper_dir: Path to the paper directory (e.g., Author_2000_Title/).
                   Must contain a notes.md file.

    Returns:
        A dict matching the ClaimFile schema with 'source' and 'claims' keys.
    """
    paper_name = paper_dir.name
    notes_path = paper_dir / "notes.md"
    notes_text = notes_path.read_text(encoding="utf-8")

    claims: list[dict[str, Any]] = []
    claim_counter = 0

    # --- Parameter claims from tables ---
    # Find all markdown tables in the text
    # Split into sections and find tables within parameter-related sections
    tables = _find_parameter_tables(notes_text)
    for table_text in tables:
        rows = parse_parameter_table(table_text)
        for row in rows:
            name = row.get("Name") or row.get("Parameter")
            if not name:
                continue
            claim_counter += 1
            claim: dict[str, Any] = {
                "id": f"claim{claim_counter}",
                "type": "parameter",
                "concept": _concept_name_from_param(name),
                "provenance": {
                    "paper": paper_name,
                    "page": 0,
                },
            }

            # Value from Default or Value column
            default_str = row.get("Default") or row.get("Value")
            if default_str is not None:
                try:
                    claim["value"] = _to_number(default_str)
                except (ValueError, TypeError):
                    pass

            # Range
            range_str = row.get("Range")
            if range_str:
                range_info = parse_range(range_str)
                if "lower_bound" in range_info:
                    claim["lower_bound"] = range_info["lower_bound"]
                    claim["upper_bound"] = range_info["upper_bound"]
                elif "value" in range_info and "value" not in claim:
                    claim["value"] = range_info["value"]

            # Unit
            unit = row.get("Units") or row.get("Unit")
            if unit and unit != "-":
                claim["unit"] = unit

            claims.append(claim)

    # --- Equation claims ---
    equations = parse_equations(notes_text)
    for eq in equations:
        claim_counter += 1
        claims.append({
            "id": f"claim{claim_counter}",
            "type": "equation",
            "expression": eq,
            "sympy": eq,
            "variables": [],
            "provenance": {
                "paper": paper_name,
                "page": 0,
            },
        })

    # --- Observation claims from testable properties ---
    properties = parse_testable_properties(notes_text)
    for prop in properties:
        claim_counter += 1
        claims.append({
            "id": f"claim{claim_counter}",
            "type": "observation",
            "statement": prop,
            "concepts": [],
            "provenance": {
                "paper": paper_name,
                "page": 0,
            },
        })

    return {
        "source": {
            "paper": paper_name,
        },
        "claims": claims,
    }


def _find_parameter_tables(text: str) -> list[str]:
    """Find markdown tables in the text that look like parameter tables.

    A parameter table has a header row with '|' separators and a separator
    row with dashes. We look for tables whose headers contain parameter-like
    column names (Name, Parameter, Symbol, Units, Default, Value, Range).
    """
    lines = text.splitlines()
    tables: list[str] = []
    i = 0
    param_columns = {"name", "parameter", "symbol", "units", "unit",
                     "default", "value", "range", "notes"}

    while i < len(lines):
        line = lines[i].strip()
        # Check if this looks like a table header row
        if "|" in line and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            # Separator row: |---|---|...|
            if re.match(r"^\|[\s\-|]+\|$", next_line):
                # Check if headers match parameter columns
                headers = {h.strip().lower() for h in line.strip("|").split("|")}
                if headers & param_columns:
                    # Collect the full table
                    table_lines = [lines[i], lines[i + 1]]
                    j = i + 2
                    while j < len(lines) and lines[j].strip().startswith("|"):
                        table_lines.append(lines[j])
                        j += 1
                    tables.append("\n".join(table_lines))
                    i = j
                    continue
        i += 1

    return tables


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate claims.yaml from a paper's notes.md"
    )
    parser.add_argument("paper_dir", type=Path, help="Path to the paper directory")
    parser.add_argument("--output", "-o", type=Path, default=None,
                        help="Output YAML file path (default: <paper_dir>/claims.yaml)")
    args = parser.parse_args()

    paper_dir = Path(args.paper_dir).resolve()
    if not (paper_dir / "notes.md").exists():
        print(f"Error: {paper_dir / 'notes.md'} not found", file=sys.stderr)
        sys.exit(1)

    try:
        import yaml
    except ImportError:
        print("Error: pyyaml is required. Install with: pip install pyyaml", file=sys.stderr)
        sys.exit(1)

    result = generate_claims(paper_dir)
    output_path = args.output or (paper_dir / "claims.yaml")

    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(result, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(f"Generated {len(result['claims'])} claims -> {output_path}")


if __name__ == "__main__":
    main()
