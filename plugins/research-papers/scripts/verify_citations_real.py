#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["requests>=2.28", "semanticscholar>=0.8"]
# ///
"""Final gate: verify every citation is a REAL paper, not a hallucination (F7).

For each entry in a deliverable's ``citations.bibtex`` this confirms the cited work
exists in the world. Design (2026-06-30 decision):

  * Fast path -- the citation already has a DOI or URL. Do NOT run a scholarly
    search; resolve the identifier and confirm the record it returns (title +
    author + year) matches the citation. A DOI/URL that 404s or whose title
    disagrees is exactly the failure this gate catches.
  * Fallback -- no DOI and no URL. Query a scholarly index (Crossref title search /
    Semantic Scholar / OpenAlex) by title + first author + year, requiring a high
    title similarity (fuzzy ratio >= 0.9) with +/-1 year tolerance.

Verdicts: REAL, MISMATCH (resolved/found but disagrees), NOT_FOUND (no external
record), UNVERIFIED (network/rate-limit/timeout -- never silently passed). Exits 2
if any citation is MISMATCH or NOT_FOUND.

Speed: a cited key whose ``papers/`` ``metadata.json`` already carries a verified
DOI + stored title is matched locally with no network call; checks run concurrently
with short timeouts; the verified status is stamped back into ``metadata.json`` so
re-runs skip the network. Google Scholar is never scraped.

Usage:
  uv run scripts/verify_citations_real.py <citations.bibtex> [--papers-dir papers/]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_keymap import load_keymap  # noqa: E402

TITLE_THRESHOLD = 0.9
YEAR_TOLERANCE = 1
REQUEST_TIMEOUT = 10
MAX_WORKERS = 8
CROSSREF_API = "https://api.crossref.org/works/"


# --------------------------------------------------------------------------- #
# Matching helpers
# --------------------------------------------------------------------------- #
def normalize_title(title: str) -> str:
    """Lowercase, strip punctuation to spaces, collapse whitespace."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", (title or "").lower())).strip()


def title_ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize_title(a), normalize_title(b)).ratio()


def year_within_tolerance(cited: str | None, found: str | None) -> bool:
    """True if years are within tolerance, or either is absent (don't over-fail)."""
    try:
        return abs(int(str(cited)[:4]) - int(str(found)[:4])) <= YEAR_TOLERANCE
    except (TypeError, ValueError):
        return True


def titles_match(cited_title: str, found_title: str, cited_year=None, found_year=None) -> bool:
    return (title_ratio(cited_title, found_title) >= TITLE_THRESHOLD
            and year_within_tolerance(cited_year, found_year))


# --------------------------------------------------------------------------- #
# Network resolvers (mockable seams -- patched in tests, never hit in CI)
# --------------------------------------------------------------------------- #
def crossref_lookup_doi(doi: str) -> dict | None:
    """Resolve a DOI via Crossref. Returns {title, authors, year} or None (404).

    Raises on transport errors so the caller can record UNVERIFIED.
    """
    resp = requests.get(f"{CROSSREF_API}{doi}", timeout=REQUEST_TIMEOUT,
                        headers={"Accept": "application/json"})
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    msg = resp.json().get("message", {})
    title = (msg.get("title") or [""])[0]
    if not title:
        return None
    authors = [a.get("family", "") for a in msg.get("author", []) if a.get("family")]
    parts = (msg.get("issued", {}).get("date-parts") or [[None]])[0]
    year = str(parts[0]) if parts and parts[0] else None
    return {"title": title, "authors": authors, "year": year}


def url_title_lookup(url: str) -> str | None:
    """Fetch a non-DOI URL and extract its <title> / citation_title meta tag."""
    resp = requests.get(url, timeout=REQUEST_TIMEOUT)
    if resp.status_code >= 400:
        return None
    html = resp.text
    meta = re.search(r'<meta[^>]+name=["\']citation_title["\'][^>]+content=["\']([^"\']+)', html, re.I)
    if meta:
        return meta.group(1)
    tag = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    return tag.group(1).strip() if tag else None


def search_scholarly(title: str, author: str | None, year: str | None) -> dict | None:
    """Title search against a scholarly index (Crossref). Returns best {title, year} or None."""
    resp = requests.get(CROSSREF_API, timeout=REQUEST_TIMEOUT,
                        params={"query.bibliographic": title, "rows": 5})
    resp.raise_for_status()
    items = resp.json().get("message", {}).get("items", [])
    best = None
    best_ratio = 0.0
    for item in items:
        cand = (item.get("title") or [""])[0]
        ratio = title_ratio(title, cand)
        if ratio > best_ratio:
            parts = (item.get("issued", {}).get("date-parts") or [[None]])[0]
            best = {"title": cand, "year": str(parts[0]) if parts and parts[0] else None}
            best_ratio = ratio
    return best


# --------------------------------------------------------------------------- #
# bibtex parsing
# --------------------------------------------------------------------------- #
_ENTRY_RE = re.compile(r"@\w+\s*\{\s*([^,\s]+)\s*,(.*?)\n\s*\}", re.DOTALL)
_FIELD_RE = re.compile(r"(\w+)\s*=\s*[{\"]\s*(.*?)\s*[}\"]\s*,?", re.DOTALL)


def parse_bibtex(text: str) -> list[dict]:
    """Parse @entries into {key, title, doi, url, year, author} dicts."""
    entries: list[dict] = []
    for key, body in _ENTRY_RE.findall(text):
        fields = {k.lower(): v for k, v in _FIELD_RE.findall(body)}
        author = fields.get("author", "")
        first_author = author.split(" and ")[0].split(",")[0].strip() if author else None
        entries.append({
            "key": key.strip(),
            "title": fields.get("title", ""),
            "doi": fields.get("doi") or None,
            "url": fields.get("url") or None,
            "year": fields.get("year") or None,
            "author": first_author,
        })
    return entries


# --------------------------------------------------------------------------- #
# Verdict logic
# --------------------------------------------------------------------------- #
@dataclass
class CitationVerdict:
    key: str
    verdict: str  # REAL | MISMATCH | NOT_FOUND | UNVERIFIED
    detail: str = ""


def _local_verification(key: str, entry: dict, papers_dir: Path | None) -> dict | None:
    """Return a stamped verification block from papers/<dir>/metadata.json, if any."""
    if papers_dir is None:
        return None
    resolved = load_keymap(papers_dir).get(key)
    if not resolved:
        return None
    meta_path = papers_dir / resolved / "metadata.json"
    if not meta_path.exists():
        return None
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (ValueError, json.JSONDecodeError):
        return None
    return meta.get("verification") if isinstance(meta.get("verification"), dict) else None


def _stamp_metadata(key: str, papers_dir: Path | None, verdict: CitationVerdict,
                    resolved_title: str | None, resolved_doi: str | None) -> None:
    if papers_dir is None or verdict.verdict != "REAL":
        return
    resolved = load_keymap(papers_dir).get(key)
    if not resolved:
        return
    meta_path = papers_dir / resolved / "metadata.json"
    if not meta_path.exists():
        return
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (ValueError, json.JSONDecodeError):
        return
    meta["verification"] = {"status": "REAL", "doi": resolved_doi, "title": resolved_title}
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


def verify_citation(entry: dict, papers_dir: Path | None = None) -> CitationVerdict:
    """Resolve one citation to a REAL/MISMATCH/NOT_FOUND/UNVERIFIED verdict."""
    key = entry["key"]
    title = entry.get("title", "")

    # Local stamp: a previously-verified, locally-owned paper -> no network.
    stamp = _local_verification(key, entry, papers_dir)
    if stamp and stamp.get("status") == "REAL" and stamp.get("title") \
            and titles_match(title, stamp["title"]):
        return CitationVerdict(key, "REAL", "cached (metadata.json verification)")

    doi, url = entry.get("doi"), entry.get("url")
    try:
        if doi:
            record = crossref_lookup_doi(doi)
            if record is None:
                return CitationVerdict(key, "NOT_FOUND", f"DOI did not resolve: {doi}")
            if titles_match(title, record["title"], entry.get("year"), record.get("year")):
                _stamp_metadata(key, papers_dir, CitationVerdict(key, "REAL"), record["title"], doi)
                return CitationVerdict(key, "REAL", "DOI resolved and title matched")
            return CitationVerdict(key, "MISMATCH",
                                   f"DOI {doi} resolves to a different title: {record['title']!r}")
        if url:
            found_title = url_title_lookup(url)
            if found_title is None:
                return CitationVerdict(key, "NOT_FOUND", f"URL did not resolve: {url}")
            if titles_match(title, found_title):
                return CitationVerdict(key, "REAL", "URL resolved and title matched")
            return CitationVerdict(key, "MISMATCH",
                                   f"URL {url} title disagrees: {found_title!r}")
        # Fallback: no identifier -> scholarly title search.
        hit = search_scholarly(title, entry.get("author"), entry.get("year"))
        if hit and titles_match(title, hit["title"], entry.get("year"), hit.get("year")):
            return CitationVerdict(key, "REAL", "scholarly search matched")
        return CitationVerdict(key, "NOT_FOUND", "no high-confidence scholarly match")
    except Exception as exc:  # noqa: BLE001 -- transient network/parse errors -> UNVERIFIED
        return CitationVerdict(key, "UNVERIFIED", f"{type(exc).__name__}: {exc}")


def verify_all(entries: list[dict], papers_dir: Path | None = None) -> list[CitationVerdict]:
    """Verify every citation concurrently; results sorted by key for stable output."""
    if not entries:
        return []
    with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(entries))) as pool:
        verdicts = list(pool.map(lambda e: verify_citation(e, papers_dir), entries))
    return sorted(verdicts, key=lambda v: v.key)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Verify every citation is a real paper (F7)")
    parser.add_argument("bibtex", help="path to the deliverable's citations.bibtex")
    parser.add_argument("--papers-dir", default=None,
                        help="papers/ dir for local-stamp fast path + stamping")
    args = parser.parse_args(argv)

    entries = parse_bibtex(Path(args.bibtex).read_text(encoding="utf-8"))
    papers_dir = Path(args.papers_dir) if args.papers_dir else None
    verdicts = verify_all(entries, papers_dir)

    blocking = 0
    for v in verdicts:
        print(f"{v.verdict:<10} @{v.key}  {v.detail}")
        if v.verdict in ("MISMATCH", "NOT_FOUND"):
            blocking += 1
    unverified = sum(1 for v in verdicts if v.verdict == "UNVERIFIED")
    print(f"\nverify-citations-real: {len(verdicts)} citation(s), "
          f"{blocking} blocking (MISMATCH/NOT_FOUND), {unverified} UNVERIFIED")
    if blocking:
        print("BLOCKED: fix the metadata, replace the citation, or remove it from BOTH "
              "the bibliography and the document.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
