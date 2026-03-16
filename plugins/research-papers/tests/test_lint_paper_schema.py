import importlib.util
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


if __name__ == "__main__":
    unittest.main()
