import importlib.util
import json
import sys
import tempfile
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

if "requests" not in sys.modules:
    requests_stub = types.ModuleType("requests")
    requests_stub.get = None
    sys.modules["requests"] = requests_stub

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


FETCH_MODULE = load_module("fetch_paper_module", SCRIPTS_DIR / "fetch_paper.py")


class TestFetchPaperMaterialization(unittest.TestCase):
    def test_failed_download_does_not_create_directory_or_metadata(self) -> None:
        metadata = {
            "title": "Example Paper",
            "authors": ["A. Author"],
            "year": "2024",
            "arxiv_id": None,
            "doi": None,
            "abstract": "Example abstract.",
            "url": "https://example.com/paper",
            "pdf_url": "https://example.com/paper.pdf",
            "first_author_surname": "Author",
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            papers_dir = Path(tmpdir)
            with patch.object(FETCH_MODULE, "resolve_metadata_s2", return_value=metadata):
                with patch.object(FETCH_MODULE, "download_pdf", return_value=False):
                    result = FETCH_MODULE.fetch_paper(
                        "https://example.com/paper",
                        papers_dir,
                    )

            paper_dir = papers_dir / "Author_2024_ExamplePaper"
            self.assertTrue(result["success"])
            self.assertTrue(result["fallback_needed"])
            self.assertFalse(result["pdf_downloaded"])
            self.assertFalse(result["directory_created"])
            self.assertFalse(result["metadata_written"])
            self.assertEqual(result["directory"], str(paper_dir))
            self.assertIn("metadata", result)
            self.assertFalse(paper_dir.exists())
            self.assertNotIn("metadata_path", result)

    def test_successful_download_writes_pdf_and_metadata(self) -> None:
        metadata = {
            "title": "Example Paper",
            "authors": ["A. Author"],
            "year": "2024",
            "arxiv_id": None,
            "doi": None,
            "abstract": "Example abstract.",
            "url": "https://example.com/paper",
            "pdf_url": "https://example.com/paper.pdf",
            "first_author_surname": "Author",
        }

        def fake_download(_url: str, dest: Path) -> bool:
            dest.write_bytes(b"%PDF-1.4\n%test\n")
            return True

        with tempfile.TemporaryDirectory() as tmpdir:
            papers_dir = Path(tmpdir)
            with patch.object(FETCH_MODULE, "resolve_metadata_s2", return_value=metadata):
                with patch.object(FETCH_MODULE, "download_pdf", side_effect=fake_download):
                    result = FETCH_MODULE.fetch_paper(
                        "https://example.com/paper",
                        papers_dir,
                    )

            paper_dir = papers_dir / "Author_2024_ExamplePaper"
            metadata_path = paper_dir / "metadata.json"
            pdf_path = paper_dir / "paper.pdf"

            self.assertTrue(result["success"])
            self.assertTrue(result["pdf_downloaded"])
            self.assertTrue(result["directory_created"])
            self.assertTrue(result["metadata_written"])
            self.assertEqual(result["metadata_path"], str(metadata_path))
            self.assertEqual(result["pdf_path"], str(pdf_path))
            self.assertTrue(pdf_path.exists())
            self.assertTrue(metadata_path.exists())

            written_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            self.assertEqual(written_metadata["title"], "Example Paper")


if __name__ == "__main__":
    unittest.main()
