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

    def test_paper_reader_stays_out_of_propstore_ingestion(self) -> None:
        skill = (PLUGIN_ROOT / "skills" / "paper-reader" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertNotIn("pks source", skill)
        self.assertNotIn("pks init", skill)

    def test_orchestrator_fallbacks_use_uv_run(self) -> None:
        for rel_path in (
            ("skills", "paper-process", "SKILL.md"),
            ("skills", "paper-reader", "SKILL.md"),
            ("skills", "process-new-papers", "SKILL.md"),
            ("skills", "adjudicate", "SKILL.md"),
        ):
            skill = (PLUGIN_ROOT.joinpath(*rel_path)).read_text(encoding="utf-8")
            self.assertNotIn('python "<skill-dir>', skill)

    def test_process_new_papers_stays_a_reader_wrapper(self) -> None:
        skill = (
            PLUGIN_ROOT / "skills" / "process-new-papers" / "SKILL.md"
        ).read_text(encoding="utf-8")

        self.assertIn("paper-reader", skill)
        self.assertNotIn("pks source", skill)

    def test_adjudicate_acquires_missing_inputs_through_paper_process_only(self) -> None:
        skill = (PLUGIN_ROOT / "skills" / "adjudicate" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("paper-process", skill)
        self.assertNotIn("pks source", skill)


if __name__ == "__main__":
    unittest.main()
