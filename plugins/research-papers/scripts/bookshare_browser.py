#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.40"]
# ///
"""Browser backend for Bookshare: log in and download an EPUB with Playwright.

This is the default Bookshare backend. It works with just a username/password
(no developer api_key), driving a real browser the way a member would:

  log in at /login -> search -> request EPUB download -> Bookshare prepares it
  asynchronously -> it appears "Available" in /bookHistory as
  GET /download/book?titleInstanceId=<id>&downloadFormat=EPUB3&tag=<tag> -> save it.

The book lands in papers/<dirname>/book.epub with a metadata.json, conforming to the
source-adapter contract. Playwright is imported lazily so the pure helpers (and the
unit tests) load without the package; the script provisions it via PEP 723 + uv, and
launches the system Chrome (channel="chrome") to avoid a browser download.

Usage:
  uv run bookshare_browser.py "<title or Bookshare ID>" --root . --papers-dir papers/
  uv run bookshare_browser.py "Alice in Wonderland" --root . --no-headless
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paper_id import generate_dirname  # noqa: E402
import credential_store  # noqa: E402

logger = logging.getLogger(__name__)

SOURCE = "bookshare"
BASE = "https://www.bookshare.org"
LOGIN_URL = f"{BASE}/login"
HISTORY_URL = f"{BASE}/bookHistory"
ARTIFACT_NAME = "book.epub"
EPUB_MAGIC = b"PK\x03\x04"
DOWNLOAD_FORMAT = "EPUB3"   # URL param value used in the /download/book link
EPUB_OPTION = "EPUB"        # combobox option label on the search row


# --- pure helpers (unit-tested) -------------------------------------------

def build_search_url(query: str) -> str:
    return f"{BASE}/search?keyword={quote(query)}"


def book_id_from_href(href: str | None) -> str | None:
    """Extract the Bookshare title id from a /browse/book/<id> or titleInstanceId href."""
    if not href:
        return None
    m = re.search(r"/browse/book/(\d+)", href)
    if m:
        return m.group(1)
    m = re.search(r"titleInstanceId=(\d+)", href)
    return m.group(1) if m else None


def download_href_selector(title_instance_id: str, fmt: str = DOWNLOAD_FORMAT) -> str:
    """CSS selector for the 'Available' download link of a given title in history."""
    return f"a[href*='titleInstanceId={title_instance_id}'][href*='downloadFormat={fmt}']"


def _surname(author: str | None) -> str | None:
    return author.split()[-1] if author else None


def _validate_epub(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            return f.read(4) == EPUB_MAGIC
    except OSError:
        return False


def _write_metadata(paper_dir: Path, meta: dict) -> Path:
    paper_dir.mkdir(parents=True, exist_ok=True)
    p = paper_dir / "metadata.json"
    p.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return p


def _fallback(identifier: str, error: str, extra: dict | None = None) -> dict:
    out = {"success": False, "source": SOURCE, "identifier": identifier,
           "error": error, "fallback_needed": True}
    if extra:
        out.update(extra)
    return out


# --- Playwright orchestration (live; not unit-tested) ---------------------

def _launch(pw, headless: bool):
    """Prefer the system Chrome (no browser download); fall back to bundled chromium."""
    try:
        return pw.chromium.launch(channel="chrome", headless=headless)
    except Exception:  # noqa: BLE001
        return pw.chromium.launch(headless=headless)


def _login(page, username: str, password: str) -> None:
    page.goto(LOGIN_URL, wait_until="domcontentloaded")
    page.get_by_role("textbox", name=re.compile("Email or Username", re.I)).fill(username)
    page.get_by_role("textbox", name=re.compile("Password", re.I)).fill(password)
    page.get_by_role("button", name=re.compile(r"^\s*Log In\s*$", re.I)).click()
    page.wait_for_load_state("domcontentloaded")


def _extract_first_result(page, identifier: str) -> dict:
    """Return {title_instance_id, title, author, year} for the first search hit."""
    page.goto(build_search_url(identifier), wait_until="domcontentloaded")
    row = page.locator("tr:has(a[href*='/browse/book/'])").first
    row.wait_for(timeout=30000)
    browse = row.locator("a[href*='/browse/book/']").first
    tid = book_id_from_href(browse.get_attribute("href"))
    title = (browse.inner_text() or "").strip() or identifier
    author = None
    a_loc = row.locator("a[href*='author=']").first
    if a_loc.count():
        author = (a_loc.inner_text() or "").strip() or None
    ym = re.search(r"\b(?:19|20)\d{2}\b", row.inner_text() or "")
    year = ym.group(0) if ym else None
    return {"row": row, "title_instance_id": tid, "title": title,
            "author": author, "year": year}


def _request_epub(row) -> None:
    row.get_by_role("combobox").select_option(EPUB_OPTION)
    row.get_by_role("button", name=re.compile("Download", re.I)).click()


def _poll_available(page, selector: str, timeout: int):
    """Reload history until the download link appears; return the locator or None."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        page.goto(HISTORY_URL, wait_until="domcontentloaded")
        loc = page.locator(selector).first
        if loc.count() > 0:
            return loc
        page.wait_for_timeout(5000)
    return None


def download_via_browser(identifier: str, papers_dir, root: str = ".",
                         output_dir: str | None = None, metadata_only: bool = False,
                         headless: bool = True, timeout: int = 180) -> dict:
    """Log in and download (or just resolve metadata for) a Bookshare title."""
    secrets = credential_store.require_secrets(SOURCE, ["username", "password"], root)
    papers_dir = Path(papers_dir)

    from playwright.sync_api import sync_playwright  # lazy: keeps import light for tests

    with sync_playwright() as pw:
        browser = _launch(pw, headless)
        ctx = browser.new_context(accept_downloads=True)
        page = ctx.new_page()
        try:
            _login(page, secrets["username"], secrets["password"])
            info = _extract_first_result(page, identifier)
            tid = info["title_instance_id"]
            if not tid:
                return _fallback(identifier, "no search result found")

            dirname = output_dir or generate_dirname(
                _surname(info["author"]), info["year"], info["title"]
            ) or f"{SOURCE}_{tid}"
            paper_dir = papers_dir / dirname
            meta = {k: v for k, v in {
                "title": info["title"],
                "authors": [info["author"]] if info["author"] else None,
                "year": info["year"], "bookshareId": tid, "source": SOURCE,
            }.items() if v}

            result = {
                "success": True, "source": SOURCE,
                "directory": str(paper_dir), "dirname": dirname,
                "title": info["title"], "authors": meta.get("authors"),
                "year": info["year"], "artifact_path": None, "artifact_type": None,
                "metadata_path": None, "downloaded": False, "pdf_path": None,
                "fallback_needed": False,
            }

            if metadata_only:
                result["metadata_path"] = str(_write_metadata(paper_dir, meta))
                return result

            _request_epub(info["row"])
            link = _poll_available(page, download_href_selector(tid), timeout)
            if link is None:
                return _fallback(identifier, "download did not become available in time",
                                 {"directory": str(paper_dir), "dirname": dirname})

            paper_dir.mkdir(parents=True, exist_ok=True)
            dest = paper_dir / ARTIFACT_NAME
            with page.expect_download(timeout=60000) as di:
                link.click()
            di.value.save_as(str(dest))
            if not _validate_epub(dest):
                Path(dest).unlink(missing_ok=True)
                return _fallback(identifier, "downloaded file is not a valid EPUB",
                                 {"directory": str(paper_dir), "dirname": dirname})

            result["metadata_path"] = str(_write_metadata(paper_dir, meta))
            result.update({
                "artifact_path": str(dest), "artifact_type": "epub",
                "downloaded": True, "artifact_size": dest.stat().st_size,
            })
            return result
        finally:
            ctx.close()
            browser.close()


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Download a book from Bookshare via a browser")
    p.add_argument("identifier", help="a title or Bookshare ID")
    p.add_argument("--papers-dir", default="papers/")
    p.add_argument("--root", default=".")
    p.add_argument("--output-dir")
    p.add_argument("--metadata-only", action="store_true")
    p.add_argument("--no-headless", dest="headless", action="store_false",
                   help="Show the browser window")
    p.add_argument("--timeout", type=int, default=180)
    p.set_defaults(headless=True)
    args = p.parse_args(argv)

    try:
        result = download_via_browser(
            args.identifier, Path(args.papers_dir), root=args.root,
            output_dir=args.output_dir, metadata_only=args.metadata_only,
            headless=args.headless, timeout=args.timeout,
        )
    except credential_store.CredentialError as exc:
        result = _fallback(args.identifier, str(exc))

    print(json.dumps(result, indent=2))
    if not result.get("success"):
        sys.exit(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
