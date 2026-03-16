import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent / "scripts" / "normalize_notes_schema.py"
)
SPEC = importlib.util.spec_from_file_location("normalize_notes_schema", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class NormalizeNotesSchemaTests(unittest.TestCase):
    def test_rewrites_alias_keys_to_canonical_keys(self) -> None:
        source = """---
title: "Sample"
author: "A. Author"
journal: "Test Journal"
doi: "https://example.com"
---

# Sample

## One-Sentence Summary
Body.
"""
        normalized, changed = MODULE.normalize_notes_text(source, "Sample_1980_TestPaper")
        self.assertTrue(changed)
        self.assertEqual(
            normalized,
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
""",
        )

    def test_preserves_unknown_keys_and_fills_year_from_dirname(self) -> None:
        source = """---
title: "Sample"
weird_field: "x"
---

# Sample
"""
        normalized, changed = MODULE.normalize_notes_text(source, "Sample_1994_TestPaper")
        self.assertTrue(changed)
        self.assertIn('year: 1994', normalized)
        self.assertIn('weird_field: "x"', normalized)

    def test_is_idempotent_when_already_canonical(self) -> None:
        source = """---
title: "Sample"
authors: "A. Author"
year: 1980
venue: "Test Journal"
doi_url: "https://example.com"
---

# Sample

## One-Sentence Summary
Body.
"""
        normalized, changed = MODULE.normalize_notes_text(source, "Sample_1980_TestPaper")
        self.assertFalse(changed)
        self.assertEqual(normalized, source)


if __name__ == "__main__":
    unittest.main()
