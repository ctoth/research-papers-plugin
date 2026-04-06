import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "research-papers"


class TestSourceBootstrapSkillContract(unittest.TestCase):
    def test_documents_origin_priority_and_source_bootstrap_commands(self) -> None:
        skill = (PLUGIN_ROOT / "skills" / "source-bootstrap" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("DOI", skill)
        self.assertIn("arXiv", skill)
        self.assertIn("URL", skill)
        self.assertIn("local file path", skill)
        self.assertIn("pks source init", skill)
        self.assertIn("pks source write-notes", skill)
        self.assertIn("pks source write-metadata", skill)


class TestSourcePromoteSkillContract(unittest.TestCase):
    def test_documents_single_purpose_promotion_surface(self) -> None:
        skill = (PLUGIN_ROOT / "skills" / "source-promote" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("pks source promote", skill)
        self.assertNotIn("pks source init", skill)


class TestSyncHelperDeprecation(unittest.TestCase):
    def test_sync_helper_is_marked_deprecated(self) -> None:
        script = (PLUGIN_ROOT / "scripts" / "sync_propstore_source.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("DEPRECATED", script)


if __name__ == "__main__":
    unittest.main()
