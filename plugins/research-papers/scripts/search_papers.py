#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["arxiv>=2.1", "semanticscholar>=0.8", "requests>=2.28"]
# ///
"""Multi-source paper search.

Usage:
  uv run search_papers.py "attention is all you need" --source all --max-results 5
  uv run search_papers.py "transformer architecture" --source arxiv --json
"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata

import arxiv
from semanticscholar import SemanticScholar


def normalize_title(title: str) -> str:
    """Normalize a title for deduplication."""
    title = unicodedata.normalize('NFKD', title)
    return ''.join(c.lower() for c in title if c.isalnum())


def search_arxiv(query: str, max_results: int) -> list[dict]:
    """Search arxiv via the arxiv library."""
    results = []
    client = arxiv.Client()
    search = arxiv.Search(query=query, max_results=max_results)
    for r in client.results(search):
        arxiv_id = r.entry_id.split('/abs/')[-1]
        # Strip version suffix for clean ID
        clean_id = arxiv_id.split('v')[0] if 'v' in arxiv_id else arxiv_id
        doi = r.doi or None
        results.append({
            'title': r.title,
            'authors': [a.name for a in r.authors],
            'year': r.published.year if r.published else None,
            'arxiv_id': clean_id,
            'doi': doi,
            'url': r.entry_id,
            'abstract': r.summary,
            'source': 'arxiv',
        })
    return results


def search_s2(query: str, max_results: int) -> list[dict]:
    """Search Semantic Scholar."""
    results = []
    sch = SemanticScholar()
    papers = sch.search_paper(
        query,
        limit=max_results,
        fields=[
            'title', 'authors', 'year', 'externalIds',
            'url', 'abstract',
        ],
    )
    for p in papers[:max_results]:
        ext = p.externalIds or {}
        results.append({
            'title': p.title,
            'authors': [a.name for a in (p.authors or [])],
            'year': p.year,
            'arxiv_id': ext.get('ArXiv'),
            'doi': ext.get('DOI'),
            'url': p.url,
            'abstract': p.abstract,
            'source': 's2',
        })
    return results


def deduplicate(results: list[dict]) -> list[dict]:
    """Deduplicate by DOI first, then by normalized title."""
    seen_dois: set[str] = set()
    seen_titles: set[str] = set()
    deduped = []

    for r in results:
        doi = r.get('doi')
        if doi:
            if doi in seen_dois:
                continue
            seen_dois.add(doi)

        norm = normalize_title(r.get('title', ''))
        if norm in seen_titles:
            continue
        seen_titles.add(norm)

        deduped.append(r)
    return deduped


def format_table(results: list[dict]) -> str:
    """Format results as a human-readable table."""
    lines = []
    for i, r in enumerate(results, 1):
        authors = ', '.join(r['authors'][:3])
        if len(r['authors']) > 3:
            authors += ' et al.'
        lines.append(f"[{i}] {r['title']}")
        lines.append(f"    Authors: {authors}")
        lines.append(f"    Year: {r.get('year', '?')}")
        ids = []
        if r.get('arxiv_id'):
            ids.append(f"arxiv:{r['arxiv_id']}")
        if r.get('doi'):
            ids.append(f"doi:{r['doi']}")
        lines.append(f"    IDs: {', '.join(ids) if ids else 'none'}")
        lines.append(f"    URL: {r.get('url', '?')}")
        if r.get('abstract'):
            abstract = r['abstract'][:200]
            if len(r['abstract']) > 200:
                abstract += '...'
            lines.append(f"    Abstract: {abstract}")
        lines.append('')
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Search for papers')
    parser.add_argument('query', help='Search query')
    parser.add_argument('--source', choices=['arxiv', 's2', 'all'],
                        default='all', help='Search source (default: all)')
    parser.add_argument('--max-results', type=int, default=5,
                        help='Max results per source (default: 5)')
    parser.add_argument('--json', action='store_true',
                        help='Output as JSON')
    args = parser.parse_args()

    results = []
    errors = []

    if args.source in ('arxiv', 'all'):
        try:
            results.extend(search_arxiv(args.query, args.max_results))
        except Exception as e:
            errors.append(f"arxiv: {e}")

    if args.source in ('s2', 'all'):
        try:
            results.extend(search_s2(args.query, args.max_results))
        except Exception as e:
            errors.append(f"s2: {e}")

    results = deduplicate(results)

    if args.json:
        output = {'results': results, 'count': len(results)}
        if errors:
            output['errors'] = errors
        print(json.dumps(output, indent=2))
    else:
        if errors:
            for e in errors:
                print(f"WARNING: {e}", file=sys.stderr)
        if results:
            print(format_table(results))
        else:
            print("No results found.")


if __name__ == '__main__':
    main()
