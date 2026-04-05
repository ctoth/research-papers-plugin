from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "research-papers"


class TestSourceWorkflowContracts(unittest.TestCase):
    def test_register_concepts_does_not_document_removed_propose_flags(self) -> None:
        skill = (PLUGIN_ROOT / "skills" / "register-concepts" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("propose_concepts.py pks-batch", skill)
        self.assertNotIn("--forms-dir", skill)
        self.assertNotIn("--domain", skill)

    def test_extract_claims_does_not_route_through_legacy_knowledge_claims(self) -> None:
        skill = (PLUGIN_ROOT / "skills" / "extract-claims" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertNotIn("knowledge/claims/*.yaml", skill)
        self.assertNotIn("Concept registry (`knowledge/concepts/*.yaml`)", skill)

    def test_sync_helper_has_no_dead_pyyaml_dependency(self) -> None:
        script = (PLUGIN_ROOT / "scripts" / "sync_propstore_source.py").read_text(
            encoding="utf-8"
        )

        self.assertNotIn('dependencies = ["pyyaml>=6.0"]', script)


if __name__ == "__main__":
    unittest.main()
