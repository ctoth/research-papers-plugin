#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["requests>=2.28"]
# ///
"""Fetch a book (EPUB3) from Bookshare into the papers/ collection.

Reference implementation of the authenticated source-adapter contract
(templates/source-adapter/HOWTO.md): resolves a title, downloads book.epub into
papers/<dirname>/, writes metadata.json, prints one JSON result, exits 0/1.

Authentication/token caching go through bookshare_auth -> credential_store; this
script never reads .secrets/ directly. Guest mode (no token) reaches only
public-domain / Creative Commons titles.

Usage:
  uv run fetch_book.py "<title or Bookshare ID>" --root . --papers-dir papers/
  uv run fetch_book.py 123456 --root . --metadata-only
  uv run fetch_book.py "Pride and Prejudice" --guest --papers-dir papers/
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import tempfile
from pathlib import Path

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paper_id import generate_dirname  # noqa: E402
import credential_store  # noqa: E402
import bookshare_auth  # noqa: E402

logger = logging.getLogger(__name__)

SOURCE = "bookshare"
API_BASE = "https://api.bookshare.org/v2"
ARTIFACT_NAME = "book.epub"
EPUB_MAGIC = b"PK\x03\x04"


def _api_base(root: str) -> str:
    return credential_store.config_for_source(SOURCE, root).get("api_base", API_BASE)


def _headers(token: dict | None) -> dict:
    if token and token.get("access_token"):
        return {"Authorization": f"Bearer {token['access_token']}"}
    return {}


def _surname(authors) -> str | None:
    if not authors:
        return None
    first = authors[0]
    name = first.get("name") if isinstance(first, dict) else first
    return name.split()[-1] if name else None


def _map_title(raw: dict) -> dict:
    """Map a Bookshare title record into the adapter metadata shape."""
    authors = [a.get("name") if isinstance(a, dict) else a
               for a in (raw.get("authors") or [])]
    year = None
    pub = raw.get("publishDate") or raw.get("copyright")
    if pub:
        digits = "".join(ch for ch in str(pub) if ch.isdigit())[:4]
        year = digits or None
    return {
        "bookshareId": str(raw.get("bookshareId") or raw.get("id") or ""),
        "title": raw.get("title"),
        "authors": authors,
        "year": year,
        "first_author_surname": _surname(authors),
    }


def search_titles(query: str, api_key: str | None = None, token: dict | None = None,
                  api_base: str = API_BASE) -> list[dict]:
    """Search the Bookshare catalog by title. Returns mapped candidate dicts."""
    params = {"title": query}
    if api_key:
        params["api_key"] = api_key
    resp = requests.get(f"{api_base}/titles", params=params,
                        headers=_headers(token), timeout=30)
    resp.raise_for_status()
    data = resp.json()
    titles = data.get("titles", []) if isinstance(data, dict) else []
    return [_map_title(t) for t in titles]


def _get_title_metadata(title_id: str, api_key: str | None, token: dict | None,
                        api_base: str) -> dict | None:
    params = {"api_key": api_key} if api_key else {}
    resp = requests.get(f"{api_base}/titles/{title_id}", params=params,
                        headers=_headers(token), timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return _map_title(data) if data else None


def resolve_metadata(identifier: str, api_key: str | None = None,
                     token: dict | None = None, api_base: str = API_BASE) -> dict | None:
    """Resolve a Bookshare ID or title query into adapter metadata, or None."""
    ident = identifier.strip()
    if ident.isdigit():
        meta = _get_title_metadata(ident, api_key, token, api_base)
        if meta:
            return meta
    candidates = search_titles(ident, api_key, token, api_base)
    return candidates[0] if candidates else None


def download_epub(title_id: str, dest: Path, api_key: str | None = None,
                  token: dict | None = None, api_base: str = API_BASE) -> bool:
    """Download a title's EPUB3 to dest. Validates EPUB (ZIP) magic. True on success."""
    params = {}
    if api_key:
        params["api_key"] = api_key
    url = f"{api_base}/titles/{title_id}/EPUB3"
    try:
        resp = requests.get(url, params=params, headers=_headers(token),
                            timeout=120, stream=True)
        resp.raise_for_status()
        first = b""
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if not first:
                    first = chunk[:4]
                f.write(chunk)
        if first[:4] != EPUB_MAGIC:
            Path(dest).unlink(missing_ok=True)
            return False
        return True
    except Exception as exc:  # noqa: BLE001 - network/IO best-effort
        logger.info("EPUB download failed: %s", exc)
        Path(dest).unlink(missing_ok=True)
        return False


def fetch_book(identifier: str, papers_dir: Path, root: str = ".",
               output_dir: str | None = None, metadata_only: bool = False,
               guest: bool = False, auth_method: str | None = None) -> dict:
    api_base = _api_base(root)
    api_key = credential_store.get_secret(SOURCE, "api_key", root)
    token = None
    if not guest:
        method = auth_method or credential_store.auth_method(SOURCE, root)
        token = bookshare_auth.get_token_or_authenticate(root=root, auth_method=method)

    metadata = resolve_metadata(identifier, api_key, token, api_base)
    if not metadata:
        return {"success": False, "source": SOURCE, "error": "title not resolved",
                "identifier": identifier, "fallback_needed": True}

    dirname = output_dir or generate_dirname(
        metadata.get("first_author_surname"),
        metadata.get("year"),
        metadata.get("title"),
    ) or f"{SOURCE}_{identifier}".replace("/", "_")
    paper_dir = papers_dir / dirname
    meta_out = {k: v for k, v in metadata.items()
                if k != "first_author_surname" and v is not None}
    meta_out["source"] = SOURCE

    result = {
        "success": True, "source": SOURCE,
        "directory": str(paper_dir), "dirname": dirname,
        "title": metadata.get("title"), "authors": metadata.get("authors"),
        "year": metadata.get("year"),
        "artifact_path": None, "artifact_type": None, "metadata_path": None,
        "downloaded": False, "pdf_path": None, "fallback_needed": False,
    }

    if metadata_only:
        paper_dir.mkdir(parents=True, exist_ok=True)
        meta_path = paper_dir / "metadata.json"
        meta_path.write_text(json.dumps(meta_out, indent=2, ensure_ascii=False),
                             encoding="utf-8")
        result["metadata_path"] = str(meta_path)
        return result

    fd, tmp = tempfile.mkstemp(prefix="temp_fetch_", suffix=".epub",
                               dir=str(papers_dir) if papers_dir.exists() else None)
    os.close(fd)
    tmp_path = Path(tmp)
    downloaded = False
    try:
        downloaded = download_epub(metadata.get("bookshareId") or identifier,
                                   tmp_path, api_key, token, api_base)
    finally:
        if not downloaded:
            tmp_path.unlink(missing_ok=True)

    if downloaded:
        paper_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = paper_dir / ARTIFACT_NAME
        tmp_path.replace(artifact_path)
        meta_path = paper_dir / "metadata.json"
        meta_path.write_text(json.dumps(meta_out, indent=2, ensure_ascii=False),
                             encoding="utf-8")
        result.update({
            "artifact_path": str(artifact_path), "artifact_type": "epub",
            "metadata_path": str(meta_path), "downloaded": True,
            "artifact_size": artifact_path.stat().st_size,
        })
    else:
        result["fallback_needed"] = True

    return result


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Fetch a book (EPUB3) from Bookshare")
    p.add_argument("identifier", help="a title or Bookshare ID")
    p.add_argument("--papers-dir", default="papers/")
    p.add_argument("--root", default=".")
    p.add_argument("--output-dir")
    p.add_argument("--metadata-only", action="store_true")
    p.add_argument("--auth-method", choices=["api", "browser"])
    p.add_argument("--guest", action="store_true",
                   help="No token; public-domain/CC titles only")
    args = p.parse_args(argv)

    result = fetch_book(args.identifier, Path(args.papers_dir), root=args.root,
                        output_dir=args.output_dir, metadata_only=args.metadata_only,
                        guest=args.guest, auth_method=args.auth_method)
    print(json.dumps(result, indent=2))
    if not result.get("success"):
        sys.exit(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
