"""Tests for the mechanical numeric-provenance gate.

The gate exists because fabricated statistics are the highest-cost failure in
this pipeline. These tests pin three properties: a number without page
provenance is always reported, a number that first appears in a summary is
always reported, and legitimate structural digits are not.
"""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


MODULE = load_module("check_numeric_provenance", SCRIPTS_DIR / "check_numeric_provenance.py")


def codes(findings) -> set:
    return {f.code for f in findings}


def write_paper(
    root: Path,
    name: str,
    notes: str,
    pages: int = 0,
    description: str | None = None,
    abstract: str | None = None,
) -> Path:
    paper_dir = root / name
    paper_dir.mkdir(parents=True, exist_ok=True)
    (paper_dir / "notes.md").write_text(notes, encoding="utf-8")
    if description is not None:
        (paper_dir / "description.md").write_text(description, encoding="utf-8")
    if abstract is not None:
        (paper_dir / "abstract.md").write_text(abstract, encoding="utf-8")
    if pages:
        pngs = paper_dir / "pngs"
        pngs.mkdir(exist_ok=True)
        for idx in range(pages):
            (pngs / f"page-{idx:03d}.png").write_bytes(b"")
    return paper_dir


class PageCiteFormTests(unittest.TestCase):
    """The collection uses several house page-cite forms. All must be honored."""

    FORMS = (
        "*(p.7)*",
        "*(pp.1-3)*",
        "*(p.1, p.3)*",
        "*(pp.2-3, p.5)*",
        "*(pp.991, 993, 996-997)*",
        "*(pp.3-4, 9)*",
        "*(pp.2, 4)*",
    )

    def test_all_house_forms_register_as_citations(self) -> None:
        for form in self.FORMS:
            with self.subTest(form=form):
                self.assertTrue(MODULE.has_page_cite(f"Effect was 0.88 {form}"))

    def test_page_numbers_inside_citations_are_not_data(self) -> None:
        for form in self.FORMS:
            with self.subTest(form=form):
                self.assertEqual(MODULE.significant_numbers(f"A finding {form}"), [])

    def test_multi_page_cite_yields_every_page(self) -> None:
        self.assertEqual(
            MODULE.cited_pages("x *(pp.991, 993, 996-997)*"), [991, 993, 996, 997]
        )


class SignificantNumberTests(unittest.TestCase):
    def test_bare_years_are_not_data(self) -> None:
        self.assertEqual(MODULE.significant_numbers("Replicates Smith 2019 findings"), [])

    def test_sample_size_beats_the_year_heuristic(self) -> None:
        self.assertIn("2019", MODULE.significant_numbers("Enrolled N = 2019 patients"))

    def test_urls_and_dois_contribute_no_data(self) -> None:
        self.assertEqual(
            MODULE.significant_numbers("See https://doi.org/10.1056/NEJMoa2034577"), []
        )

    def test_decimals_are_always_data(self) -> None:
        self.assertIn("0.88", MODULE.significant_numbers("Hazard ratio was 0.88"))

    def test_list_markers_are_not_data(self) -> None:
        self.assertEqual(MODULE.significant_numbers("3. Randomize participants"), [])

    def test_thousands_separators_normalize(self) -> None:
        self.assertIn("1220", MODULE.significant_numbers("Retrieved 1,220 records"))


class NumericNoPageTests(unittest.TestCase):
    def test_unsourced_p_value_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paper = write_paper(
                Path(tmp),
                "Doe_2024_Trial",
                "# Trial\n\n## Results Summary\nMortality fell 34% (p = 0.003).\n",
            )
            self.assertIn("NUMERIC_NO_PAGE", codes(MODULE.check_paper(paper)))

    def test_sourced_p_value_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paper = write_paper(
                Path(tmp),
                "Doe_2024_Trial",
                "# Trial\n\n## Results Summary\nMortality fell 34% (p = 0.003) *(p.7)*\n",
            )
            self.assertEqual(MODULE.check_paper(paper), [])

    def test_not_reported_sentinel_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paper = write_paper(
                Path(tmp),
                "Doe_2024_Trial",
                "# Trial\n\n## Results Summary\nSubgroup effect at 12 months: not reported\n",
            )
            self.assertEqual(MODULE.check_paper(paper), [])

    def test_equation_constants_need_a_nearby_page_cite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paper = write_paper(
                Path(tmp),
                "Doe_2024_Trial",
                "# Trial\n\n## Key Equations\n\n$$\ny = 0.42x + 1.7\n$$\nWhere: x is dose\n",
            )
            self.assertIn("NUMERIC_NO_PAGE", codes(MODULE.check_paper(paper)))

    def test_equation_with_page_cite_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paper = write_paper(
                Path(tmp),
                "Doe_2024_Trial",
                "# Trial\n\n## Key Equations\n\n$$\ny = 0.42x + 1.7\n$$\nWhere: x is dose\n*(p.9)*\n",
            )
            self.assertEqual(MODULE.check_paper(paper), [])

    def test_reference_sections_are_exempt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paper = write_paper(
                Path(tmp),
                "Doe_2024_Trial",
                "# Trial\n\n## Reference List\nSmith J. Lancet. 2019;393:1958-1972.\n",
            )
            self.assertEqual(MODULE.check_paper(paper), [])

    def test_fenced_code_is_exempt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paper = write_paper(
                Path(tmp),
                "Doe_2024_Trial",
                "# Trial\n\n## Methods\n\n```python\nlr = 0.001\n```\n",
            )
            self.assertEqual(MODULE.check_paper(paper), [])


class TableProvenanceTests(unittest.TestCase):
    NOTES_HEAD = "# Trial\n\n## Parameters\n\n"

    def test_row_with_empty_page_cell_is_flagged(self) -> None:
        table = (
            "| Name | Value | Page |\n"
            "|------|-------|------|\n"
            "| Hazard ratio | 0.88 |  |\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            paper = write_paper(Path(tmp), "Doe_2024_Trial", self.NOTES_HEAD + table)
            self.assertIn("PARAM_ROW_NO_PAGE", codes(MODULE.check_paper(paper)))

    def test_row_with_page_cell_passes(self) -> None:
        table = (
            "| Name | Value | Page |\n"
            "|------|-------|------|\n"
            "| Hazard ratio | 0.88 | 7 |\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            paper = write_paper(Path(tmp), "Doe_2024_Trial", self.NOTES_HEAD + table)
            self.assertEqual(MODULE.check_paper(paper), [])

    def test_quantitative_table_without_page_column_is_flagged(self) -> None:
        table = "| Name | Value |\n|------|-------|\n| Hazard ratio | 0.88 |\n"
        with tempfile.TemporaryDirectory() as tmp:
            paper = write_paper(Path(tmp), "Doe_2024_Trial", self.NOTES_HEAD + table)
            self.assertIn("PARAM_TABLE_NO_PAGE_COL", codes(MODULE.check_paper(paper)))

    def test_checklist_table_is_not_treated_as_quantitative(self) -> None:
        """Reporting-guideline checklists carry item numbers, not measurements."""
        table = (
            "| Item | Requirement |\n"
            "| --- | --- |\n"
            "| 1a | Indicate the study design in the title. |\n"
            "| 17b | Report absolute and relative effect sizes. |\n"
        )
        notes = "# Guideline\n\n## Checklist\n\n" + table
        with tempfile.TemporaryDirectory() as tmp:
            paper = write_paper(Path(tmp), "Doe_2024_Guideline", notes)
            self.assertEqual(MODULE.check_paper(paper), [])

    def test_non_numeric_row_needs_no_page(self) -> None:
        table = (
            "| Name | Value | Page |\n"
            "|------|-------|------|\n"
            "| Primary endpoint | all-cause mortality |  |\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            paper = write_paper(Path(tmp), "Doe_2024_Trial", self.NOTES_HEAD + table)
            self.assertEqual(MODULE.check_paper(paper), [])


class PageRangeTests(unittest.TestCase):
    def test_citation_beyond_page_count_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paper = write_paper(
                Path(tmp),
                "Doe_2024_Trial",
                "# Trial\n\n## Results Summary\nEffect 0.88 *(p.47)*\n",
                pages=12,
            )
            self.assertIn("PAGE_OUT_OF_RANGE", codes(MODULE.check_paper(paper)))

    def test_citation_within_page_count_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paper = write_paper(
                Path(tmp),
                "Doe_2024_Trial",
                "# Trial\n\n## Results Summary\nEffect 0.88 *(p.7)*\n",
                pages=12,
            )
            self.assertEqual(MODULE.check_paper(paper), [])

    def test_no_page_images_disables_the_range_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paper = write_paper(
                Path(tmp),
                "Doe_2024_Trial",
                "# Trial\n\n## Results Summary\nEffect 0.88 *(p.47)*\n",
            )
            self.assertEqual(MODULE.check_paper(paper), [])


class SummaryCrossCheckTests(unittest.TestCase):
    """The reported failure: numbers invented at the summary layer."""

    NOTES = "# Trial\n\n## Results Summary\nMortality fell to 0.88 across 52 sites *(p.7)*\n"

    def test_description_number_absent_from_notes_is_flagged(self) -> None:
        description = "---\ntags:\n  - trials\n---\nReports a hazard ratio of 0.42 across 52 sites.\n"
        with tempfile.TemporaryDirectory() as tmp:
            paper = write_paper(
                Path(tmp), "Doe_2024_Trial", self.NOTES, description=description
            )
            findings = MODULE.check_paper(paper)
            self.assertIn("NUMERIC_NOT_IN_NOTES", codes(findings))
            self.assertTrue(any("0.42" in f.detail for f in findings))

    def test_description_numbers_present_in_notes_pass(self) -> None:
        description = "---\ntags:\n  - trials\n---\nReports a hazard ratio of 0.88 across 52 sites.\n"
        with tempfile.TemporaryDirectory() as tmp:
            paper = write_paper(
                Path(tmp), "Doe_2024_Trial", self.NOTES, description=description
            )
            self.assertEqual(MODULE.check_paper(paper), [])

    def test_verbatim_abstract_section_is_exempt(self) -> None:
        abstract = (
            "# Abstract\n\n## Original Text (Verbatim)\n\n"
            "We enrolled 4,312 patients and observed p = 0.031.\n\n"
            "---\n\n## Our Interpretation\n\nEffect held at 0.88.\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            paper = write_paper(Path(tmp), "Doe_2024_Trial", self.NOTES, abstract=abstract)
            self.assertEqual(MODULE.check_paper(paper), [])

    def test_interpretation_number_absent_from_notes_is_flagged(self) -> None:
        abstract = (
            "# Abstract\n\n## Original Text (Verbatim)\n\nSome text.\n\n"
            "## Our Interpretation\n\nThe effect was 0.13, a large reduction.\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            paper = write_paper(Path(tmp), "Doe_2024_Trial", self.NOTES, abstract=abstract)
            self.assertIn("NUMERIC_NOT_IN_NOTES", codes(MODULE.check_paper(paper)))

    def test_chapter_numbers_count_as_sourced_for_books(self) -> None:
        description = "---\ntags:\n  - books\n---\nThe threshold is 0.35 of maximum.\n"
        with tempfile.TemporaryDirectory() as tmp:
            paper = write_paper(
                Path(tmp), "Doe_2024_Book", "# Book\n", description=description
            )
            chapters = paper / "chapters"
            chapters.mkdir()
            (chapters / "chapter-01-intro.md").write_text(
                "# Chapter 1\n\n## Parameters\nThreshold is 0.35 of the maximum *(p.44)*\n",
                encoding="utf-8",
            )
            self.assertEqual(MODULE.check_paper(paper), [])


class PlaceholderTests(unittest.TestCase):
    def test_unfilled_page_token_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paper = write_paper(
                Path(tmp),
                "Doe_2024_Trial",
                "# Trial\n\n## Limitations\nSmall sample *(p.N)*\n",
            )
            self.assertIn("TEMPLATE_PLACEHOLDER", codes(MODULE.check_paper(paper)))

    def test_unfilled_year_token_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paper = write_paper(
                Path(tmp),
                "Doe_2024_Trial",
                "# Trial\n\n## Methodology\nPublished [Year] in a journal.\n",
            )
            self.assertIn("TEMPLATE_PLACEHOLDER", codes(MODULE.check_paper(paper)))


class ChapterFileTests(unittest.TestCase):
    def test_chapter_files_are_checked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paper = write_paper(Path(tmp), "Doe_2024_Book", "# Book\n")
            chapters = paper / "chapters"
            chapters.mkdir()
            (chapters / "chapter-01-intro.md").write_text(
                "# Chapter 1\n\n## Parameters\nThreshold is 0.35 of the maximum.\n",
                encoding="utf-8",
            )
            findings = MODULE.check_paper(paper)
            self.assertIn("NUMERIC_NO_PAGE", codes(findings))
            self.assertTrue(any(f.file == "chapter-01-intro.md" for f in findings))


class CliTests(unittest.TestCase):
    def test_exit_code_signals_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paper = write_paper(
                Path(tmp),
                "Doe_2024_Trial",
                "# Trial\n\n## Results Summary\nEffect 0.88 with no source.\n",
            )
            self.assertEqual(MODULE.main(["check", str(paper)]), 1)

    def test_exit_code_zero_when_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paper = write_paper(
                Path(tmp),
                "Doe_2024_Trial",
                "# Trial\n\n## Results Summary\nEffect 0.88 *(p.3)*\n",
            )
            self.assertEqual(MODULE.main(["check", str(paper)]), 0)

    def test_all_mode_walks_the_collection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_paper(root, "A_2024_One", "# One\n\n## Results\nRate 0.5 unsourced\n")
            write_paper(root, "B_2024_Two", "# Two\n\n## Results\nRate 0.5 *(p.2)*\n")
            self.assertEqual(MODULE.main(["check", "--all", "--papers-dir", str(root)]), 1)


if __name__ == "__main__":
    unittest.main()
