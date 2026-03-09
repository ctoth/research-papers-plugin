#!/usr/bin/env python3
"""
Canonical paper identity resolution.

Two modes:
  1. lookup:   given a citation string, find matching directory in papers/
  2. generate: given author/year/title, produce the canonical dirname

Usage:
  python paper_hash.py lookup "Fan et al. (2018) - Hierarchical neural story generation"
  python paper_hash.py lookup --author Fan --year 2018
  python paper_hash.py generate --author Fan --year 2018 --title "Hierarchical Neural Story Generation"
  python paper_hash.py parse "Fan et al. (2018) - Hierarchical neural story generation"
  python paper_hash.py extract-leads [--papers-dir papers/]

All commands accept --papers-dir to specify the collection root (default: papers/).
"""

import argparse
import os
import re
import sys


# Words to drop from titles when generating short dirname
FILLER_WORDS = {
    'a', 'an', 'the', 'of', 'in', 'on', 'for', 'and', 'or', 'to', 'with',
    'from', 'by', 'as', 'at', 'is', 'are', 'was', 'were', 'be', 'been',
    'its', 'their', 'our', 'your', 'that', 'this', 'these', 'those',
    'using', 'via', 'through', 'toward', 'towards', 'into', 'between',
    'based', 'how', 'what', 'when', 'where', 'why', 'which', 'who',
}

# Max title words in dirname (after filtering)
MAX_TITLE_WORDS = 4


def parse_citation(text):
    """Parse a freeform citation string into (author, year, title).

    Handles formats like:
      Fan et al. (2018) - "Hierarchical neural story generation"
      **Fan et al., 2018** - "Hierarchical neural story generation"
      Genette, G. (1972). *Narrative discourse: an essay in method.*
      Fan et al. (2018) - source of Writing Prompts dataset
      Roemmele and Gordon (2015) - "Creative help"
    """
    text = text.strip()
    # Strip leading markdown bold/italic
    text = re.sub(r'^\*+\s*', '', text)
    text = re.sub(r'\s*\*+$', '', text)
    text = text.strip()

    author = None
    year = None
    title = None

    # Extract year - look for (YYYY) or just YYYY near the start
    year_match = re.search(r'\((\d{4})\)', text)
    if not year_match:
        year_match = re.search(r'[\s,](\d{4})[\s,\b\)]', text)
    if not year_match:
        year_match = re.search(r'(\d{4})', text)
    if year_match:
        year = year_match.group(1)

    # Extract author - everything before the year (or first punctuation pattern)
    if year_match:
        before_year = text[:year_match.start()].strip()
    else:
        before_year = text.split('-')[0].split('—')[0].strip()

    # Clean up author string
    before_year = re.sub(r'[,\s]+$', '', before_year)
    before_year = re.sub(r'\s+et\s+al\.?$', '', before_year)
    # Get surname (first capitalized word)
    author_match = re.match(r'([A-Z][a-z]+)', before_year)
    if author_match:
        author = author_match.group(1)

    # Extract title - look for quoted or italicized text after author+year
    if year_match:
        after_year = text[year_match.end():]
    else:
        after_year = text

    # Try quoted title: "Title here"
    title_match = re.search(r'"([^"]+)"', after_year)
    if not title_match:
        # Try italicized: *Title here*
        title_match = re.search(r'\*([^*]+)\*', after_year)
    if not title_match:
        # Try after dash/colon separator
        sep_match = re.search(r'[\-—:]\s*(.+?)(?:\s*[\-—]|$)', after_year)
        if sep_match:
            candidate = sep_match.group(1).strip()
            # Only use if it looks like a title (starts with cap, reasonable length)
            if candidate and candidate[0].isupper() and len(candidate) > 5:
                title = candidate
    if title_match and not title:
        title = title_match.group(1).strip()

    # Strip trailing periods from title
    if title:
        title = title.rstrip('.')

    return author, year, title


def generate_dirname(author, year, title):
    """Generate canonical directory name: Author_Year_ShortTitle.

    ShortTitle is 2-4 CamelCase words from the title, dropping filler words.
    Keeps acronyms (all-caps words) as-is.
    """
    if not author or not year:
        return None

    if not title:
        return f"{author}_{year}"

    # Split title, drop filler, take first MAX_TITLE_WORDS meaningful words
    words = re.split(r'[\s/]+', title)
    meaningful = []
    for w in words:
        # Strip punctuation from edges
        clean = re.sub(r'^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$', '', w)
        if not clean:
            continue
        if clean.lower() in FILLER_WORDS:
            continue
        # Capitalize unless it's an acronym (already all-caps)
        if clean.isupper() and len(clean) > 1:
            meaningful.append(clean)
        else:
            meaningful.append(clean[0].upper() + clean[1:])
        if len(meaningful) >= MAX_TITLE_WORDS:
            break

    short_title = ''.join(meaningful) if meaningful else 'Untitled'
    return f"{author}_{year}_{short_title}"


def list_papers(papers_dir):
    """List all paper directories."""
    if not os.path.isdir(papers_dir):
        return []
    return [d for d in os.listdir(papers_dir)
            if os.path.isdir(os.path.join(papers_dir, d))]


def lookup(author, year, title, papers_dir):
    """Find a matching paper directory. Returns dirname or None."""
    dirs = list_papers(papers_dir)
    if not author:
        return None

    author_lower = author.lower()
    candidates = []

    for d in dirs:
        dl = d.lower()
        # Must match author surname at start
        if not dl.startswith(author_lower + '_'):
            # Also try without underscore for compound names
            if not dl.startswith(author_lower):
                continue

        # Must match year if provided
        if year and year not in d:
            continue

        candidates.append(d)

    if not candidates:
        return None

    if len(candidates) == 1:
        return candidates[0]

    # Multiple candidates - try title matching to disambiguate
    if title:
        title_words = set(w.lower() for w in re.split(r'\W+', title) if len(w) > 2)
        best = None
        best_score = 0
        for c in candidates:
            dir_words = set(w.lower() for w in re.split(r'[_\-]', c) if len(w) > 2)
            score = len(title_words & dir_words)
            if score > best_score:
                best_score = score
                best = c
        if best:
            return best

    # Return first match if we can't disambiguate
    return candidates[0]


def extract_leads(papers_dir):
    """Extract all New Leads, skipping ones already in collection."""
    dirs = list_papers(papers_dir)
    leads = []
    seen_keys = set()
    skipped = 0

    for d in sorted(dirs):
        notes_path = os.path.join(papers_dir, d, 'notes.md')
        if not os.path.isfile(notes_path):
            continue

        with open(notes_path, encoding='utf-8') as f:
            text = f.read()

        m = re.search(
            r'### New Leads \(Not Yet in Collection\)\n(.*?)(?:\n###|\n## |\Z)',
            text, re.DOTALL
        )
        if not m:
            continue

        for line in m.group(1).strip().split('\n'):
            line = line.strip()
            if not line.startswith('- '):
                continue

            entry = line[2:].strip()
            author, year, title = parse_citation(entry)

            # Dedup key
            key = f"{(author or '').lower()}_{year or ''}"
            if key in seen_keys:
                continue
            seen_keys.add(key)

            # Check if already in collection
            if author and year:
                match = lookup(author, year, title, papers_dir)
                if match:
                    skipped += 1
                    continue

            leads.append({
                'source': d,
                'text': entry,
                'author': author,
                'year': year,
                'title': title,
            })

    return leads, skipped


def main():
    parser = argparse.ArgumentParser(description='Paper identity resolution')
    parser.add_argument('--papers-dir', default='papers/',
                        help='Path to papers collection (default: papers/)')
    sub = parser.add_subparsers(dest='command')

    # parse: extract author/year/title from citation string
    p_parse = sub.add_parser('parse', help='Parse a citation string')
    p_parse.add_argument('citation', help='Citation text')

    # generate: produce dirname from components
    p_gen = sub.add_parser('generate', help='Generate canonical dirname')
    p_gen.add_argument('--author', required=True)
    p_gen.add_argument('--year', required=True)
    p_gen.add_argument('--title', default='')

    # lookup: find matching directory
    p_look = sub.add_parser('lookup', help='Find matching paper directory')
    p_look.add_argument('citation', nargs='?', help='Citation text')
    p_look.add_argument('--author')
    p_look.add_argument('--year')
    p_look.add_argument('--title', default='')

    # extract-leads: list unfulfilled leads
    p_leads = sub.add_parser('extract-leads',
                             help='Extract unfulfilled New Leads from collection')
    p_leads.add_argument('--json', action='store_true',
                         help='Output as JSON')

    args = parser.parse_args()

    if args.command == 'parse':
        author, year, title = parse_citation(args.citation)
        print(f"author: {author}")
        print(f"year:   {year}")
        print(f"title:  {title}")
        dirname = generate_dirname(author, year, title)
        print(f"dirname: {dirname}")

    elif args.command == 'generate':
        dirname = generate_dirname(args.author, args.year, args.title)
        print(dirname or 'ERROR: need at least author and year')

    elif args.command == 'lookup':
        if args.citation:
            author, year, title = parse_citation(args.citation)
        else:
            author, year, title = args.author, args.year, args.title
        match = lookup(author, year, title, args.papers_dir)
        if match:
            print(match)
        else:
            # Also show what dirname would be generated
            dirname = generate_dirname(author, year, title)
            print(f"NOT FOUND (would be: {dirname})", file=sys.stderr)
            sys.exit(1)

    elif args.command == 'extract-leads':
        leads, skipped = extract_leads(args.papers_dir)
        if args.json:
            import json
            print(json.dumps({
                'total': len(leads),
                'skipped_existing': skipped,
                'leads': leads,
            }, indent=2))
        else:
            print(f"Total leads: {len(leads)}")
            print(f"Skipped (in collection): {skipped}")
            print("---")
            for lead in leads:
                print(f"[{lead['source']}] {lead['text']}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
