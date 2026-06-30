import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PLUGIN_ROOT / "scripts"
SKILL_DIR = PLUGIN_ROOT / "skills" / "write-lit-review"
GUIDES_DIR = SKILL_DIR / "guides"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


LIT = load_module("lit_review", SCRIPTS_DIR / "lit_review.py")


def _write_complete_paper(papers_dir: Path, cite_key: str) -> None:
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


class VendoredGuidesTests(unittest.TestCase):
    def test_skill_md_exists(self) -> None:
        self.assertTrue((SKILL_DIR / "SKILL.md").exists(), "write-lit-review SKILL.md missing")

    def test_both_guides_vendored_and_nonempty(self) -> None:
        for name in ("writing_full_paper_literature_reviews.md",
                     "writing_intro_paper_literature_reviews.md"):
            guide = GUIDES_DIR / name
            self.assertTrue(guide.exists(), f"vendored guide missing: {name}")
            self.assertGreater(guide.stat().st_size, 1000, f"vendored guide too small: {name}")


class GateHandoffSmokeTest(unittest.TestCase):
    """The skill's mechanical assembly + F2 gate handoff works end to end."""

    def test_build_then_gate_passes_on_resolvable_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            papers = root / "papers"
            _write_complete_paper(papers, "foo2020")
            folder = root / "deliverable"
            folder.mkdir()
            (folder / "draft.md").write_text("Prior work [@foo2020].\n", encoding="utf-8")

            # Assemble citations.bibtex from the draft's cited keys (lit_review build).
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                LIT.main(["build", str(folder)])
            (folder / "citations.bibtex").write_text(buf.getvalue(), encoding="utf-8")

            # The F2 presence gate must now pass: foo2020 is in the bibtex and
            # resolves to a complete paper dir.
            rc = LIT.main(["gate", str(folder), "--papers-dir", str(papers)])
            self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
