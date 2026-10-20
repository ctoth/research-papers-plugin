"""Contract tests for the numeric-fidelity gate across the skill surface.

Fabricated statistics have shipped in this collection: invented effect sizes and
p-values that inverted a paper's conclusions. The defence is layered, and each
layer is load-bearing. These tests pin the layers so a future edit cannot quietly
remove one.

The most important test here is
`test_chunk_worker_template_carries_numeric_fidelity`: chunk workers receive the
template prompt, *not* SKILL.md, so a rule that lives only in SKILL.md reaches
nobody on book-length papers.
"""

import re
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SKILLS = PLUGIN_ROOT / "skills"


def read_skill(name: str) -> str:
    return (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")


def fenced_block_after(text: str, heading: str) -> str:
    """Return the first fenced code block following a heading."""
    start = text.index(heading)
    fence = re.search(r"```[a-z]*\n(.*?)\n```", text[start:], re.DOTALL)
    assert fence is not None, f"no fenced block after {heading!r}"
    return fence.group(1)


class PaperReaderNumericFidelityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.skill = read_skill("paper-reader")

    def test_canonical_section_exists(self) -> None:
        self.assertIn("### Numeric Fidelity (MANDATORY)", self.skill)

    def test_transcription_rule_is_stated(self) -> None:
        self.assertIn(
            "every number you write is a transcription of a number you are looking at",
            " ".join(self.skill.lower().split()),
        )

    def test_fabrication_is_named_as_the_worst_failure(self) -> None:
        self.assertIn("A fabricated number is the worst failure", self.skill)

    def test_forbidden_list_exists(self) -> None:
        self.assertIn("#### Forbidden", self.skill)

    def test_page_image_index_formula_is_given(self) -> None:
        """A verification rule with no way to find the page image is unactionable."""
        self.assertIn("pngs/page-{(N-1):03d}.png", self.skill)

    def test_not_reported_sentinel_is_defined(self) -> None:
        self.assertIn("not reported", self.skill)

    def test_three_checks_are_named(self) -> None:
        for step in ("Step 3.6", "Step 3.7", "Step 6.5"):
            with self.subTest(step=step):
                self.assertIn(step, self.skill)

    def test_verification_pass_is_mandatory(self) -> None:
        self.assertIn("## Step 3.6: Numeric Verification Pass (MANDATORY)", self.skill)

    def test_mechanical_gate_step_invokes_the_script(self) -> None:
        self.assertIn("## Step 3.7: Mechanical Numeric Gate (MANDATORY)", self.skill)
        self.assertIn("check_numeric_provenance.py", self.skill)

    def test_gate_reruns_after_summary_artifacts_exist(self) -> None:
        """3.7 runs before description/abstract exist; 6.5 is what covers them."""
        self.assertIn("## Step 6.5: Re-run the Mechanical Numeric Gate (MANDATORY)", self.skill)
        self.assertLess(
            self.skill.index("## Step 4: Write Description"),
            self.skill.index("## Step 6.5"),
        )

    def test_quality_checklist_gates_numbers(self) -> None:
        checklist = self.skill[self.skill.index("## Quality Checklist") :]
        self.assertIn("Numeric fidelity", checklist)
        self.assertIn("Step 3.6", checklist)
        self.assertIn("not reported", checklist)

    def test_do_not_list_forbids_fabrication(self) -> None:
        tail = self.skill[self.skill.index("Do NOT:") :]
        self.assertIn("did not read off a page image", tail)

    def test_output_block_requires_verification_counts(self) -> None:
        self.assertIn("Numeric verification:", self.skill)

    def test_parameter_table_example_carries_a_page_column(self) -> None:
        table = self.skill[self.skill.index("### Parameter Table Format (MANDATORY)") :]
        self.assertIn("| Name | Symbol | Units | Default | Range | Page | Notes |", table)

    def test_parameter_table_does_not_pressure_invented_values(self) -> None:
        """The old wording demanded a populated cell, which invites a plausible fill."""
        self.assertNotIn("At least one must be populated", self.skill)

    def test_typo_is_fixed(self) -> None:
        self.assertNotIn("tripple", self.skill.lower())


class ChunkWorkerTemplateTests(unittest.TestCase):
    """Chunk workers see the template prompt, never SKILL.md."""

    def setUp(self) -> None:
        skill = read_skill("paper-reader")
        self.template = fenced_block_after(skill, "### Step 2B.4: Write ONE Template Prompt")

    def test_chunk_worker_template_carries_numeric_fidelity(self) -> None:
        self.assertIn("## CRITICAL: Numeric fidelity", self.template)

    def test_template_states_the_transcription_rule(self) -> None:
        self.assertIn("transcription of a number you are looking at right now", self.template)

    def test_template_defines_the_not_reported_sentinel(self) -> None:
        self.assertIn("not reported", self.template)

    def test_template_requires_a_self_verification_pass(self) -> None:
        self.assertIn("numeric verification pass", self.template.lower())

    def test_template_requires_reporting_verification_counts(self) -> None:
        self.assertIn("verified", self.template.lower())

    def test_template_forbids_memory_transcription(self) -> None:
        self.assertIn("from memory", self.template)


class SynthesisTests(unittest.TestCase):
    def setUp(self) -> None:
        skill = read_skill("paper-reader")
        start = skill.index("### Step 2B.7: Synthesize")
        self.section = skill[start : skill.index("## Step 3: Write Notes")]

    def test_synthesis_reverifies_against_page_images(self) -> None:
        self.assertIn("pngs/page-{(N-1):03d}.png", self.section)

    def test_chapter_files_are_not_authoritative_for_numbers(self) -> None:
        flat = " ".join(self.section.split())
        self.assertIn("The chapter files are **not** an authoritative source", flat)

    def test_synthesis_subagent_prompt_must_carry_the_rules(self) -> None:
        self.assertIn("verbatim in its prompt", self.section)


class AbstractAndDescriptionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.skill = read_skill("paper-reader")

    def test_description_forbids_new_numbers(self) -> None:
        section = self.skill[
            self.skill.index("## Step 4: Write Description") : self.skill.index(
                "## Step 5: Write Abstract"
            )
        ]
        self.assertIn("must already appear in `notes.md`", section)

    def test_abstract_subagent_prompt_must_carry_the_rules(self) -> None:
        section = self.skill[
            self.skill.index("## Step 5: Write Abstract") : self.skill.index(
                "## Step 6: Write Citations"
            )
        ]
        self.assertIn("verbatim in the subagent's prompt", section)
        self.assertIn("character-for-character", section)

    def test_metadata_identity_fields_are_transcribed(self) -> None:
        section = self.skill[
            self.skill.index("## Step 3.5: Write metadata.json") : self.skill.index(
                "## Step 3.6"
            )
        ]
        self.assertIn("Never infer it from the directory name", section)


class DownstreamBackstopTests(unittest.TestCase):
    def test_extract_claims_requires_page_image_verification(self) -> None:
        skill = read_skill("extract-claims")
        self.assertIn("Numeric verification is mandatory, not a spot-check", skill)
        self.assertIn("the page image wins", skill)

    def test_verify_citations_grades_numbers_against_page_images(self) -> None:
        skill = read_skill("verify-citations")
        self.assertIn("NUMERIC_MISMATCH", skill)
        self.assertIn("pngs/page-{(N-1):03d}.png", skill)
        self.assertIn("not against `notes.md`", skill)

    def test_lint_paper_runs_the_mechanical_gate(self) -> None:
        skill = read_skill("lint-paper")
        self.assertIn("check_numeric_provenance.py", skill)
        self.assertIn("PAGE_OUT_OF_RANGE", skill)
        self.assertIn("NUMERIC_NOT_IN_NOTES", skill)

    def test_light_flow_mandates_the_gate(self) -> None:
        """--light skips extract-claims, so notes are the last numeric checkpoint."""
        skill = read_skill("paper-process")
        self.assertIn("no claim-layer numeric backstop", skill)
        self.assertIn("lint-paper", skill)

    def test_batch_callers_collect_verification_reports(self) -> None:
        for name in ("process-new-papers", "process-leads"):
            with self.subTest(skill=name):
                self.assertIn("Numeric verification", read_skill(name))


class GateScriptContractTests(unittest.TestCase):
    def test_script_is_installed_next_to_the_other_helpers(self) -> None:
        self.assertTrue((PLUGIN_ROOT / "scripts" / "check_numeric_provenance.py").is_file())

    def test_every_documented_code_exists_in_the_script(self) -> None:
        source = (PLUGIN_ROOT / "scripts" / "check_numeric_provenance.py").read_text(
            encoding="utf-8"
        )
        for code in (
            "NUMERIC_NO_PAGE",
            "PARAM_TABLE_NO_PAGE_COL",
            "PARAM_ROW_NO_PAGE",
            "PAGE_OUT_OF_RANGE",
            "TEMPLATE_PLACEHOLDER",
            "NUMERIC_NOT_IN_NOTES",
        ):
            with self.subTest(code=code):
                self.assertIn(code, source)
                self.assertIn(code, read_skill("paper-reader"))


if __name__ == "__main__":
    unittest.main()
