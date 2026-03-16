import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent / "scripts" / "migrate_notes_frontmatter.py"
)
SPEC = importlib.util.spec_from_file_location("migrate_notes_frontmatter", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class MigrateNotesFrontmatterTests(unittest.TestCase):
    def test_migrates_title_and_metadata_block_into_frontmatter(self) -> None:
        source = """# Example Paper

**Authors:** Jane Doe, John Roe
**Year:** 1987
**Venue:** Test Journal
**DOI/URL:** https://example.com/paper

## One-Sentence Summary
Summary text.
"""
        migrated, changed = MODULE.migrate_notes_text(source)
        self.assertTrue(changed)
        self.assertEqual(
            migrated,
            """---
title: "Example Paper"
authors: "Jane Doe, John Roe"
year: 1987
venue: "Test Journal"
doi_url: "https://example.com/paper"
---

# Example Paper

## One-Sentence Summary
Summary text.
""",
        )

    def test_title_only_notes_get_title_frontmatter(self) -> None:
        source = """# Example Paper

## One-Sentence Summary
Summary text.
"""
        migrated, changed = MODULE.migrate_notes_text(source)
        self.assertTrue(changed)
        self.assertEqual(
            migrated,
            """---
title: "Example Paper"
---

# Example Paper

## One-Sentence Summary
Summary text.
""",
        )

    def test_existing_frontmatter_is_left_unchanged(self) -> None:
        source = """---
title: "Example Paper"
year: 1987
---

# Example Paper

## One-Sentence Summary
Summary text.
"""
        migrated, changed = MODULE.migrate_notes_text(source)
        self.assertFalse(changed)
        self.assertEqual(migrated, source)


if __name__ == "__main__":
    unittest.main()
