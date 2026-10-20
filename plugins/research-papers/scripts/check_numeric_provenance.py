#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Mechanical numeric-provenance gate for paper artifacts.

Fabricated statistics are the highest-cost failure mode in this pipeline: a
wrong hazard ratio or p-value silently inverts a paper's conclusion and then
propagates into claims, lit reviews, and the collection index. Model-facing
instructions alone cannot gate that. This module is the deterministic backstop.

It never reads the PDF and never judges whether a number is *correct* -- it
enforces the structural preconditions that make a number auditable, and it
catches the specific failure of numbers appearing for the first time in a
summary artifact.

Codes:
  NUMERIC_NO_PAGE            a data-bearing number in notes with no page citation
  PARAM_TABLE_NO_PAGE_COL    a quantitative table missing the mandated Page column
  PARAM_ROW_NO_PAGE          a quantitative row with an empty Page cell
  PAGE_OUT_OF_RANGE          *(p.N)* where N exceeds the source's page count
  TEMPLATE_PLACEHOLDER       an unfilled paper-reader template token
  NUMERIC_NOT_IN_NOTES       a number in description.md / abstract.md interpretation
                             that appears nowhere in notes.md

A number that cannot be traced to a page cannot be checked against the page
image, and an untraceable number is indistinguishable from an invented one.
A number that appears only in a summary was never transcribed from the paper.

Usage:
  uv run scripts/check_numeric_provenance.py check papers/Author_Year_Title
  uv run scripts/check_numeric_provenance.py check --all [--papers-dir papers/]
  uv run scripts/check_numeric_provenance.py check <dir> --json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

CODES = (
    "NUMERIC_NO_PAGE",
    "PARAM_TABLE_NO_PAGE_COL",
    "PARAM_ROW_NO_PAGE",
    "PAGE_OUT_OF_RANGE",
    "TEMPLATE_PLACEHOLDER",
    "NUMERIC_NOT_IN_NOTES",
)

# House page-citation forms, including the multi-page and mixed variants that
# appear throughout the collection:
#   (p.7)  (pp.1-3)  (p.1, p.3)  (pp.2-3, p.5)  (pp.991, 993, 996-997)
_PAGE_ATOM = r"[0-9]+(?:\s*[-–]\s*[0-9]+)?"
PAGE_CITE_RE = re.compile(
    rf"\(\s*pp?\.\s*{_PAGE_ATOM}(?:\s*,\s*(?:pp?\.\s*)?{_PAGE_ATOM})*\s*\)"
)

# Sentinel a reader must write when the paper does not report a value.
NOT_REPORTED_RE = re.compile(r"\bnot reported\b|\bnot stated\b|\bn/a\b", re.IGNORECASE)

# Unfilled template tokens from the paper-reader notes scaffold.
PLACEHOLDER_RE = re.compile(
    r"\*\(p\.N\)\*|\(p\.N\)|\(p\.X\)|\[Year\]|\[Full Paper Title\]|\[All authors\]"
)

# Sections whose numbers are bibliographic (years, volumes, reference page
# spans) or navigational rather than empirical findings.
EXEMPT_SECTIONS = {
    "collection cross-references",
    "related work worth reading",
    "reference list",
    "references",
    "bibliography",
    "key citations for follow-up",
    "citations",
    "open questions",
    "notable references cited",
    "sections covered",
}

# The verbatim abstract is a transcription, checked against page-000 by the
# reader rather than by per-line page citations.
VERBATIM_SECTION = "original text (verbatim)"

PAGE_HEADER = "page"

# Header cells that mark a table as carrying reported quantities. Only these
# tables are required to carry per-row page provenance; checklist and glossary
# tables legitimately contain structural digits.
QUANT_HEADERS = {
    "value", "values", "default", "range", "units", "unit", "symbol",
    "measure", "ci", "p", "outcome", "estimate", "effect", "result",
    "results", "score", "mean", "sd", "median", "n", "quantity",
}

_URLISH_RE = re.compile(
    r"https?://\S+|doi:\S+|\b10\.\d{4,}/\S+|arxiv[:/]\S+|\bISBN\b\S*", re.IGNORECASE
)
_LATEX_CMD_RE = re.compile(r"\\[A-Za-z]+")
_MD_LINK_TARGET_RE = re.compile(r"\]\([^)]*\)")

_YEAR_RE = re.compile(r"^(1[5-9]\d{2}|20\d{2}|21\d{2})$")
_NUMBER_RE = re.compile(r"\d+(?:,\d{3})*(?:\.\d+)?(?:[eE][-+]?\d+)?")

# Contexts that make an otherwise structural-looking number a real datum.
_FORCED_SIGNIFICANT_RE = re.compile(
    r"\bN\s*=|\bn\s*=|\bp\s*[<>=]|\bHR\b|\bOR\b|\bRR\b|\bCI\b|%|\bmg\b|\bms\b|\bHz\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Finding:
    code: str
    paper: str
    file: str
    line: int
    detail: str

    def render(self) -> str:
        return f"{self.code}\t{self.paper}\t{self.file}:{self.line}\t{self.detail}"


def strip_frontmatter(text: str) -> tuple[str, int]:
    """Return (body, line_offset) with YAML frontmatter removed."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return text, 0
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return "\n".join(lines[idx + 1 :]), idx + 1
    return text, 0


def scrub_line(line: str) -> str:
    """Remove spans whose digits are never empirical findings."""
    out = PAGE_CITE_RE.sub(" ", line)
    out = _URLISH_RE.sub(" ", out)
    out = _MD_LINK_TARGET_RE.sub(" ", out)
    out = _LATEX_CMD_RE.sub(" ", out)
    return out


def has_page_cite(line: str) -> bool:
    return bool(PAGE_CITE_RE.search(line))


def cited_pages(line: str) -> list[int]:
    pages: list[int] = []
    for match in PAGE_CITE_RE.finditer(line):
        pages.extend(int(tok) for tok in re.findall(r"\d+", match.group(0)))
    return pages


def normalize_number(token: str) -> str:
    return token.replace(",", "")


def significant_numbers(line: str) -> list[str]:
    """Numbers on this line that look like reported data, not structure."""
    scrubbed = scrub_line(line)
    if not scrubbed.strip():
        return []
    forced = bool(_FORCED_SIGNIFICANT_RE.search(scrubbed))
    found: list[str] = []
    for token in _NUMBER_RE.findall(scrubbed):
        plain = normalize_number(token)
        if not forced and _YEAR_RE.match(plain):
            continue
        if not forced and "." not in plain and len(plain) <= 1:
            # Bare single digits are overwhelmingly list markers, chapter
            # numbers, and heading ordinals rather than reported quantities.
            continue
        found.append(plain)
    return found


def _is_table_row(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|") and stripped.count("|") >= 3


def _split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_separator_row(cells: list[str]) -> bool:
    meaningful = [cell for cell in cells if cell]
    if not meaningful:
        return False
    return all(re.fullmatch(r":?-{2,}:?", cell) for cell in meaningful)


def _is_quantitative_table(header_cells: list[str]) -> bool:
    lowered = {cell.lower() for cell in header_cells}
    return bool(lowered & QUANT_HEADERS) or PAGE_HEADER in lowered


def page_count(paper_dir: Path) -> int | None:
    """Actual page count from rendered page images, if available."""
    pngs = paper_dir / "pngs"
    if not pngs.is_dir():
        return None
    pages = list(pngs.glob("page-*.png"))
    return len(pages) or None


def collect_numbers(text: str) -> set[str]:
    """Every number anywhere in a document, for cross-artifact comparison."""
    body, _ = strip_frontmatter(text)
    numbers: set[str] = set()
    for line in body.splitlines():
        numbers.update(normalize_number(tok) for tok in _NUMBER_RE.findall(line))
    return numbers


def check_notes_file(paper: str, path: Path, max_page: int | None = None) -> list[Finding]:
    """Page-provenance checks for notes.md and per-chapter/chunk files."""
    if not path.is_file():
        return []
    raw = path.read_text(encoding="utf-8", errors="replace")
    body, offset = strip_frontmatter(raw)
    findings: list[Finding] = []
    fname = path.name

    section = ""
    in_fence = False
    in_math = False
    math_start_line = 0
    math_has_number = False
    table_page_col: int | None = None
    table_is_quant = False
    in_table = False

    lines = body.splitlines()
    for idx, line in enumerate(lines):
        lineno = idx + 1 + offset
        stripped = line.strip()

        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        if stripped == "$$":
            if in_math:
                if math_has_number:
                    window = lines[idx + 1 : idx + 7]
                    if not any(has_page_cite(w) for w in window):
                        findings.append(
                            Finding(
                                "NUMERIC_NO_PAGE",
                                paper,
                                fname,
                                math_start_line,
                                "equation block with numeric constants has no page citation within 6 lines",
                            )
                        )
                in_math = False
                math_has_number = False
            else:
                in_math = True
                math_start_line = lineno
                math_has_number = False
            continue
        if in_math:
            if significant_numbers(line):
                math_has_number = True
            continue

        if stripped.startswith("#"):
            section = stripped.lstrip("#").strip().lower()
            in_table = False
            table_page_col = None
            table_is_quant = False
            continue

        for token in PLACEHOLDER_RE.findall(line):
            findings.append(
                Finding(
                    "TEMPLATE_PLACEHOLDER",
                    paper,
                    fname,
                    lineno,
                    f"unfilled template token {token.strip()!r}",
                )
            )

        if max_page is not None:
            for page in cited_pages(line):
                if page < 1 or page > max_page:
                    findings.append(
                        Finding(
                            "PAGE_OUT_OF_RANGE",
                            paper,
                            fname,
                            lineno,
                            f"cites p.{page} but the source has {max_page} page(s)",
                        )
                    )

        if section in EXEMPT_SECTIONS:
            continue

        if _is_table_row(line):
            cells = _split_row(line)
            if not in_table:
                in_table = True
                table_is_quant = _is_quantitative_table(cells)
                lowered = [cell.lower() for cell in cells]
                table_page_col = lowered.index(PAGE_HEADER) if PAGE_HEADER in lowered else None
                if table_is_quant and table_page_col is None:
                    findings.append(
                        Finding(
                            "PARAM_TABLE_NO_PAGE_COL",
                            paper,
                            fname,
                            lineno,
                            "quantitative table has no Page column",
                        )
                    )
                continue
            if _is_separator_row(cells) or not table_is_quant:
                continue
            if table_page_col is None:
                continue
            cell = cells[table_page_col] if table_page_col < len(cells) else ""
            row_has_data = any(
                significant_numbers(c) for i, c in enumerate(cells) if i != table_page_col
            )
            if row_has_data and not re.search(r"\d", cell):
                findings.append(
                    Finding(
                        "PARAM_ROW_NO_PAGE",
                        paper,
                        fname,
                        lineno,
                        f"quantitative row {cells[0]!r} has an empty Page cell",
                    )
                )
            continue
        in_table = False
        table_page_col = None
        table_is_quant = False

        numbers = significant_numbers(line)
        if not numbers:
            continue
        if has_page_cite(line):
            continue
        if NOT_REPORTED_RE.search(line):
            continue
        findings.append(
            Finding(
                "NUMERIC_NO_PAGE",
                paper,
                fname,
                lineno,
                f"numbers {', '.join(numbers[:4])} with no page citation",
            )
        )

    return findings


def check_summary_file(
    paper: str, path: Path, notes_numbers: set[str]
) -> list[Finding]:
    """Cross-check derived summaries against notes.md.

    A number that appears in description.md or in the abstract's interpretation
    but nowhere in notes.md was never transcribed from a page image. That is the
    exact shape of a summary-layer fabrication.
    """
    if not path.is_file():
        return []
    raw = path.read_text(encoding="utf-8", errors="replace")
    body, offset = strip_frontmatter(raw)
    findings: list[Finding] = []
    fname = path.name
    section = ""
    in_fence = False

    for idx, line in enumerate(body.splitlines()):
        lineno = idx + 1 + offset
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if stripped.startswith("#"):
            section = stripped.lstrip("#").strip().lower()
            continue
        if section == VERBATIM_SECTION:
            continue
        for token in PLACEHOLDER_RE.findall(line):
            findings.append(
                Finding(
                    "TEMPLATE_PLACEHOLDER",
                    paper,
                    fname,
                    lineno,
                    f"unfilled template token {token.strip()!r}",
                )
            )
        unsourced = [n for n in significant_numbers(line) if n not in notes_numbers]
        if unsourced:
            findings.append(
                Finding(
                    "NUMERIC_NOT_IN_NOTES",
                    paper,
                    fname,
                    lineno,
                    f"numbers {', '.join(unsourced[:4])} appear nowhere in notes.md",
                )
            )
    return findings


SUMMARY_FILES = ("description.md", "abstract.md")


def check_paper(paper_dir: Path) -> list[Finding]:
    paper = paper_dir.name
    max_page = page_count(paper_dir)
    findings: list[Finding] = []

    notes_path = paper_dir / "notes.md"
    findings.extend(check_notes_file(paper, notes_path, max_page))

    for sub in ("chapters", "chunks"):
        subdir = paper_dir / sub
        if subdir.is_dir():
            for path in sorted(subdir.glob("*.md")):
                findings.extend(check_notes_file(paper, path, max_page))

    notes_numbers: set[str] = set()
    if notes_path.is_file():
        notes_numbers = collect_numbers(
            notes_path.read_text(encoding="utf-8", errors="replace")
        )
    for sub in ("chapters", "chunks"):
        subdir = paper_dir / sub
        if subdir.is_dir():
            for path in sorted(subdir.glob("*.md")):
                notes_numbers |= collect_numbers(
                    path.read_text(encoding="utf-8", errors="replace")
                )

    for name in SUMMARY_FILES:
        findings.extend(check_summary_file(paper, paper_dir / name, notes_numbers))

    return findings


def iter_paper_dirs(papers_dir: Path):
    for entry in sorted(papers_dir.iterdir()):
        if entry.is_dir() and (entry / "notes.md").is_file():
            yield entry


def render_report(findings: list[Finding], papers_checked: int) -> str:
    lines = [f"Numeric provenance: {papers_checked} paper(s) checked"]
    if not findings:
        lines.append("  OK - every reported number carries page provenance")
        return "\n".join(lines)
    by_code: dict[str, list[Finding]] = {}
    for finding in findings:
        by_code.setdefault(finding.code, []).append(finding)
    for code in CODES:
        group = by_code.get(code)
        if not group:
            continue
        lines.append("")
        lines.append(f"  {code} ({len(group)}):")
        for finding in group:
            lines.append(
                f"    {finding.paper}/{finding.file}:{finding.line} - {finding.detail}"
            )
    lines.append("")
    lines.append(f"Summary: {len(findings)} finding(s) across {papers_checked} paper(s)")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Mechanical numeric-provenance gate for paper artifacts"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="check one paper directory or the whole collection")
    check.add_argument("paper_dir", nargs="?", help="papers/Author_Year_Title")
    check.add_argument("--all", action="store_true", help="check every paper in --papers-dir")
    check.add_argument("--papers-dir", default="papers/")
    check.add_argument("--json", action="store_true", help="emit findings as JSON")
    args = parser.parse_args(argv)

    if args.all:
        papers_dir = Path(args.papers_dir)
        if not papers_dir.is_dir():
            print(f"No such papers dir: {papers_dir}", file=sys.stderr)
            return 2
        dirs = list(iter_paper_dirs(papers_dir))
    elif args.paper_dir:
        target = Path(args.paper_dir)
        if not target.is_dir():
            print(f"No such paper dir: {target}", file=sys.stderr)
            return 2
        dirs = [target]
    else:
        parser.error("pass a paper directory or --all")
        return 2

    findings: list[Finding] = []
    for paper_dir in dirs:
        findings.extend(check_paper(paper_dir))

    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        print(render_report(findings, len(dirs)))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
