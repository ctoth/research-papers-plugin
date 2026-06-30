import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


LIT = load_module("lit_review", SCRIPTS_DIR / "lit_review.py")


def _write_complete_paper(papers_dir: Path, cite_key: str) -> None:
    """A paper dir that passes the F3 completeness gate (zero lint violations)."""
    d = papers_dir / cite_key
    d.mkdir(parents=True, exist_ok=True)
    (d / "notes.md").write_text(
        "---\ntitle: \"Sample\"\nauthors: \"A. Author\"\nyear: 1980\nvenue: \"V\"\n"
        "doi_url: \"https://example.com\"\n---\n\n# Sample\n\n"
        "## One-Sentence Summary\nBody.\n\n## Collection Cross-References\n- (none found)\n",
        encoding="utf-8",
    )
    (d / "description.md").write_text("---\ntags: [prosody]\n---\nShort.\n", encoding="utf-8")
    (d / "abstract.md").write_text(
        "## Original Text (Verbatim)\na\n\n## Our Interpretation\nb\n", encoding="utf-8"
    )
    (d / "citations.md").write_text("x", encoding="utf-8")
    (d / "paper.pdf").write_text("x", encoding="utf-8")
    (d / "metadata.json").write_text(
        json.dumps({"cite_key": cite_key, "title": "Sample"}, indent=2) + "\n", encoding="utf-8"
    )


def _run_gate(folder: Path, papers_dir: Path) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = LIT.main(["gate", str(folder), "--papers-dir", str(papers_dir)])
    return rc, buf.getvalue()


class PresenceGateTests(unittest.TestCase):
    def test_missing_from_papers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            papers = root / "papers"
            papers.mkdir()
            folder = root / "deliverable"
            folder.mkdir()
            (folder / "draft.md").write_text(
                "Prior work shows a clear effect [@foo2020].\n", encoding="utf-8"
            )
            (folder / "citations.bibtex").write_text(
                "@article{foo2020,\n  title={X},\n}\n", encoding="utf-8"
            )
            rc, out = _run_gate(folder, papers)
            self.assertEqual(rc, 2)
            self.assertIn("MISSING_FROM_PAPERS", out)
            self.assertIn("foo2020", out)
            self.assertIn("Prior work shows a clear effect", out)

    def test_missing_from_bibtex(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            papers = root / "papers"
            _write_complete_paper(papers, "bar2019")
            folder = root / "deliverable"
            folder.mkdir()
            (folder / "draft.md").write_text("As argued [@bar2019].\n", encoding="utf-8")
            (folder / "citations.bibtex").write_text("", encoding="utf-8")
            rc, out = _run_gate(folder, papers)
            self.assertEqual(rc, 2)
            self.assertIn("MISSING_FROM_BIBTEX", out)
            self.assertIn("bar2019", out)

    def test_clean_draft_exit_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            papers = root / "papers"
            _write_complete_paper(papers, "bar2019")
            folder = root / "deliverable"
            folder.mkdir()
            (folder / "draft.md").write_text("As argued [@bar2019].\n", encoding="utf-8")
            (folder / "citations.bibtex").write_text(
                "@article{bar2019,\n  title={Y},\n}\n", encoding="utf-8"
            )
            rc, out = _run_gate(folder, papers)
            self.assertEqual(rc, 0)

    def test_resolves_but_fails_f3(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            papers = root / "papers"
            _write_complete_paper(papers, "baz2018")
            # Break F3: remove abstract.md so the dir is incomplete.
            (papers / "baz2018" / "abstract.md").unlink()
            folder = root / "deliverable"
            folder.mkdir()
            (folder / "draft.md").write_text("See [@baz2018].\n", encoding="utf-8")
            (folder / "citations.bibtex").write_text(
                "@article{baz2018,\n  title={Z},\n}\n", encoding="utf-8"
            )
            rc, out = _run_gate(folder, papers)
            self.assertEqual(rc, 2)
            self.assertIn("MISSING_FROM_PAPERS", out)
            self.assertIn("baz2018", out)


if __name__ == "__main__":
    unittest.main()
