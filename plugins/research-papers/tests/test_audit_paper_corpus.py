import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent / "scripts" / "audit_paper_corpus.py"
)
SPEC = importlib.util.spec_from_file_location("audit_paper_corpus", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class AuditPaperCorpusTests(unittest.TestCase):
    def test_analyze_notes_format_detects_current_template_block(self) -> None:
        notes = """# Example Title

**Authors:** Jane Doe, John Roe
**Year:** 1987
**Venue:** Test Journal
**DOI/URL:** https://example.com

## One-Sentence Summary
Body.
"""
        result = MODULE.analyze_notes_format(notes)
        self.assertEqual(result.family, "title+metadata-block")
        self.assertEqual(
            result.metadata_keys,
            ("Authors", "Year", "Venue", "DOI/URL"),
        )
        self.assertFalse(result.has_frontmatter)

    def test_analyze_description_style_detects_yaml_tags(self) -> None:
        description = """---
tags: [prosody, intonation]
---
Short description.
"""
        style, has_tags = MODULE.analyze_description_style(description)
        self.assertEqual(style, "yaml-frontmatter")
        self.assertTrue(has_tags)

    def test_analyze_notes_format_reads_frontmatter_keys(self) -> None:
        notes = """---
title: "Example Title"
authors: "Jane Doe, John Roe"
year: 1987
venue: "Test Journal"
doi_url: "https://example.com"
---

# Example Title

## One-Sentence Summary
Body.
"""
        result = MODULE.analyze_notes_format(notes)
        self.assertEqual(result.family, "frontmatter+title+metadata-block")
        self.assertEqual(
            result.metadata_keys,
            ("title", "authors", "year", "venue", "doi_url"),
        )
        self.assertTrue(result.has_frontmatter)

    def test_audit_paper_dir_detects_legacy_description_and_missing_crossrefs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            paper_dir = Path(tmpdir) / "Sample_1980_TestPaper"
            paper_dir.mkdir()
            (paper_dir / "notes.md").write_text(
                "# Title\n\n**Author:** A. Author\n**Year:** 1980\n\n## One-Sentence Summary\nX\n",
                encoding="utf-8",
            )
            (paper_dir / "description.md").write_text(
                "Short description.\n\nTags: duration, prosody\n",
                encoding="utf-8",
            )
            audit = MODULE.audit_paper_dir(paper_dir)
            self.assertEqual(audit.description_style, "legacy-tags-line")
            self.assertTrue(audit.has_tags)
            self.assertEqual(audit.crossref_status, "missing-section")
            self.assertEqual(audit.notes_format.metadata_keys, ("Author", "Year"))


if __name__ == "__main__":
    unittest.main()
