import importlib.util
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


AUDIT_MODULE = load_module("audit_paper_corpus", SCRIPTS_DIR / "audit_paper_corpus.py")
MANIFEST_MODULE = load_module("paper_db_manifest", SCRIPTS_DIR / "paper_db_manifest.py")
LINT_MODULE = load_module("lint_paper_schema", SCRIPTS_DIR / "lint_paper_schema.py")


class LintPaperSchemaTests(unittest.TestCase):
    def test_lint_paper_reports_aliases_unknown_fields_and_missing_tags(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paper_dir = root / "Sample_1980_TestPaper"
            paper_dir.mkdir()
            (paper_dir / "notes.md").write_text(
                """---
title: "Sample"
author: "A. Author"
year: 1980
journal: "Test Journal"
weird_field: "x"
---

# Sample

## One-Sentence Summary
Body.
""",
                encoding="utf-8",
            )
            (paper_dir / "description.md").write_text("Plain description.\n", encoding="utf-8")
            audit = AUDIT_MODULE.audit_paper_dir(paper_dir)
            violations = LINT_MODULE.lint_paper(audit, root)
            pairs = {(v.code, v.detail) for v in violations}
            self.assertIn(("NOTES_FIELD_ALIAS", "author->authors"), pairs)
            self.assertIn(("NOTES_FIELD_ALIAS", "journal->venue"), pairs)
            self.assertIn(("NOTES_UNKNOWN_FIELD", "weird_field"), pairs)
            self.assertIn(("DESCRIPTION_TAGS_MISSING", "plain-body"), pairs)
            self.assertIn(("ABSTRACT_MISSING", ""), pairs)
            self.assertIn(("CITATIONS_MISSING", ""), pairs)
            self.assertIn(("SOURCE_MISSING", ""), pairs)
            self.assertIn(("CROSSREFS_MISSING", ""), pairs)

    def test_lint_paper_accepts_canonical_minimal_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paper_dir = root / "Sample_1980_TestPaper"
            paper_dir.mkdir()
            (paper_dir / "notes.md").write_text(
                """---
title: "Sample"
authors: "A. Author"
year: 1980
venue: "Test Journal"
doi_url: "https://example.com"
---

# Sample

## One-Sentence Summary
Body.

## Collection Cross-References
- (none found)
""",
                encoding="utf-8",
            )
            (paper_dir / "description.md").write_text(
                """---
tags: [prosody]
---
Short description.
""",
                encoding="utf-8",
            )
            (paper_dir / "abstract.md").write_text("x", encoding="utf-8")
            (paper_dir / "citations.md").write_text("x", encoding="utf-8")
            (paper_dir / "paper.pdf").write_text("x", encoding="utf-8")
            audit = AUDIT_MODULE.audit_paper_dir(paper_dir)
            violations = LINT_MODULE.lint_paper(audit, root)
            self.assertEqual(violations, [])

    def test_linter_reads_manifest_from_project_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            papers_dir = root / "papers"
            papers_dir.mkdir()
            (papers_dir / "db.yaml").write_text(
                """schema_version: 1
database_kind: research-papers
notes_format: notes-frontmatter-v1
description_format: description-frontmatter-tags-v1
required_files: [notes.md, description.md]
recommended_files: [abstract.md, citations.md]
canonical_notes_required: [title, year, venue]
canonical_notes_recommended: [authors]
canonical_notes_optional: []
legacy_aliases:
  author: authors
""",
                encoding="utf-8",
            )
            paper_dir = papers_dir / "Sample_1980_TestPaper"
            paper_dir.mkdir()
            (paper_dir / "notes.md").write_text(
                """---
title: "Sample"
authors: "A. Author"
year: 1980
---

# Sample

## Collection Cross-References
- (none found)
""",
                encoding="utf-8",
            )
            (paper_dir / "description.md").write_text(
                """---
tags: [prosody]
---
Short description.
""",
                encoding="utf-8",
            )
            audit = AUDIT_MODULE.audit_paper_dir(paper_dir)
            violations = LINT_MODULE.lint_paper(audit, papers_dir)
            pairs = {(v.code, v.detail) for v in violations}
            self.assertIn(("NOTES_REQUIRED_MISSING", "venue"), pairs)


class CompletenessGateTests(unittest.TestCase):
    """F3: abstract.md (both sections) and citations.md are required; exit 2."""

    def _minimal_notes_paper(self, paper_dir: Path) -> None:
        paper_dir.mkdir(parents=True, exist_ok=True)
        (paper_dir / "notes.md").write_text(
            "---\ntitle: \"S\"\nauthors: \"A\"\nyear: 1980\nvenue: \"V\"\n"
            "doi_url: \"https://example.com\"\n---\n\n# S\n\n"
            "## One-Sentence Summary\nBody.\n\n## Collection Cross-References\n- (none found)\n",
            encoding="utf-8",
        )
        (paper_dir / "description.md").write_text(
            "---\ntags: [prosody]\n---\nShort.\n", encoding="utf-8"
        )
        (paper_dir / "paper.pdf").write_text("x", encoding="utf-8")

    def test_abstract_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paper_dir = root / "Sample_1980_X"
            self._minimal_notes_paper(paper_dir)
            (paper_dir / "citations.md").write_text("x", encoding="utf-8")
            audit = AUDIT_MODULE.audit_paper_dir(paper_dir)
            codes = {v.code for v in LINT_MODULE.lint_paper(audit, root)}
            self.assertIn("ABSTRACT_MISSING", codes)

    def test_citations_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paper_dir = root / "Sample_1980_X"
            self._minimal_notes_paper(paper_dir)
            (paper_dir / "abstract.md").write_text(
                "## Original Text (Verbatim)\na\n\n## Our Interpretation\nb\n", encoding="utf-8"
            )
            audit = AUDIT_MODULE.audit_paper_dir(paper_dir)
            codes = {v.code for v in LINT_MODULE.lint_paper(audit, root)}
            self.assertIn("CITATIONS_MISSING", codes)

    def test_abstract_missing_interpretation_section(self) -> None:
        # abstract.md has the verbatim section but not "Our Interpretation".
        with tempfile.TemporaryDirectory() as tmp:
            papers = Path(tmp) / "papers"
            paper_dir = papers / "Sample_1980_X"
            self._minimal_notes_paper(paper_dir)
            (paper_dir / "citations.md").write_text("x", encoding="utf-8")
            (paper_dir / "abstract.md").write_text(
                "## Original Text (Verbatim)\nonly the verbatim, no interpretation\n",
                encoding="utf-8",
            )
            (paper_dir / "metadata.json").write_text(
                json.dumps({"cite_key": "Sample_1980_X", "title": "S"}, indent=2) + "\n",
                encoding="utf-8",
            )
            violations = LINT_MODULE.lint_collection(papers)
            codes = {v.code for v in violations}
            self.assertIn("ABSTRACT_SECTIONS", codes)

    def test_main_exits_two_on_incomplete_paper(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            papers = Path(tmp) / "papers"
            paper_dir = papers / "Sample_1980_X"
            self._minimal_notes_paper(paper_dir)  # no abstract.md, no citations.md
            original = LINT_MODULE.PAPERS_DIR
            try:
                LINT_MODULE.PAPERS_DIR = papers
                rc = LINT_MODULE.main()
            finally:
                LINT_MODULE.PAPERS_DIR = original
            self.assertEqual(rc, 2)


class NestedChapterLintTests(unittest.TestCase):
    """F1: nested book/chapters/<dir> paper dirs are discovered and linted."""

    def test_nested_chapter_is_discovered_and_linted_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            papers = Path(tmp) / "papers"
            book = papers / "Geertz_1973_Interpretation"
            _write_complete_paper(book, cite_key="Geertz_1973_Interpretation")
            chapter = book / "chapters" / "Geertz_1973_ThickDescription"
            _write_complete_paper(chapter, cite_key="Geertz_1973_ThickDescription")

            audits = AUDIT_MODULE.collect_audits(papers)
            relpaths = {a.relpath for a in audits}
            self.assertIn("Geertz_1973_Interpretation/chapters/Geertz_1973_ThickDescription", relpaths)

            violations = []
            for audit in audits:
                violations.extend(LINT_MODULE.lint_paper(audit, papers))
            self.assertEqual(violations, [], violations)

    def test_count_mismatch_includes_chapters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            papers = Path(tmp) / "papers"
            book = papers / "Geertz_1973_Interpretation"
            _write_complete_paper(book, cite_key="Geertz_1973_Interpretation")
            chapter = book / "chapters" / "Geertz_1973_ThickDescription"
            _write_complete_paper(chapter, cite_key="Geertz_1973_ThickDescription")
            # index.md lists only the book (1 header), but there are 2 paper dirs.
            (papers / "index.md").write_text(
                "## [Book](Geertz_1973_Interpretation/notes.md)\nd\n\n", encoding="utf-8")
            violations = LINT_MODULE.lint_collection(papers)
            mismatch = [v for v in violations if v.code == "COUNT_MISMATCH"]
            self.assertTrue(mismatch)
            self.assertIn("dirs=2", mismatch[0].detail)


def _write_complete_paper(paper_dir: Path, cite_key: str) -> None:
    """Write a minimal but lint-complete paper dir with the given cite_key."""
    paper_dir.mkdir(parents=True, exist_ok=True)
    (paper_dir / "notes.md").write_text(
        """---
title: "Sample"
authors: "A. Author"
year: 1980
venue: "Test Journal"
doi_url: "https://example.com"
---

# Sample

## One-Sentence Summary
Body.

## Collection Cross-References
- (none found)
""",
        encoding="utf-8",
    )
    (paper_dir / "description.md").write_text(
        "---\ntags: [prosody]\n---\nShort description.\n", encoding="utf-8"
    )
    (paper_dir / "abstract.md").write_text(
        "## Original Text (Verbatim)\nx\n\n## Our Interpretation\ny\n", encoding="utf-8"
    )
    (paper_dir / "citations.md").write_text("x", encoding="utf-8")
    (paper_dir / "paper.pdf").write_text("x", encoding="utf-8")
    (paper_dir / "metadata.json").write_text(
        json.dumps({"cite_key": cite_key, "title": "Sample"}, indent=2) + "\n",
        encoding="utf-8",
    )


class DirKeyMismatchTests(unittest.TestCase):
    def test_dir_key_mismatch_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paper_dir = root / "Foo_2019_Bar"
            _write_complete_paper(paper_dir, cite_key="foo2020bar")
            audit = AUDIT_MODULE.audit_paper_dir(paper_dir)
            violations = LINT_MODULE.lint_paper(audit, root)
            pairs = {(v.code, v.detail) for v in violations}
            self.assertIn(("DIR_KEY_MISMATCH", "cite_key=foo2020bar"), pairs)

    def test_dir_key_match_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paper_dir = root / "foo2020bar"
            _write_complete_paper(paper_dir, cite_key="foo2020bar")
            audit = AUDIT_MODULE.audit_paper_dir(paper_dir)
            violations = LINT_MODULE.lint_paper(audit, root)
            codes = {v.code for v in violations}
            self.assertNotIn("DIR_KEY_MISMATCH", codes)

    def test_year_differs_but_key_matches(self) -> None:
        # Folder year (2019 implied) differs from cite-key year (2020), but the
        # directory is named after the published cite key, so dir == cite_key.
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paper_dir = root / "Author_2020_Title"
            _write_complete_paper(paper_dir, cite_key="Author_2020_Title")
            audit = AUDIT_MODULE.audit_paper_dir(paper_dir)
            violations = LINT_MODULE.lint_paper(audit, root)
            self.assertEqual(violations, [])

    def test_main_exits_two_on_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            papers_dir = root / "papers"
            _write_complete_paper(papers_dir / "Foo_2019_Bar", cite_key="foo2020bar")
            original = LINT_MODULE.PAPERS_DIR
            try:
                LINT_MODULE.PAPERS_DIR = papers_dir
                rc = LINT_MODULE.main()
            finally:
                LINT_MODULE.PAPERS_DIR = original
            self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
