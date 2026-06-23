"""Tests for the Bookshare browser backend's pure helpers (scripts/bookshare_browser.py).

The Playwright orchestration (download_via_browser) is validated by a live run, not
here. These tests pin the URL/selector/parsing logic that the orchestration relies
on. The module imports Playwright lazily, so it loads without the package installed.
"""

import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BB = load_module("bookshare_browser_module", SCRIPTS_DIR / "bookshare_browser.py")


class HelpersTest(unittest.TestCase):
    def test_build_search_url_encodes_query(self) -> None:
        url = BB.build_search_url("Alice's Adventures in Wonderland")
        self.assertTrue(url.startswith("https://www.bookshare.org/search?keyword="))
        self.assertIn("Alice", url)
        self.assertNotIn(" ", url)  # spaces encoded

    def test_book_id_from_browse_href(self) -> None:
        self.assertEqual(
            BB.book_id_from_href("https://www.bookshare.org/browse/book/250712?x=y"),
            "250712",
        )

    def test_book_id_from_title_instance_href(self) -> None:
        self.assertEqual(
            BB.book_id_from_href("/download/book?titleInstanceId=2054415&downloadFormat=EPUB3&tag=23212039"),
            "2054415",
        )

    def test_book_id_from_href_none_when_absent(self) -> None:
        self.assertIsNone(BB.book_id_from_href("/something/else"))
        self.assertIsNone(BB.book_id_from_href(None))

    def test_download_href_selector_matches_id_and_format(self) -> None:
        sel = BB.download_href_selector("2054415")
        self.assertIn("titleInstanceId=2054415", sel)
        self.assertIn("downloadFormat=EPUB3", sel)

    def test_surname_takes_last_token(self) -> None:
        self.assertEqual(BB._surname("Brandon Sanderson"), "Sanderson")
        self.assertIsNone(BB._surname(None))

    def test_validate_epub_checks_magic(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            good = Path(td) / "good.epub"
            good.write_bytes(b"PK\x03\x04rest")
            bad = Path(td) / "bad.epub"
            bad.write_bytes(b"<html>nope")
            self.assertTrue(BB._validate_epub(good))
            self.assertFalse(BB._validate_epub(bad))


if __name__ == "__main__":
    unittest.main()
