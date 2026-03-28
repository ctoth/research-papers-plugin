#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Export BibTeX for the paper collection.

For papers with a stored bibtex field (from Semantic Scholar), emits it as-is.
For papers without, synthesizes an entry from metadata.json fields.

Usage:
  uv run export_bibtex.py --papers-dir papers/
  uv run export_bibtex.py --papers-dir papers/ --output papers/collection.bib
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def _citation_key(metadata: dict, dirname: str) -> str:
    """Generate a citation key from metadata: LastName_YYYY."""
    authors = metadata.get('authors', [])
    if authors:
        surname = authors[0].split()[-1]
    else:
        surname = dirname.split('_')[0]
    year = metadata.get('year', '')
    # Strip non-alphanumeric for key safety
    surname = re.sub(r'[^a-zA-Z]', '', surname)
    return f"{surname}_{year}" if year else surname


def _escape_bibtex(s: str) -> str:
    """Escape special BibTeX characters in a value."""
    return s.replace('&', r'\&').replace('%', r'\%')


def _entry_type(metadata: dict) -> str:
    """Guess BibTeX entry type from venue_type or defaults."""
    vtype = metadata.get('venue_type', '')
    if vtype == 'journal':
        return 'article'
    if vtype == 'conference':
        return 'inproceedings'
    # Default: article (most common in this collection)
    return 'article'


def _synthesize_bibtex(metadata: dict, dirname: str) -> str:
    """Build a BibTeX entry from metadata.json fields."""
    key = _citation_key(metadata, dirname)
    etype = _entry_type(metadata)
    lines = [f"@{etype}{{{key},"]

    title = metadata.get('title', '')
    if title:
        lines.append(f"  title = {{{_escape_bibtex(title)}}},")

    authors = metadata.get('authors', [])
    if authors:
        lines.append(f"  author = {{{_escape_bibtex(' and '.join(authors))}}},")

    year = metadata.get('year')
    if year:
        lines.append(f"  year = {{{year}}},")

    venue = metadata.get('venue')
    if venue:
        field = 'journal' if etype == 'article' else 'booktitle'
        lines.append(f"  {field} = {{{_escape_bibtex(venue)}}},")

    volume = metadata.get('volume')
    if volume:
        lines.append(f"  volume = {{{volume}}},")

    pages = metadata.get('pages')
    if pages:
        lines.append(f"  pages = {{{pages}}},")

    doi = metadata.get('doi')
    if doi:
        lines.append(f"  doi = {{{doi}}},")

    lines.append("}")
    return '\n'.join(lines)


def export_collection(papers_dir: Path) -> str:
    """Generate BibTeX for all papers with metadata.json."""
    entries = []
    for meta_path in sorted(papers_dir.glob('*/metadata.json')):
        dirname = meta_path.parent.name
        with open(meta_path, encoding='utf-8') as f:
            metadata = json.load(f)

        bibtex = metadata.get('bibtex')
        if bibtex:
            entries.append(bibtex.strip())
        else:
            entries.append(_synthesize_bibtex(metadata, dirname))

    return '\n\n'.join(entries) + '\n' if entries else ''


def main():
    parser = argparse.ArgumentParser(description='Export collection BibTeX')
    parser.add_argument('--papers-dir', default='papers/',
                        help='Papers collection directory (default: papers/)')
    parser.add_argument('--output', '-o',
                        help='Output .bib file (default: stdout)')
    args = parser.parse_args()

    bib = export_collection(Path(args.papers_dir))

    if args.output:
        Path(args.output).write_text(bib, encoding='utf-8')
        print(f"Wrote {args.output}", file=sys.stderr)
    else:
        print(bib, end='')


if __name__ == '__main__':
    main()
