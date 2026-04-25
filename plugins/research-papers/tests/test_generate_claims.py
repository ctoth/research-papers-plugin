import importlib.util
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
SCHEMA_PATH = Path(__file__).resolve().parent.parent.parent.parent.parent / "propstore" / "schema" / "generated" / "claim.schema.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# Will fail until generate_claims.py exists — that's the TDD point.
GEN_MODULE = load_module("generate_claims", SCRIPTS_DIR / "generate_claims.py")

# ---------------------------------------------------------------------------
# Inline test data
# ---------------------------------------------------------------------------

SAMPLE_PARAMETER_TABLE = """\
| Name | Symbol | Units | Default | Range |
|------|--------|-------|---------|-------|
| Fundamental frequency | F0 | Hz | 120 | 55-500 |
| Open quotient | Oq | - | 0.5 | 0.3-0.8 |
"""

SAMPLE_TABLE_NO_RANGE = """\
| Name | Symbol | Units | Default |
|------|--------|-------|---------|
| Spectral tilt | Tl | dB | -6 |
"""

SAMPLE_EQUATIONS = """\
Some prose here.

$$
E(t) = E_0 \\cdot e^{\\alpha t} \\cdot \\sin(\\omega_g t)
$$

More prose.

$$
F(x) = a x^2 + b x + c
$$
"""

SAMPLE_TESTABLE_PROPERTIES = """\
## Testable Properties

- F0 perturbation affects perceived naturalness
- Open quotient correlates with voice quality
"""

SAMPLE_NOTES_MD = """\
---
title: "A Glottal Model"
authors: "A. Author"
year: 2000
venue: "Journal of Voice"
---

# A Glottal Model

## One-Sentence Summary
A model of glottal excitation.

## Parameters

| Name | Symbol | Units | Default | Range |
|------|--------|-------|---------|-------|
| Fundamental frequency | F0 | Hz | 120 | 55-500 |
| Open quotient | Oq | - | 0.5 | 0.3-0.8 |
| Spectral tilt | Tl | dB | -6 | - |

## Equations

$$
E(t) = E_0 \\cdot e^{\\alpha t} \\cdot \\sin(\\omega_g t)
$$

## Testable Properties

- F0 perturbation affects perceived naturalness
- Open quotient correlates with voice quality
"""


class TestParseParameterTable(unittest.TestCase):
    """Tests for parse_parameter_table."""

    def test_parse_parameter_table_extracts_rows(self) -> None:
        rows = GEN_MODULE.parse_parameter_table(SAMPLE_PARAMETER_TABLE)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["Name"], "Fundamental frequency")
        self.assertEqual(rows[0]["Symbol"], "F0")
        self.assertEqual(rows[0]["Units"], "Hz")
        self.assertEqual(rows[0]["Default"], "120")
        self.assertEqual(rows[0]["Range"], "55-500")
        self.assertEqual(rows[1]["Name"], "Open quotient")
        self.assertEqual(rows[1]["Symbol"], "Oq")

    def test_parse_parameter_table_handles_missing_columns(self) -> None:
        rows = GEN_MODULE.parse_parameter_table(SAMPLE_TABLE_NO_RANGE)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["Name"], "Spectral tilt")
        self.assertNotIn("Range", rows[0])


class TestParseRange(unittest.TestCase):
    """Tests for parse_range."""

    def test_parse_range_numeric_range(self) -> None:
        result = GEN_MODULE.parse_range("55-110")
        self.assertEqual(result["lower_bound"], 55)
        self.assertEqual(result["upper_bound"], 110)

    def test_parse_range_approximate(self) -> None:
        result = GEN_MODULE.parse_range("~0.5")
        self.assertEqual(result["value"], 0.5)
        self.assertNotIn("lower_bound", result)
        self.assertNotIn("upper_bound", result)

    def test_parse_range_dash_means_no_bounds(self) -> None:
        result = GEN_MODULE.parse_range("-")
        self.assertEqual(result, {})

    def test_parse_range_single_value(self) -> None:
        result = GEN_MODULE.parse_range("440")
        self.assertEqual(result["value"], 440)


class TestParseUncertainty(unittest.TestCase):
    """Tests for parse_uncertainty."""

    def test_parse_uncertainty_sd(self) -> None:
        result = GEN_MODULE.parse_uncertainty("s.d. 0.29")
        self.assertAlmostEqual(result["uncertainty"], 0.29)
        self.assertEqual(result["uncertainty_type"], "sd")

    def test_parse_uncertainty_se(self) -> None:
        result = GEN_MODULE.parse_uncertainty("s.e. 0.05")
        self.assertAlmostEqual(result["uncertainty"], 0.05)
        self.assertEqual(result["uncertainty_type"], "se")


class TestParseEquations(unittest.TestCase):
    """Tests for parse_equations."""

    def test_parse_equations_extracts_dollar_blocks(self) -> None:
        equations = GEN_MODULE.parse_equations(SAMPLE_EQUATIONS)
        self.assertEqual(len(equations), 2)
        self.assertIn("E(t)", equations[0])
        self.assertIn("F(x)", equations[1])


class TestParseTestableProperties(unittest.TestCase):
    """Tests for parse_testable_properties."""

    def test_parse_testable_properties_extracts_bullets(self) -> None:
        props = GEN_MODULE.parse_testable_properties(SAMPLE_TESTABLE_PROPERTIES)
        self.assertEqual(len(props), 2)
        self.assertIn("F0 perturbation", props[0])
        self.assertIn("Open quotient correlates", props[1])


class TestFullPipeline(unittest.TestCase):
    """Integration test for the full generation pipeline."""

    def test_full_pipeline_generates_valid_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            paper_dir = Path(tmpdir) / "Author_2000_GlottalModel"
            paper_dir.mkdir()
            (paper_dir / "notes.md").write_text(SAMPLE_NOTES_MD, encoding="utf-8")

            result = GEN_MODULE.generate_claims(paper_dir)

            self.assertIn("source", result)
            self.assertIn("claims", result)
            self.assertIsInstance(result["claims"], list)
            self.assertGreater(len(result["claims"]), 0)
            self.assertIn("paper", result["source"])

    def test_output_is_explicitly_marked_draft(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            paper_dir = Path(tmpdir) / "Author_2000_GlottalModel"
            paper_dir.mkdir()
            (paper_dir / "notes.md").write_text(SAMPLE_NOTES_MD, encoding="utf-8")

            result = GEN_MODULE.generate_claims(paper_dir)
            self.assertEqual(result.get("stage"), "draft")
            observations = [c for c in result["claims"] if c["type"] == "observation"]
            self.assertTrue(observations)
            self.assertTrue(any(c.get("concepts") == [] for c in observations))


class TestClaimProperties(unittest.TestCase):
    """Property-based tests for generated claims."""

    def _generate(self) -> dict:
        """Helper: generate claims from sample notes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            paper_dir = Path(tmpdir) / "Author_2000_GlottalModel"
            paper_dir.mkdir()
            (paper_dir / "notes.md").write_text(SAMPLE_NOTES_MD, encoding="utf-8")
            return GEN_MODULE.generate_claims(paper_dir)

    def test_all_claim_ids_unique(self) -> None:
        result = self._generate()
        ids = [c["id"] for c in result["claims"]]
        self.assertEqual(len(ids), len(set(ids)), "Duplicate claim IDs found")

    def test_all_claim_ids_match_pattern(self) -> None:
        result = self._generate()
        pattern = re.compile(r"^claim\d+$")
        for claim in result["claims"]:
            self.assertRegex(claim["id"], pattern)

    def test_all_claims_have_provenance(self) -> None:
        result = self._generate()
        for claim in result["claims"]:
            self.assertIn("provenance", claim)
            self.assertIn("paper", claim["provenance"])
            self.assertIn("page", claim["provenance"])

    def test_parameter_table_row_count(self) -> None:
        """For the sample table with 3 data rows, there should be 3 parameter claims."""
        result = self._generate()
        param_claims = [c for c in result["claims"] if c["type"] == "parameter"]
        # SAMPLE_NOTES_MD has 3 parameter rows
        self.assertEqual(len(param_claims), 3)

    def test_parameter_claims_use_output_concept(self) -> None:
        result = self._generate()
        param_claims = [c for c in result["claims"] if c["type"] == "parameter"]
        self.assertTrue(param_claims)
        for claim in param_claims:
            self.assertIn("output_concept", claim)
            self.assertNotIn("concept", claim)


if __name__ == "__main__":
    unittest.main()
