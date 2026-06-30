import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"

# Offline: stub the network-touching third-party modules before import.
if "requests" not in sys.modules:
    requests_stub = types.ModuleType("requests")

    class _RequestException(Exception):
        pass

    requests_stub.RequestException = _RequestException
    requests_stub.get = lambda *a, **k: (_ for _ in ()).throw(_RequestException("no network in tests"))
    sys.modules["requests"] = requests_stub

if "semanticscholar" not in sys.modules:
    s2_stub = types.ModuleType("semanticscholar")

    class _SemanticScholar:
        pass

    s2_stub.SemanticScholar = _SemanticScholar
    sys.modules["semanticscholar"] = s2_stub


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VCR = load_module("verify_citations_real", SCRIPTS_DIR / "verify_citations_real.py")


def _entry(key, title, doi=None, url=None, year=None, author="Vaswani"):
    return {"key": key, "title": title, "doi": doi, "url": url, "year": year, "author": author}


class FastPathDoiTests(unittest.TestCase):
    def test_doi_title_match_no_search(self) -> None:
        entry = _entry("vaswani2017", "Attention Is All You Need", doi="10.5555/3295222", year="2017")
        with patch.object(VCR, "crossref_lookup_doi",
                          return_value={"title": "Attention Is All You Need",
                                        "authors": ["Vaswani"], "year": "2017"}) as cr, \
             patch.object(VCR, "search_scholarly") as search:
            verdict = VCR.verify_citation(entry, papers_dir=None)
        self.assertEqual(verdict.verdict, "REAL")
        cr.assert_called_once()
        search.assert_not_called()

    def test_doi_404_not_found(self) -> None:
        entry = _entry("ghost2099", "A Paper That Does Not Exist", doi="10.0000/nope", year="2099")
        with patch.object(VCR, "crossref_lookup_doi", return_value=None):
            verdict = VCR.verify_citation(entry, papers_dir=None)
        self.assertEqual(verdict.verdict, "NOT_FOUND")

    def test_doi_title_mismatch(self) -> None:
        entry = _entry("vaswani2017", "Attention Is All You Need", doi="10.5555/3295222", year="2017")
        with patch.object(VCR, "crossref_lookup_doi",
                          return_value={"title": "Some Entirely Unrelated Title About Frogs",
                                        "authors": ["Other"], "year": "2017"}):
            verdict = VCR.verify_citation(entry, papers_dir=None)
        self.assertEqual(verdict.verdict, "MISMATCH")

    def test_unverified_on_timeout(self) -> None:
        entry = _entry("vaswani2017", "Attention Is All You Need", doi="10.5555/3295222", year="2017")
        with patch.object(VCR, "crossref_lookup_doi", side_effect=TimeoutError("slow API")):
            verdict = VCR.verify_citation(entry, papers_dir=None)
        self.assertEqual(verdict.verdict, "UNVERIFIED")


class FallbackSearchTests(unittest.TestCase):
    def test_title_only_fallback_match(self) -> None:
        entry = _entry("vaswani2017", "Attention Is All You Need", year="2017")  # no doi/url
        with patch.object(VCR, "crossref_lookup_doi") as cr, \
             patch.object(VCR, "search_scholarly",
                          return_value={"title": "Attention is all you need", "year": "2018"}):
            verdict = VCR.verify_citation(entry, papers_dir=None)
        self.assertEqual(verdict.verdict, "REAL")  # >=0.9 fuzzy, within +/-1 year
        cr.assert_not_called()  # no DOI -> no DOI lookup

    def test_not_found(self) -> None:
        entry = _entry("ghost2099", "A Paper That Does Not Exist", year="2099")
        with patch.object(VCR, "search_scholarly", return_value=None):
            verdict = VCR.verify_citation(entry, papers_dir=None)
        self.assertEqual(verdict.verdict, "NOT_FOUND")


class LocalStampTests(unittest.TestCase):
    def test_local_stamp_skips_network(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            papers = Path(tmp) / "papers"
            d = papers / "vaswani2017"
            d.mkdir(parents=True)
            (d / "metadata.json").write_text(
                json.dumps({
                    "cite_key": "vaswani2017",
                    "title": "Attention Is All You Need",
                    "doi": "10.5555/3295222",
                    "verification": {"status": "REAL",
                                     "doi": "10.5555/3295222",
                                     "title": "Attention Is All You Need"},
                }),
                encoding="utf-8",
            )
            entry = _entry("vaswani2017", "Attention Is All You Need", doi="10.5555/3295222", year="2017")
            with patch.object(VCR, "crossref_lookup_doi") as cr, \
                 patch.object(VCR, "search_scholarly") as search:
                verdict = VCR.verify_citation(entry, papers_dir=papers)
            self.assertEqual(verdict.verdict, "REAL")
            cr.assert_not_called()
            search.assert_not_called()


class MainExitTests(unittest.TestCase):
    def _run(self, bibtex_text: str) -> tuple[int, str]:
        with tempfile.TemporaryDirectory() as tmp:
            bib = Path(tmp) / "citations.bibtex"
            bib.write_text(bibtex_text, encoding="utf-8")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = VCR.main([str(bib)])
            return rc, buf.getvalue()

    def test_main_exits_two_on_not_found(self) -> None:
        bib = "@article{ghost2099,\n  title={A Paper That Does Not Exist},\n  doi={10.0000/nope},\n}\n"
        with patch.object(VCR, "crossref_lookup_doi", return_value=None):
            rc, out = self._run(bib)
        self.assertEqual(rc, 2)
        self.assertIn("NOT_FOUND", out)
        self.assertIn("ghost2099", out)

    def test_main_exits_zero_when_all_real(self) -> None:
        bib = "@article{vaswani2017,\n  title={Attention Is All You Need},\n  doi={10.5555/3295222},\n  year={2017},\n}\n"
        with patch.object(VCR, "crossref_lookup_doi",
                          return_value={"title": "Attention Is All You Need",
                                        "authors": ["Vaswani"], "year": "2017"}):
            rc, out = self._run(bib)
        self.assertEqual(rc, 0)
        self.assertIn("REAL", out)


if __name__ == "__main__":
    unittest.main()
