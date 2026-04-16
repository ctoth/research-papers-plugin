import importlib.util
import sys
import threading
import types
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"

if "arxiv" not in sys.modules:
    arxiv_stub = types.ModuleType("arxiv")
    arxiv_stub.Client = object
    arxiv_stub.Search = object
    sys.modules["arxiv"] = arxiv_stub

if "semanticscholar" not in sys.modules:
    semanticscholar_stub = types.ModuleType("semanticscholar")

    class _SemanticScholar:
        pass

    semanticscholar_stub.SemanticScholar = _SemanticScholar
    sys.modules["semanticscholar"] = semanticscholar_stub


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SEARCH_MODULE = load_module("search_papers_module", SCRIPTS_DIR / "search_papers.py")


class TestSearchPapers(unittest.TestCase):
    def test_all_sources_run_concurrently_but_merge_in_stable_order(self) -> None:
        arxiv_entered = threading.Event()
        s2_entered = threading.Event()
        overlapped: dict[str, bool] = {}

        def arxiv_search(_query: str, _max_results: int) -> list[dict]:
            arxiv_entered.set()
            overlapped["arxiv"] = s2_entered.wait(timeout=1)
            return [{"title": "Arxiv Result", "authors": [], "source": "arxiv"}]

        def s2_search(_query: str, _max_results: int) -> list[dict]:
            s2_entered.set()
            overlapped["s2"] = arxiv_entered.wait(timeout=1)
            return [{"title": "S2 Result", "authors": [], "source": "s2"}]

        with patch.dict(
            SEARCH_MODULE.SEARCHERS,
            {"arxiv": arxiv_search, "s2": s2_search},
            clear=True,
        ):
            results, errors = SEARCH_MODULE.run_searches("query", 5, "all")

        self.assertEqual(errors, [])
        self.assertEqual([r["source"] for r in results], ["arxiv", "s2"])
        self.assertEqual(overlapped, {"arxiv": True, "s2": True})

    def test_source_errors_do_not_drop_other_results(self) -> None:
        def arxiv_search(_query: str, _max_results: int) -> list[dict]:
            return [{"title": "Arxiv Result", "authors": [], "source": "arxiv"}]

        def s2_search(_query: str, _max_results: int) -> list[dict]:
            raise RuntimeError("rate limited")

        with patch.dict(
            SEARCH_MODULE.SEARCHERS,
            {"arxiv": arxiv_search, "s2": s2_search},
            clear=True,
        ):
            results, errors = SEARCH_MODULE.run_searches("query", 5, "all")

        self.assertEqual([r["source"] for r in results], ["arxiv"])
        self.assertEqual(errors, ["s2: rate limited"])

    def test_deduplicate_matches_doi_case_insensitively(self) -> None:
        results = SEARCH_MODULE.deduplicate(
            [
                {"title": "First", "doi": "10.1000/ABC"},
                {"title": "Duplicate", "doi": " 10.1000/abc "},
                {"title": "Different", "doi": "10.1000/def"},
            ]
        )

        self.assertEqual([r["title"] for r in results], ["First", "Different"])


if __name__ == "__main__":
    unittest.main()
