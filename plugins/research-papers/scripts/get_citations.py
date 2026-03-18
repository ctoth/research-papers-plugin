#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["semanticscholar>=0.8", "requests>=2.28"]
# ///
"""Citation graph traversal via Semantic Scholar.

Usage:
  uv run get_citations.py 1706.03762 --direction references --max-results 10
  uv run get_citations.py "10.18653/v1/2023.acl-long.1" --direction both --json
  uv run get_citations.py 1706.03762 --direction citations --filter-existing --papers-dir papers/
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from semanticscholar import SemanticScholar

# Add scripts dir to path for _paper_id import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paper_id import classify_identifier, to_s2_id  # noqa: E402

SCRIPTS_DIR = Path(__file__).resolve().parent


def lookup_in_collection(author: str | None, year: str | None,
                         title: str | None, papers_dir: str) -> str | None:
    """Check if a paper is already in the collection via paper_hash.py."""
    if not author:
        return None
    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / 'paper_hash.py'),
        '--papers-dir', papers_dir,
        'lookup',
        '--author', author,
    ]
    if year:
        cmd.extend(['--year', year])
    if title:
        cmd.extend(['--title', title])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def get_first_surname(name: str) -> str | None:
    """Extract surname from 'First Last' format."""
    parts = name.strip().split()
    return parts[-1] if parts else None


def fetch_citations(identifier: str, direction: str,
                    max_results: int) -> tuple[list[dict], dict]:
    """Fetch references and/or citations for a paper.

    Returns (papers_list, source_paper_info).
    """
    id_type, value = classify_identifier(identifier)
    s2_id = to_s2_id(id_type, value)

    sch = SemanticScholar()

    # Get the source paper info
    source = sch.get_paper(s2_id, fields=['title', 'authors', 'year', 'externalIds'])
    source_info = {
        'title': source.title if source else identifier,
        'paperId': source.paperId if source else None,
    }

    results = []

    if direction in ('references', 'both'):
        refs = sch.get_paper_references(
            s2_id,
            fields=[
                'title', 'authors', 'year', 'externalIds',
                'url', 'abstract', 'influentialCitationCount',
                'citationCount',
            ],
            limit=max_results * 2,  # fetch extra for sorting
        )
        for ref in refs:
            p = ref.citedPaper
            if not p or not p.title:
                continue
            ext = p.externalIds or {}
            first_author = None
            if p.authors:
                first_author = get_first_surname(p.authors[0].name)
            results.append({
                'title': p.title,
                'authors': [a.name for a in (p.authors or [])],
                'year': p.year,
                'arxiv_id': ext.get('ArXiv'),
                'doi': ext.get('DOI'),
                'url': p.url,
                'abstract': p.abstract,
                'influential_citation_count': p.influentialCitationCount,
                'citation_count': p.citationCount,
                'first_author_surname': first_author,
                'relation': 'reference',
            })

    if direction in ('citations', 'both'):
        cits = sch.get_paper_citations(
            s2_id,
            fields=[
                'title', 'authors', 'year', 'externalIds',
                'url', 'abstract', 'influentialCitationCount',
                'citationCount',
            ],
            limit=max_results * 2,
        )
        for cit in cits:
            p = cit.citingPaper
            if not p or not p.title:
                continue
            ext = p.externalIds or {}
            first_author = None
            if p.authors:
                first_author = get_first_surname(p.authors[0].name)
            results.append({
                'title': p.title,
                'authors': [a.name for a in (p.authors or [])],
                'year': p.year,
                'arxiv_id': ext.get('ArXiv'),
                'doi': ext.get('DOI'),
                'url': p.url,
                'abstract': p.abstract,
                'influential_citation_count': p.influentialCitationCount,
                'citation_count': p.citationCount,
                'first_author_surname': first_author,
                'relation': 'citation',
            })

    # Sort by influential citation count (highest first)
    results.sort(
        key=lambda x: x.get('influential_citation_count') or 0,
        reverse=True,
    )

    return results[:max_results], source_info


def main():
    parser = argparse.ArgumentParser(
        description='Fetch citation graph via Semantic Scholar')
    parser.add_argument('identifier', help='arxiv ID/URL, DOI, or S2 paper ID')
    parser.add_argument('--direction', choices=['references', 'citations', 'both'],
                        default='references',
                        help='Which direction to traverse (default: references)')
    parser.add_argument('--max-results', type=int, default=50,
                        help='Max results to return (default: 50)')
    parser.add_argument('--papers-dir', default='papers/',
                        help='Papers collection directory (default: papers/)')
    parser.add_argument('--filter-existing', action='store_true',
                        help='Exclude papers already in the collection')
    parser.add_argument('--json', action='store_true',
                        help='Output as JSON')
    args = parser.parse_args()

    results, source_info = fetch_citations(
        args.identifier, args.direction, args.max_results)

    if args.filter_existing:
        filtered = []
        for r in results:
            match = lookup_in_collection(
                r.get('first_author_surname'),
                str(r['year']) if r.get('year') else None,
                r.get('title'),
                args.papers_dir,
            )
            if match:
                r['existing_dir'] = match
            else:
                filtered.append(r)
        results = filtered

    if args.json:
        # Remove internal fields from JSON output
        clean = []
        for r in results:
            out = {k: v for k, v in r.items() if k != 'first_author_surname'}
            clean.append(out)
        print(json.dumps({
            'source': source_info,
            'direction': args.direction,
            'count': len(clean),
            'results': clean,
        }, indent=2))
    else:
        print(f"Source: {source_info.get('title', '?')}")
        print(f"Direction: {args.direction}")
        print(f"Results: {len(results)}")
        print('---')
        for i, r in enumerate(results, 1):
            authors = ', '.join(r['authors'][:3])
            if len(r['authors']) > 3:
                authors += ' et al.'
            year = r.get('year', '?')
            rel = r.get('relation', '?')
            influential = r.get('influential_citation_count', 0)
            print(f"[{i}] ({rel}) {r['title']}")
            print(f"    {authors} ({year})")
            ids = []
            if r.get('arxiv_id'):
                ids.append(f"arxiv:{r['arxiv_id']}")
            if r.get('doi'):
                ids.append(f"doi:{r['doi']}")
            print(f"    IDs: {', '.join(ids) if ids else 'none'}")
            print(f"    Influential citations: {influential}")
            print()


if __name__ == '__main__':
    main()
