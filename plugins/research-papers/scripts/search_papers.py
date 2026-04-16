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
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import re
import sys
import unicodedata
from collections.abc import Callable

import arxiv
from semanticscholar import SemanticScholar

SOURCE_ORDER = ('arxiv', 's2')
SearchFn = Callable[[str, int], list[dict]]


def normalize_title(title: str) -> str:
    """Normalize a title for deduplication."""
    title = unicodedata.normalize('NFKD', title)
    return ''.join(c.lower() for c in title if c.isalnum())


def normalize_doi(doi: str | None) -> str | None:
    """Normalize a DOI for deduplication while preserving displayed metadata."""
    if not doi:
        return None
    return doi.strip().lower()


def search_arxiv(query: str, max_results: int) -> list[dict]:
    """Search arxiv via the arxiv library."""
    results = []
    client = arxiv.Client()
    search = arxiv.Search(query=query, max_results=max_results)
    for r in client.results(search):
        arxiv_id = r.entry_id.split('/abs/')[-1]
        # Strip version suffix for clean ID
        clean_id = re.sub(r'v\d+$', '', arxiv_id)
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


SEARCHERS: dict[str, SearchFn] = {
    'arxiv': search_arxiv,
    's2': search_s2,
}


def sources_for(source: str) -> list[str]:
    """Return concrete sources in stable output order."""
    if source == 'all':
        return list(SOURCE_ORDER)
    return [source]


def run_searches(query: str, max_results: int, source: str) -> tuple[list[dict], list[str]]:
    """Run requested searches, overlapping independent network-bound sources."""
    selected_sources = sources_for(source)
    if max_results <= 0:
        return [], []

    per_source: dict[str, list[dict]] = {name: [] for name in selected_sources}
    errors_by_source: dict[str, str] = {}

    if len(selected_sources) == 1:
        name = selected_sources[0]
        try:
            per_source[name] = SEARCHERS[name](query, max_results)
        except Exception as e:
            errors_by_source[name] = str(e)
    else:
        with ThreadPoolExecutor(
            max_workers=len(selected_sources),
            thread_name_prefix='paper-search',
        ) as executor:
            future_to_source = {
                executor.submit(SEARCHERS[name], query, max_results): name
                for name in selected_sources
            }
            for future in as_completed(future_to_source):
                name = future_to_source[future]
                try:
                    per_source[name] = future.result()
                except Exception as e:
                    errors_by_source[name] = str(e)

    results: list[dict] = []
    for name in selected_sources:
        results.extend(per_source[name])
    errors = [
        f"{name}: {errors_by_source[name]}"
        for name in selected_sources
        if name in errors_by_source
    ]
    return deduplicate(results), errors


def deduplicate(results: list[dict]) -> list[dict]:
    """Deduplicate by DOI first, then by normalized title."""
    seen_dois: set[str] = set()
    seen_titles: set[str] = set()
    deduped = []

    for r in results:
        doi = normalize_doi(r.get('doi'))
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

    results, errors = run_searches(args.query, args.max_results, args.source)

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
