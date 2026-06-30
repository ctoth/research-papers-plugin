import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PLUGIN_ROOT / "scripts"
SKILL_MD = PLUGIN_ROOT / "skills" / "create-lit-review" / "SKILL.md"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


LIT = load_module("lit_review", SCRIPTS_DIR / "lit_review.py")


class SkillContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(SKILL_MD.exists(), "create-lit-review SKILL.md missing")
        self.text = SKILL_MD.read_text(encoding="utf-8")

    def test_drives_the_goal_loop(self) -> None:
        self.assertIn("/goal", self.text)

    def test_documents_both_modes(self) -> None:
        self.assertIn("--mode full", self.text)
        self.assertIn("--mode intro", self.text)

    def test_lists_ordered_pipeline_stages(self) -> None:
        for stage in ("research", "paper-retriever", "process-new-papers",
                      "write-lit-review", "verify-citations"):
            self.assertIn(stage, self.text)

    def test_documents_wanted_papers_exclusion(self) -> None:
        self.assertIn("wanted-papers.md", self.text)
        self.assertIn("exclude", self.text.lower())

    def test_references_all_four_gates(self) -> None:
        # F4 (dir==cite_key) + F3 (completeness) + F2 (presence) + F7 (reality).
        for gate in ("lint_paper_schema.py", "lit_review.py gate", "verify_citations_real.py"):
            self.assertIn(gate, self.text)


class LoopCompletionConditionTest(unittest.TestCase):
    """A cited-but-unretrievable key keeps the F2 gate blocking, so the /goal loop
    cannot declare 'done' — the behavior the orchestrator relies on."""

    def test_unretrievable_citation_blocks_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            papers = root / "papers"
            papers.mkdir()
            folder = root / "deliverable"
            folder.mkdir()
            (folder / "draft.md").write_text("Claim [@unretrievable2030].\n", encoding="utf-8")
            (folder / "citations.bibtex").write_text(
                "@article{unretrievable2030,\n}\n", encoding="utf-8")
            rc = LIT.main(["gate", str(folder), "--papers-dir", str(papers)])
            self.assertEqual(rc, 2)  # loop must keep iterating, not finish


if __name__ == "__main__":
    unittest.main()
