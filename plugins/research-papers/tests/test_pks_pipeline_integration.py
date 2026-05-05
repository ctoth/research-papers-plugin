"""Contract tests for the pks-first paper ingestion workflow."""

from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "research-papers"


class TestPksFirstPipelineContract(unittest.TestCase):
    def test_paper_process_routes_through_source_cli_skills(self) -> None:
        skill = (PLUGIN_ROOT / "skills" / "paper-process" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("source-bootstrap", skill)
        self.assertIn("register-concepts", skill)
        self.assertIn("extract-claims", skill)
        self.assertIn("extract-justifications", skill)
        self.assertIn("extract-stances", skill)
        self.assertIn("source-promote", skill)

    def test_source_authoring_skills_use_proposal_cli(self) -> None:
        expected_commands = {
            "register-concepts": "pks source propose-concept",
            "extract-claims": "pks source propose-claim",
            "extract-justifications": "pks source propose-justification",
            "extract-stances": "pks source propose-stance",
        }

        for skill_name, command in expected_commands.items():
            with self.subTest(skill_name=skill_name):
                skill = (PLUGIN_ROOT / "skills" / skill_name / "SKILL.md").read_text(
                    encoding="utf-8"
                )
                self.assertIn(command, skill)
                self.assertNotIn("pks source add-", skill)
                self.assertNotIn("--batch", skill)

    def test_pipeline_no_longer_depends_on_removed_yaml_generators(self) -> None:
        removed_scripts = [
            "generate_claims.py",
            "batch_generate_claims.py",
            "bootstrap_concepts.py",
            "propose_concepts.py",
        ]

        for script in removed_scripts:
            with self.subTest(script=script):
                self.assertFalse((PLUGIN_ROOT / "scripts" / script).exists())


if __name__ == "__main__":
    unittest.main()
