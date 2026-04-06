from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "research-papers"


class TestSourceWorkflowContracts(unittest.TestCase):
    def test_source_bootstrap_skill_exists_for_propstore_init_writes(self) -> None:
        skill = (PLUGIN_ROOT / "skills" / "source-bootstrap" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("pks source init", skill)
        self.assertIn("pks source write-notes", skill)
        self.assertIn("pks source write-metadata", skill)

    def test_source_promote_skill_exists_for_final_promotion(self) -> None:
        skill = (PLUGIN_ROOT / "skills" / "source-promote" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("pks source promote", skill)

    def test_register_concepts_does_not_document_removed_propose_flags(self) -> None:
        skill = (PLUGIN_ROOT / "skills" / "register-concepts" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("notes.md", skill)
        self.assertIn("propose_concepts.py pks-batch", skill)
        self.assertNotIn("If `claims.yaml` is missing → STOP", skill)
        self.assertNotIn("This must run after extract-claims", skill)
        self.assertNotIn("Run the concept proposer to extract all concept names from this paper's claims.yaml", skill)
        self.assertNotIn("--forms-dir", skill)
        self.assertNotIn("--domain", skill)

    def test_extract_claims_does_not_route_through_legacy_knowledge_claims(self) -> None:
        skill = (PLUGIN_ROOT / "skills" / "extract-claims" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("pngs/page-", skill)
        self.assertIn("spot-check", skill)
        self.assertIn("unknown concept", skill)
        self.assertNotIn("knowledge/claims/*.yaml", skill)
        self.assertNotIn("Concept registry (`knowledge/concepts/*.yaml`)", skill)
        self.assertNotIn(
            "report and ask whether to overwrite or use enrich-claims instead",
            skill,
        )

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

    def test_paper_process_is_a_pure_skill_orchestrator(self) -> None:
        skill = (PLUGIN_ROOT / "skills" / "paper-process" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        for required in (
            "paper-retriever",
            "paper-reader",
            "source-bootstrap",
            "register-concepts",
            "extract-claims",
            "extract-justifications",
            "extract-stances",
            "source-promote",
        ):
            self.assertIn(required, skill)

        self.assertNotIn("pks source init", skill)
        self.assertNotIn("pks source write-notes", skill)
        self.assertNotIn("pks source write-metadata", skill)
        self.assertNotIn("pks source finalize", skill)
        self.assertNotIn("pks source promote", skill)

    def test_orchestrator_fallbacks_use_uv_run(self) -> None:
        for rel_path in (
            ("skills", "paper-process", "SKILL.md"),
            ("skills", "paper-reader", "SKILL.md"),
            ("skills", "process-new-papers", "SKILL.md"),
            ("skills", "process-leads", "SKILL.md"),
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

    def test_enrich_claims_does_not_require_legacy_registry_mutation(self) -> None:
        skill = (PLUGIN_ROOT / "skills" / "enrich-claims" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertNotIn("knowledge/concepts/*.yaml", skill)
        self.assertNotIn("pks concept add-value", skill)
        self.assertNotIn('python3 scripts/generate_claims.py', skill)

    def test_reconcile_vocabulary_operates_on_concept_inventories(self) -> None:
        skill = (
            PLUGIN_ROOT / "skills" / "reconcile-vocabulary" / "SKILL.md"
        ).read_text(encoding="utf-8")

        self.assertIn("concepts.yaml", skill)
        self.assertNotIn("rewrite all claims.yaml files", skill)

    def test_reconcile_stays_notes_layer_only(self) -> None:
        skill = (PLUGIN_ROOT / "skills" / "reconcile" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertNotIn("pks source", skill)


if __name__ == "__main__":
    unittest.main()
