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
import unicodedata
from pathlib import Path
from typing import Any


# Units commonly found in column headers of parameter tables
_UNIT_PATTERN = re.compile(
    r"\b(Hz|dB|ms|Pa|kHz|MHz|sec|s|%|ratio|octave|semitone)\b", re.IGNORECASE
)

# Pattern to extract a unit from a column header like "D_inh (ms)" or "F1 (Hz)"
_HEADER_UNIT_PATTERN = re.compile(r"\((\w+)\)\s*$")


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
        "60-150 Hz" -> {"lower_bound": 60, "upper_bound": 150, "unit": "Hz"}
        "~0.5"    -> {"value": 0.5}
        "-"       -> {}
        "440"     -> {"value": 440}
    """
    s = range_str.strip()
    if s == "-" or not s:
        return {}

    # Normalize en-dash and em-dash to hyphen
    s = s.replace("\u2013", "-").replace("\u2014", "-")

    # Strip parenthetical suffixes like "(female)", "(consistent)"
    s = re.sub(r"\s*\([^)]*\)\s*$", "", s).strip()

    # Strip markdown bold markers
    s = s.replace("**", "")

    # Strip trailing unit (e.g., "60-150 Hz" -> "60-150", unit="Hz")
    unit_match = re.search(r"\s+(Hz|dB|ms|Pa|kHz|%|sec|s)\s*$", s, re.IGNORECASE)
    unit = None
    if unit_match:
        unit = unit_match.group(1)
        s = s[:unit_match.start()].strip()

    # Strip any remaining non-numeric trailing text (e.g., "4 m" -> "4")
    s = re.sub(r"\s+[a-zA-Z].*$", "", s).strip()

    if not s:
        return {}

    # Approximate value: ~X
    if s.startswith("~"):
        val = s[1:]
        try:
            result = {"value": _to_number(val)}
            if unit:
                result["unit"] = unit
            return result
        except (ValueError, TypeError):
            return {}

    # Range: X-Y (but not negative number)
    range_match = re.match(r"^(-?\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)$", s)
    if range_match:
        lo = _to_number(range_match.group(1))
        hi = _to_number(range_match.group(2))
        result: dict[str, Any] = {"lower_bound": lo, "upper_bound": hi}
        if unit:
            result["unit"] = unit
        return result

    # Single value
    try:
        result = {"value": _to_number(s)}
        if unit:
            result["unit"] = unit
        return result
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


def _is_numeric_cell(s: str) -> bool:
    """Check if a string looks like a numeric value (possibly with units or ranges)."""
    s = s.strip()
    if not s or s == "-":
        return False
    # Strip markdown bold
    s = s.strip("*")
    # Normalize en-dash/em-dash to hyphen
    s = s.replace("\u2013", "-").replace("\u2014", "-")
    # Strip parenthetical suffixes
    s = re.sub(r"\s*\([^)]*\)\s*$", "", s).strip()
    # Strip trailing unit
    s = re.sub(r"\s*(Hz|dB|ms|Pa|kHz|%|sec|s)\s*$", "", s, flags=re.IGNORECASE).strip()
    # Strip trailing non-numeric text (e.g., "4 m", "15 vowel classes")
    s = re.sub(r"\s+[a-zA-Z].*$", "", s).strip()
    if not s:
        return False
    # Range like "50-80" or "0.42"
    if re.match(r"^-?\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?$", s):
        return True
    # Approximate: ~0.5
    if re.match(r"^~\d", s):
        return True
    return False


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
    """Extract $$...$$ delimited equation blocks from text.

    Validates extracted equations: rejects those containing markdown artifacts,
    overly long content, or label-only parenthetical text.
    """
    # Match $$ ... $$ blocks (possibly multiline)
    pattern = re.compile(r"\$\$\s*\n(.*?)\n\s*\$\$", re.DOTALL)
    equations = []
    for m in pattern.finditer(text):
        eq = m.group(1).strip()
        if not eq:
            continue
        # Reject equations longer than 500 characters
        if len(eq) > 500:
            continue
        # Reject equations containing markdown indicators
        has_markdown = False
        for line in eq.splitlines():
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("**") or stripped.startswith("- ") or stripped.startswith("|"):
                has_markdown = True
                break
        if has_markdown:
            continue
        # Reject label-only parenthetical like "(Mean frequency)"
        if re.match(r"^\([\w\s]+\)$", eq.strip()):
            continue
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
    """Derive a clean concept name from a parameter Name value.

    Strips IPA characters, parenthetical suffixes, normalizes separators,
    and collapses to ASCII alphanumeric + underscores.
    """
    s = name.strip().lower()
    # Replace / with _
    s = s.replace("/", "_")
    # Strip parenthetical suffixes like _(as), _(swedish)
    s = re.sub(r"_?\([^)]*\)", "", s)
    # Replace spaces with underscores
    s = s.replace(" ", "_")
    # Normalize unicode to NFKD and strip non-ASCII
    s = unicodedata.normalize("NFKD", s)
    cleaned = re.sub(r"[^a-z0-9_]", "", s)
    # Collapse multiple underscores
    cleaned = re.sub(r"_+", "_", cleaned)
    # Strip leading/trailing underscores
    cleaned = cleaned.strip("_")
    # If stripping removed everything (e.g., pure IPA like /æ/), use unicode name
    if not cleaned:
        # Try to get unicode character names for non-ASCII chars
        chars = []
        for ch in name.strip():
            if ch.isascii() and ch.isalnum():
                chars.append(ch)
            elif not ch.isascii():
                try:
                    uname = unicodedata.name(ch, "").lower().replace(" ", "_")
                    if uname:
                        chars.append(uname)
                except ValueError:
                    pass
        cleaned = "_".join(chars) if chars else "unknown"
        cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned


def _extract_unit_from_header(header: str) -> str | None:
    """Extract a unit from a column header like 'D_inh (ms)' or 'F1 (Hz)'."""
    m = _HEADER_UNIT_PATTERN.search(header)
    if m:
        return m.group(1)
    return None


def _find_name_column(headers: list[str]) -> str | None:
    """Find which column header serves as the parameter name column.

    Checks for exact matches first, then heuristic: first column that
    doesn't contain units and isn't purely numeric.
    """
    # Exact match
    for h in headers:
        hl = h.strip().lower()
        if hl in ("name", "parameter"):
            return h
    # Heuristic: first non-numeric, non-unit column (typically column 0)
    for h in headers:
        hl = h.strip().lower()
        if not _UNIT_PATTERN.search(h) and hl not in ("", "-"):
            return h
    return None


def _row_to_claim(
    row: dict[str, str],
    name_col: str,
    headers: list[str],
    paper_name: str,
    claim_counter: int,
) -> dict[str, Any] | None:
    """Convert a parsed table row into a parameter claim dict.

    Handles both standard columns (Name/Parameter, Default, Value, Range, Units)
    and fuzzy columns where units are embedded in headers and values are numeric.

    Returns None if the row would produce a skeleton claim (no value, no bounds, no unit).
    """
    name = row.get(name_col)
    if not name:
        return None

    claim: dict[str, Any] = {
        "id": f"claim{claim_counter}",
        "type": "parameter",
        "concept": _concept_name_from_param(name),
        "provenance": {
            "paper": paper_name,
            "page": 0,
        },
    }

    # --- Standard columns ---

    # Value from Default or Value column
    default_str = row.get("Default") or row.get("Value")
    if default_str is not None:
        try:
            claim["value"] = _to_number(default_str)
        except (ValueError, TypeError):
            pass

    # Range (exact header match)
    range_str = row.get("Range")
    if range_str:
        range_info = parse_range(range_str)
        if "lower_bound" in range_info:
            claim["lower_bound"] = range_info["lower_bound"]
            claim["upper_bound"] = range_info["upper_bound"]
        elif "value" in range_info and "value" not in claim:
            claim["value"] = range_info["value"]
        # Range may carry a unit (e.g., "60-150 Hz")
        if "unit" in range_info and "unit" not in claim:
            claim["unit"] = range_info["unit"]

    # Unit from Units/Unit column
    unit = row.get("Units") or row.get("Unit")
    if unit and unit != "-":
        claim["unit"] = unit

    # --- Fuzzy columns: headers with embedded units ---
    # For columns like "D_inh (ms)", "F1 (Hz)", "Range in Study", etc.
    for h in headers:
        if h == name_col:
            continue
        val_str = row.get(h)
        if not val_str:
            continue

        # Check for "Range in Study" or similar range-like header
        if "range" in h.lower() and "range" not in {k.lower() for k in row if row.get(k)} | {"range"}:
            # Already handled above via exact "Range" key; try fuzzy
            pass
        if "range" in h.lower() and h != "Range":
            range_info = parse_range(val_str)
            if "lower_bound" in range_info and "lower_bound" not in claim:
                claim["lower_bound"] = range_info["lower_bound"]
                claim["upper_bound"] = range_info["upper_bound"]
            if "unit" in range_info and "unit" not in claim:
                claim["unit"] = range_info["unit"]

        # Extract unit from header like "D_inh (ms)"
        header_unit = _extract_unit_from_header(h)
        if header_unit and _is_numeric_cell(val_str):
            # This column has values with known units
            if "unit" not in claim:
                claim["unit"] = header_unit
            if "value" not in claim:
                # Try to parse as a single value or range
                parsed = parse_range(val_str)
                if "value" in parsed:
                    claim["value"] = parsed["value"]
                elif "lower_bound" in parsed and "lower_bound" not in claim:
                    claim["lower_bound"] = parsed["lower_bound"]
                    claim["upper_bound"] = parsed["upper_bound"]

    # --- Quality gate: require at least one of value, bounds, or unit ---
    has_value = "value" in claim
    has_bounds = "lower_bound" in claim and "upper_bound" in claim
    has_unit = "unit" in claim
    if not (has_value or has_bounds or has_unit):
        return None

    return claim


def _is_standard_table(headers: list[str]) -> bool:
    """Check if a table has standard parameter columns (Value, Default, Range, Units).

    Standard tables produce one claim per row. Non-standard (multi-value) tables
    produce one claim per numeric cell.
    """
    standard_cols = {"default", "value", "range", "units", "unit"}
    headers_lower = {h.strip().lower() for h in headers}
    # Also count headers with "range" substring (e.g., "Range in Study")
    has_range_like = any("range" in h.lower() for h in headers)
    has_unit_in_header = any(_HEADER_UNIT_PATTERN.search(h) for h in headers)
    return bool((headers_lower & standard_cols) or has_range_like or has_unit_in_header)


def _row_to_multi_claims(
    row: dict[str, str],
    name_col: str,
    headers: list[str],
    paper_name: str,
    claim_counter: int,
) -> tuple[list[dict[str, Any]], int]:
    """Convert a multi-value table row into multiple parameter claims.

    For tables like `Vowel | F1 | F2 | F3`, generates one claim per numeric cell.
    Concept name is derived from row_name + column_header (e.g., "i_f1").

    Returns (claims_list, updated_claim_counter).
    """
    row_name = row.get(name_col)
    if not row_name:
        return [], claim_counter

    result: list[dict[str, Any]] = []
    for h in headers:
        if h == name_col:
            continue
        val_str = row.get(h)
        if not val_str or not _is_numeric_cell(val_str):
            continue

        parsed = parse_range(val_str)
        if not parsed:
            continue

        claim_counter += 1
        concept = _concept_name_from_param(f"{row_name}_{h}")
        claim: dict[str, Any] = {
            "id": f"claim{claim_counter}",
            "type": "parameter",
            "concept": concept,
            "provenance": {
                "paper": paper_name,
                "page": 0,
            },
        }
        if "value" in parsed:
            claim["value"] = parsed["value"]
        if "lower_bound" in parsed:
            claim["lower_bound"] = parsed["lower_bound"]
            claim["upper_bound"] = parsed["upper_bound"]
        if "unit" in parsed:
            claim["unit"] = parsed["unit"]

        # Quality gate
        has_value = "value" in claim
        has_bounds = "lower_bound" in claim and "upper_bound" in claim
        has_unit = "unit" in claim
        if has_value or has_bounds or has_unit:
            result.append(claim)
        else:
            claim_counter -= 1

    return result, claim_counter


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
    tables = _find_parameter_tables(notes_text)
    for table_text, table_headers in tables:
        rows = parse_parameter_table(table_text)
        name_col = _find_name_column(table_headers)
        if not name_col:
            continue

        if _is_standard_table(table_headers):
            # Standard table: one claim per row
            for row in rows:
                claim_counter += 1
                claim = _row_to_claim(row, name_col, table_headers, paper_name, claim_counter)
                if claim is not None:
                    claims.append(claim)
                else:
                    claim_counter -= 1  # reclaim unused ID
        else:
            # Multi-value table: one claim per numeric cell
            for row in rows:
                new_claims, claim_counter = _row_to_multi_claims(
                    row, name_col, table_headers, paper_name, claim_counter
                )
                claims.extend(new_claims)

    # --- Equation claims ---
    equations = parse_equations(notes_text)
    for eq in equations:
        claim_counter += 1
        claims.append({
            "id": f"claim{claim_counter}",
            "type": "equation",
            "expression": eq,
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


def _find_parameter_tables(text: str) -> list[tuple[str, list[str]]]:
    """Find markdown tables in the text that look like parameter tables.

    Returns a list of (table_text, headers) tuples.

    A parameter table is identified by either:
    1. Headers containing known parameter column names (Name, Parameter, Symbol, etc.)
    2. Fuzzy match: table with >=3 columns where any header contains a unit-like
       string (Hz, dB, ms) or where the first data row has numeric cells.
    """
    lines = text.splitlines()
    tables: list[tuple[str, list[str]]] = []
    i = 0
    param_columns = {"name", "parameter", "symbol", "units", "unit",
                     "default", "value", "range", "notes"}

    while i < len(lines):
        line = lines[i].strip()
        # Check if this looks like a table header row
        if "|" in line and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            # Separator row: |---|---|...|
            if re.match(r"^\|[\s\-:|]+\|$", next_line):
                headers = [h.strip() for h in line.strip("|").split("|")]
                headers_lower = {h.lower() for h in headers}
                is_param_table = False

                # Path 1: exact header match
                if headers_lower & param_columns:
                    is_param_table = True

                # Path 2: fuzzy match — >=3 columns and unit-like headers or numeric data
                if not is_param_table and len(headers) >= 3:
                    # Check if any header contains a unit pattern
                    if any(_UNIT_PATTERN.search(h) for h in headers):
                        is_param_table = True
                    # Check if any header has "range" in it (e.g., "Range in Study")
                    elif any("range" in h.lower() for h in headers):
                        is_param_table = True
                    # Check first data row for numeric content
                    elif i + 2 < len(lines) and lines[i + 2].strip().startswith("|"):
                        first_data = [v.strip() for v in lines[i + 2].strip().strip("|").split("|")]
                        # If at least 2 cells look numeric, it's a data table
                        numeric_count = sum(1 for v in first_data if _is_numeric_cell(v))
                        if numeric_count >= 2:
                            is_param_table = True

                if is_param_table:
                    # Collect the full table
                    table_lines = [lines[i], lines[i + 1]]
                    j = i + 2
                    while j < len(lines) and lines[j].strip().startswith("|"):
                        table_lines.append(lines[j])
                        j += 1
                    tables.append(("\n".join(table_lines), headers))
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

    # Count claim types for summary
    params_with_values = sum(
        1 for c in result["claims"]
        if c["type"] == "parameter" and ("value" in c or ("lower_bound" in c and "upper_bound" in c))
    )
    equations = sum(1 for c in result["claims"] if c["type"] == "equation")
    observations = sum(1 for c in result["claims"] if c["type"] == "observation")
    total = len(result["claims"])

    print(f"Generated {total} claims ({params_with_values} parameters with values, {equations} equations, {observations} observations) -> {output_path}")


if __name__ == "__main__":
    main()
