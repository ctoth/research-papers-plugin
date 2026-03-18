#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["arxiv>=2.1", "semanticscholar>=0.8", "requests>=2.28"]
# ///
"""Fetch a paper PDF with metadata via waterfall download strategy.

Usage:
  uv run fetch_paper.py 1706.03762 --papers-dir papers/
  uv run fetch_paper.py "10.18653/v1/2023.acl-long.1" --papers-dir papers/
  uv run fetch_paper.py https://arxiv.org/abs/2401.12345 --papers-dir papers/
  uv run fetch_paper.py 1706.03762 --metadata-only
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import arxiv
import requests
from semanticscholar import SemanticScholar

# Add scripts dir to path for _paper_id import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paper_id import IdType, classify_identifier, generate_dirname  # noqa: E402

UNPAYWALL_EMAIL = "research-papers-plugin@example.com"


def resolve_metadata_arxiv(arxiv_id: str) -> dict | None:
    """Fetch metadata from arxiv."""
    client = arxiv.Client()
    search = arxiv.Search(id_list=[arxiv_id])
    results = list(client.results(search))
    if not results:
        return None
    r = results[0]
    first_author = r.authors[0].name.split()[-1] if r.authors else "Unknown"
    year = str(r.published.year) if r.published else None
    return {
        'title': r.title,
        'authors': [a.name for a in r.authors],
        'year': year,
        'arxiv_id': arxiv_id,
        'doi': r.doi,
        'abstract': r.summary,
        'url': r.entry_id,
        'pdf_url': r.pdf_url,
        'first_author_surname': first_author,
    }


def resolve_metadata_s2(s2_query: str) -> dict | None:
    """Fetch metadata from Semantic Scholar."""
    sch = SemanticScholar()
    try:
        paper = sch.get_paper(
            s2_query,
            fields=[
                'title', 'authors', 'year', 'externalIds',
                'url', 'abstract', 'openAccessPdf',
            ],
        )
    except Exception:
        return None
    if not paper or not paper.title:
        return None
    ext = paper.externalIds or {}
    first_author = "Unknown"
    if paper.authors:
        name = paper.authors[0].name
        first_author = name.split()[-1] if name else "Unknown"
    oa_pdf = None
    if paper.openAccessPdf:
        oa_pdf = paper.openAccessPdf.get('url')
    return {
        'title': paper.title,
        'authors': [a.name for a in (paper.authors or [])],
        'year': str(paper.year) if paper.year else None,
        'arxiv_id': ext.get('ArXiv'),
        'doi': ext.get('DOI'),
        'abstract': paper.abstract,
        'url': paper.url,
        'pdf_url': oa_pdf,
        'first_author_surname': first_author,
    }


def try_unpaywall(doi: str) -> str | None:
    """Try Unpaywall API for a legal open-access PDF URL."""
    if not doi:
        return None
    url = f"https://api.unpaywall.org/v2/{doi}?email={UNPAYWALL_EMAIL}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.json()
        best = data.get('best_oa_location')
        if best:
            return best.get('url_for_pdf') or best.get('url')
    except Exception:
        pass
    return None


def download_pdf(url: str, dest: Path) -> bool:
    """Download a PDF from url to dest. Returns True on success."""
    try:
        resp = requests.get(url, timeout=60, stream=True)
        resp.raise_for_status()
        content_start = b''
        with open(dest, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if not content_start:
                    content_start = chunk[:16]
                f.write(chunk)
        # Verify it looks like a PDF
        if content_start[:5] != b'%PDF-':
            dest.unlink(missing_ok=True)
            return False
        return True
    except Exception:
        dest.unlink(missing_ok=True)
        return False


def fetch_paper(identifier: str, papers_dir: Path, output_dir: str | None = None,
                metadata_only: bool = False) -> dict:
    """Fetch a paper. Returns a JSON-serializable summary dict."""
    id_type, value = classify_identifier(identifier)

    # --- Resolve metadata ---
    metadata = None

    if id_type in (IdType.ARXIV_ID, IdType.ARXIV_URL):
        metadata = resolve_metadata_arxiv(value)
        # Supplement with S2 if arxiv didn't give a DOI
        if metadata and not metadata.get('doi'):
            s2_meta = resolve_metadata_s2(f"ArXiv:{value}")
            if s2_meta and s2_meta.get('doi'):
                metadata['doi'] = s2_meta['doi']
            if s2_meta and s2_meta.get('pdf_url') and not metadata.get('pdf_url'):
                metadata['pdf_url'] = s2_meta['pdf_url']
    elif id_type == IdType.DOI:
        metadata = resolve_metadata_s2(f"DOI:{value}")
    elif id_type == IdType.ACL_URL:
        metadata = resolve_metadata_s2(f"ACL:{value}")
        # ACL papers have direct PDF URLs
        if metadata and not metadata.get('pdf_url'):
            metadata['pdf_url'] = f"https://aclanthology.org/{value}.pdf"
    elif id_type == IdType.S2_ID:
        metadata = resolve_metadata_s2(f"CorpusId:{value}")
    else:
        # Generic URL — try S2 by URL
        metadata = resolve_metadata_s2(f"URL:{value}")

    if not metadata:
        return {'success': False, 'error': 'Could not resolve metadata',
                'identifier': identifier}

    # --- Determine output directory ---
    if output_dir:
        dirname = output_dir
    else:
        dirname = generate_dirname(
            metadata['first_author_surname'],
            metadata.get('year'),
            metadata.get('title'),
        )
    if not dirname:
        dirname = f"paper_{value.replace('/', '_')}"

    paper_dir = papers_dir / dirname
    paper_dir.mkdir(parents=True, exist_ok=True)

    # Write metadata
    meta_path = paper_dir / 'metadata.json'
    meta_out = {k: v for k, v in metadata.items()
                if k != 'first_author_surname'}
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta_out, f, indent=2, ensure_ascii=False)

    result = {
        'success': True,
        'directory': str(paper_dir),
        'dirname': dirname,
        'metadata_path': str(meta_path),
        'title': metadata.get('title'),
        'authors': metadata.get('authors'),
        'year': metadata.get('year'),
    }

    if metadata_only:
        result['pdf_downloaded'] = False
        return result

    # --- Download waterfall ---
    pdf_path = paper_dir / 'paper.pdf'
    downloaded = False

    # 1. Direct PDF URL from metadata (arxiv, ACL, S2 open access)
    if metadata.get('pdf_url'):
        downloaded = download_pdf(metadata['pdf_url'], pdf_path)

    # 2. Arxiv PDF URL construction
    if not downloaded and metadata.get('arxiv_id'):
        arxiv_url = f"https://arxiv.org/pdf/{metadata['arxiv_id']}.pdf"
        downloaded = download_pdf(arxiv_url, pdf_path)

    # 3. ACL direct download
    if not downloaded and id_type == IdType.ACL_URL:
        acl_url = f"https://aclanthology.org/{value}.pdf"
        downloaded = download_pdf(acl_url, pdf_path)

    # 4. Unpaywall
    if not downloaded and metadata.get('doi'):
        unpaywall_url = try_unpaywall(metadata['doi'])
        if unpaywall_url:
            downloaded = download_pdf(unpaywall_url, pdf_path)

    result['pdf_downloaded'] = downloaded
    if downloaded:
        result['pdf_path'] = str(pdf_path)
        result['pdf_size'] = pdf_path.stat().st_size
    else:
        result['fallback_needed'] = True
        result['doi'] = metadata.get('doi')

    return result


def main():
    parser = argparse.ArgumentParser(description='Fetch a paper PDF')
    parser.add_argument('identifier', help='arxiv ID/URL, DOI, ACL URL, or S2 ID')
    parser.add_argument('--papers-dir', default='papers/',
                        help='Papers collection directory (default: papers/)')
    parser.add_argument('--output-dir',
                        help='Override output directory name')
    parser.add_argument('--metadata-only', action='store_true',
                        help='Only fetch metadata, skip PDF download')
    args = parser.parse_args()

    result = fetch_paper(
        args.identifier,
        Path(args.papers_dir),
        output_dir=args.output_dir,
        metadata_only=args.metadata_only,
    )

    print(json.dumps(result, indent=2))
    if not result.get('success'):
        sys.exit(1)


if __name__ == '__main__':
    main()
