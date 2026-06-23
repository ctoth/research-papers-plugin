"""Tests for the Bookshare fetch adapter (scripts/fetch_book.py).

No real network: `requests` is stubbed, the network-touching functions are patched,
and auth is patched so no token is acquired. Credential state and papers/ are
sandboxed under a tempfile root. Mirrors test_fetch_paper.py conventions.
"""

import importlib.util
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"

# Ensure a `requests` module exists with get/post attrs, regardless of whether a
# sibling test already installed a partial stub (order-independent).
_req = sys.modules.get("requests")
if _req is None:
    _req = types.ModuleType("requests")
    sys.modules["requests"] = _req
for _attr in ("get", "post"):
    if not hasattr(_req, _attr):
        setattr(_req, _attr, None)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


FETCH = load_module("fetch_book_module", SCRIPTS_DIR / "fetch_book.py")
CRED = FETCH.credential_store

META = {
    "title": "Example Book", "authors": ["A. Author"], "year": "2024",
    "first_author_surname": "Author", "bookshareId": "123",
}


def _write_epub(_title_id, dest, *_a, **_k):
    # Matches download_epub(title_id, dest, ...): dest is the SECOND positional arg.
    Path(dest).write_bytes(b"PK\x03\x04" + b"\x00" * 32)
    return True


class FetchBookContractTest(unittest.TestCase):
    def test_success_writes_epub_and_metadata_with_expected_dirname(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            papers = Path(td) / "papers"
            papers.mkdir()
            CRED.save("bookshare", {"secrets": {"api_key": "KEY"}}, td)
            with patch.object(FETCH, "resolve_metadata", return_value=META):
                with patch.object(FETCH, "download_epub", side_effect=_write_epub):
                    with patch.object(FETCH.bookshare_auth, "get_token_or_authenticate",
                                      return_value={"access_token": "T"}):
                        result = FETCH.fetch_book("Example Book", papers, root=td)

            self.assertTrue(result["success"])
            self.assertEqual(result["source"], "bookshare")
            self.assertEqual(result["dirname"], "Author_2024_ExampleBook")
            self.assertTrue(result["downloaded"])
            self.assertEqual(result["artifact_type"], "epub")
            artifact = Path(result["artifact_path"])
            self.assertTrue(artifact.exists())
            self.assertEqual(artifact.name, "book.epub")
            # The real EPUB bytes must land in the artifact (not an empty temp file).
            self.assertTrue(artifact.read_bytes().startswith(b"PK\x03\x04"))
            meta = json.loads(Path(result["metadata_path"]).read_text(encoding="utf-8"))
            self.assertEqual(meta["source"], "bookshare")
            self.assertEqual(meta["title"], "Example Book")

    def test_failed_download_creates_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            papers = Path(td) / "papers"
            papers.mkdir()
            with patch.object(FETCH, "resolve_metadata", return_value=META):
                with patch.object(FETCH, "download_epub", return_value=False):
                    with patch.object(FETCH.bookshare_auth, "get_token_or_authenticate",
                                      return_value={"access_token": "T"}):
                        result = FETCH.fetch_book("Example Book", papers, root=td)
            self.assertTrue(result["fallback_needed"])
            self.assertFalse(result["downloaded"])
            self.assertFalse(Path(result["directory"]).exists())

    def test_guest_mode_skips_auth(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            papers = Path(td) / "papers"
            papers.mkdir()
            with patch.object(FETCH, "resolve_metadata", return_value=META):
                with patch.object(FETCH, "download_epub", side_effect=_write_epub):
                    with patch.object(
                        FETCH.bookshare_auth, "get_token_or_authenticate",
                        side_effect=AssertionError("auth must not run in guest mode"),
                    ):
                        result = FETCH.fetch_book("Example Book", papers, root=td, guest=True)
            self.assertTrue(result["success"])
            self.assertTrue(result["downloaded"])


class DownloadEpubValidationTest(unittest.TestCase):
    def _fake_get(self, body: bytes):
        resp = MagicMock()
        resp.raise_for_status.return_value = None
        resp.iter_content = lambda chunk_size=8192: iter([body])
        return MagicMock(return_value=resp)

    def test_rejects_non_zip_body(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td) / "book.epub"
            with patch.object(FETCH.requests, "get", self._fake_get(b"<html>nope</html>")):
                ok = FETCH.download_epub("123", dest, api_key="KEY", token={"access_token": "T"})
            self.assertFalse(ok)
            self.assertFalse(dest.exists())

    def test_accepts_zip_magic_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td) / "book.epub"
            with patch.object(FETCH.requests, "get",
                              self._fake_get(b"PK\x03\x04" + b"\x00" * 64)):
                ok = FETCH.download_epub("123", dest, api_key="KEY", token={"access_token": "T"})
            self.assertTrue(ok)
            self.assertTrue(dest.exists())


class MainExitCodeTest(unittest.TestCase):
    def test_main_exits_zero_on_success(self) -> None:
        with patch.object(FETCH, "fetch_book", return_value={"success": True}):
            # No SystemExit on success.
            self.assertIsNone(FETCH.main(["x", "--root", "."]))

    def test_main_exits_one_on_failure(self) -> None:
        with patch.object(FETCH, "fetch_book", return_value={"success": False}):
            with self.assertRaises(SystemExit) as ctx:
                FETCH.main(["x", "--root", "."])
            self.assertEqual(ctx.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
