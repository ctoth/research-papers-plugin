import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PROPOSE_MODULE = load_module("propose_concepts", SCRIPTS_DIR / "propose_concepts.py")

# ---------------------------------------------------------------------------
# Inline test data
# ---------------------------------------------------------------------------

SAMPLE_CLAIMS_YAML = """\
source:
  paper: Bowman_2018_EffectsAspirinPrimaryPrevention
claims:
  - id: claim1
    type: parameter
    output_concept: rate_ratio
    value: 0.88
    unit: "dimensionless"
  - id: claim2
    type: parameter
    output_concept: event_rate
    value: 8.5
    unit: "%"
  - id: claim3
    type: measurement
    target_concept: blood_pressure
    measure: systolic
    value: 140
    unit: "mmHg"
  - id: claim4
    type: observation
    concepts:
      - aspirin_adherence
      - treatment_compliance
    statement: "Adherence was high in both groups."
"""

SAMPLE_CLAIMS_YAML_2 = """\
source:
  paper: McNeil_2018_EffectAspirinMortality
claims:
  - id: claim1
    type: parameter
    output_concept: hazard_ratio
    value: 1.14
    unit: "dimensionless"
  - id: claim2
    type: parameter
    output_concept: event_rate
    value: 12.7
    unit: "%"
"""

SAMPLE_CLAIMS_YAML_EQUATION = """\
source:
  paper: Model_2020_EquationExample
claims:
  - id: claim1
    type: equation
    expression: "HR = exp(beta * X)"
    sympy: "Eq(HR, exp(beta * X))"
    variables:
      - symbol: HR
        concept: hazard_ratio
        role: dependent
      - symbol: beta
        concept: log_hazard_coefficient
        role: parameter
      - symbol: X
        concept: covariate_value
        role: independent
  - id: claim2
    type: model
    name: "Cox proportional hazards"
    parameters:
      - name: baseline_hazard
        concept: baseline_hazard_rate
      - name: treatment_effect
        concept: treatment_hazard_ratio
"""


def _make_papers_dir(root: Path) -> Path:
    """Create a directory with sample claims.yaml files."""
    paper1 = root / "Bowman_2018_EffectsAspirinPrimaryPrevention"
    paper1.mkdir(parents=True, exist_ok=True)
    (paper1 / "claims.yaml").write_text(SAMPLE_CLAIMS_YAML, encoding="utf-8")

    paper2 = root / "McNeil_2018_EffectAspirinMortality"
    paper2.mkdir(parents=True, exist_ok=True)
    (paper2 / "claims.yaml").write_text(SAMPLE_CLAIMS_YAML_2, encoding="utf-8")

    return root


class TestIsJunkName(unittest.TestCase):
    """Tests for is_junk_name."""

    def test_pure_numbers_are_junk(self) -> None:
        self.assertTrue(PROPOSE_MODULE.is_junk_name("123"))
        self.assertTrue(PROPOSE_MODULE.is_junk_name("4.5"))

    def test_single_char_is_junk(self) -> None:
        self.assertTrue(PROPOSE_MODULE.is_junk_name("x"))

    def test_normal_names_pass(self) -> None:
        self.assertFalse(PROPOSE_MODULE.is_junk_name("hazard_ratio"))
        self.assertFalse(PROPOSE_MODULE.is_junk_name("event_rate"))


class TestExtractConcepts(unittest.TestCase):
    """Tests for extract_concepts."""

    def test_extracts_concept_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            papers = _make_papers_dir(Path(tmpdir))
            concepts = PROPOSE_MODULE.extract_concepts(papers)
            self.assertIn("rate_ratio", concepts)
            self.assertIn("event_rate", concepts)
            self.assertIn("hazard_ratio", concepts)

    def test_extracts_target_concept_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            papers = _make_papers_dir(Path(tmpdir))
            concepts = PROPOSE_MODULE.extract_concepts(papers)
            self.assertIn("blood_pressure", concepts)

    def test_extracts_concepts_list_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            papers = _make_papers_dir(Path(tmpdir))
            concepts = PROPOSE_MODULE.extract_concepts(papers)
            self.assertIn("aspirin_adherence", concepts)
            self.assertIn("treatment_compliance", concepts)

    def test_counts_cross_paper_occurrences(self) -> None:
        """event_rate appears in both papers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            papers = _make_papers_dir(Path(tmpdir))
            concepts = PROPOSE_MODULE.extract_concepts(papers)
            self.assertEqual(concepts["event_rate"]["count"], 2)
            self.assertEqual(len(concepts["event_rate"]["papers"]), 2)

    def test_extracts_variables_concept_field(self) -> None:
        """Equation claims: variables[].concept should be extracted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            paper_dir = Path(tmpdir) / "Model_2020_EquationExample"
            paper_dir.mkdir()
            (paper_dir / "claims.yaml").write_text(
                SAMPLE_CLAIMS_YAML_EQUATION, encoding="utf-8"
            )
            concepts = PROPOSE_MODULE.extract_concepts(Path(tmpdir))
            self.assertIn("hazard_ratio", concepts)
            self.assertIn("log_hazard_coefficient", concepts)
            self.assertIn("covariate_value", concepts)

    def test_extracts_parameters_concept_field(self) -> None:
        """Model claims: parameters[].concept should be extracted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            paper_dir = Path(tmpdir) / "Model_2020_EquationExample"
            paper_dir.mkdir()
            (paper_dir / "claims.yaml").write_text(
                SAMPLE_CLAIMS_YAML_EQUATION, encoding="utf-8"
            )
            concepts = PROPOSE_MODULE.extract_concepts(Path(tmpdir))
            self.assertIn("baseline_hazard_rate", concepts)
            self.assertIn("treatment_hazard_ratio", concepts)

    def test_extracts_legacy_parameter_concept_field(self) -> None:
        import yaml

        with tempfile.TemporaryDirectory() as tmpdir:
            paper_dir = Path(tmpdir) / "LegacyPaper"
            paper_dir.mkdir()
            claims = {
                "source": {"paper": "LegacyPaper"},
                "claims": [
                    {"id": "claim1", "type": "parameter", "concept": "legacy_parameter_name", "value": 1.0}
                ],
            }
            (paper_dir / "claims.yaml").write_text(
                yaml.dump(claims, default_flow_style=False),
                encoding="utf-8",
            )

            concepts = PROPOSE_MODULE.extract_concepts(Path(tmpdir))
            self.assertIn("legacy_parameter_name", concepts)

    def test_collects_units(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            papers = _make_papers_dir(Path(tmpdir))
            concepts = PROPOSE_MODULE.extract_concepts(papers)
            self.assertIn("%", concepts["event_rate"]["units"])


class TestPksBatchMode(unittest.TestCase):
    """Tests for the pks-batch output mode."""

    def test_pks_batch_single_paper(self) -> None:
        """Produces concepts.yaml in pks batch format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            paper_dir = Path(tmpdir) / "Bowman_2018_EffectsAspirinPrimaryPrevention"
            paper_dir.mkdir()
            (paper_dir / "claims.yaml").write_text(
                SAMPLE_CLAIMS_YAML, encoding="utf-8"
            )

            result = PROPOSE_MODULE.propose_pks_batch(
                paper_dir=paper_dir,
            )

            self.assertIsInstance(result, dict)
            self.assertIn("concepts", result)
            self.assertIsInstance(result["concepts"], list)
            for concept in result["concepts"]:
                self.assertIn("local_name", concept)
                self.assertIn("definition", concept)
                self.assertIn("form", concept)

    def test_pks_batch_concept_names_from_claims(self) -> None:
        """Concepts match what's referenced in claims.yaml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            paper_dir = Path(tmpdir) / "Bowman_2018"
            paper_dir.mkdir()
            (paper_dir / "claims.yaml").write_text(
                SAMPLE_CLAIMS_YAML, encoding="utf-8"
            )

            result = PROPOSE_MODULE.propose_pks_batch(
                paper_dir=paper_dir,
            )

            names = {c["local_name"] for c in result["concepts"]}
            self.assertIn("rate_ratio", names)
            self.assertIn("event_rate", names)
            self.assertIn("blood_pressure", names)

    def test_pks_batch_reuses_existing_registry(self) -> None:
        """When registry has a concept, in_registry is True."""
        import yaml

        with tempfile.TemporaryDirectory() as tmpdir:
            paper_dir = Path(tmpdir) / "Bowman_2018"
            paper_dir.mkdir()
            (paper_dir / "claims.yaml").write_text(
                SAMPLE_CLAIMS_YAML, encoding="utf-8"
            )

            registry_dir = Path(tmpdir) / "registry"
            registry_dir.mkdir()
            existing = {
                "id": "concept42",
                "canonical_name": "rate_ratio",
                "status": "accepted",
                "definition": "The canonical rate ratio.",
                "domain": "cvd",
                "form": "ratio",
            }
            (registry_dir / "rate_ratio.yaml").write_text(
                yaml.dump(existing, default_flow_style=False),
                encoding="utf-8",
            )

            result = PROPOSE_MODULE.propose_pks_batch(
                paper_dir=paper_dir,
                registry_dir=registry_dir,
            )

            rr = next(
                c for c in result["concepts"] if c["local_name"] == "rate_ratio"
            )
            self.assertTrue(rr["in_registry"])

    def test_pks_batch_writes_file(self) -> None:
        """When output_path given, writes concepts.yaml to disk."""
        import yaml

        with tempfile.TemporaryDirectory() as tmpdir:
            paper_dir = Path(tmpdir) / "Bowman_2018"
            paper_dir.mkdir()
            (paper_dir / "claims.yaml").write_text(
                SAMPLE_CLAIMS_YAML, encoding="utf-8"
            )

            output_path = paper_dir / "concepts.yaml"
            PROPOSE_MODULE.propose_pks_batch(
                paper_dir=paper_dir,
                output_path=output_path,
            )

            self.assertTrue(output_path.exists())
            data = yaml.safe_load(output_path.read_text(encoding="utf-8"))
            self.assertIn("concepts", data)

    def test_pks_batch_includes_observed_units(self) -> None:
        """Each concept entry includes the units observed in claims."""
        with tempfile.TemporaryDirectory() as tmpdir:
            paper_dir = Path(tmpdir) / "Bowman_2018"
            paper_dir.mkdir()
            (paper_dir / "claims.yaml").write_text(
                SAMPLE_CLAIMS_YAML, encoding="utf-8"
            )

            result = PROPOSE_MODULE.propose_pks_batch(paper_dir=paper_dir)

            er = next(c for c in result["concepts"] if c["local_name"] == "event_rate")
            self.assertIn("units_observed", er)
            self.assertIn("%", er["units_observed"])

    def test_pks_batch_filters_junk(self) -> None:
        """Junk names are not included in output."""
        import yaml

        with tempfile.TemporaryDirectory() as tmpdir:
            paper_dir = Path(tmpdir) / "TestPaper"
            paper_dir.mkdir()
            claims = {
                "source": {"paper": "TestPaper"},
                "claims": [
                    {"id": "c1", "type": "parameter", "output_concept": "x", "value": 1},
                    {"id": "c2", "type": "parameter", "output_concept": "real_concept", "value": 2},
                ],
            }
            (paper_dir / "claims.yaml").write_text(
                yaml.dump(claims, default_flow_style=False), encoding="utf-8"
            )

            result = PROPOSE_MODULE.propose_pks_batch(paper_dir=paper_dir)
            names = {c["local_name"] for c in result["concepts"]}
            self.assertNotIn("x", names)
            self.assertIn("real_concept", names)


class TestHypothesisProperties(unittest.TestCase):
    """Property-based tests."""

    @given(name=st.text(min_size=0, max_size=50))
    @settings(max_examples=100)
    def test_is_junk_name_never_crashes(self, name: str) -> None:
        """is_junk_name never raises on arbitrary strings."""
        result = PROPOSE_MODULE.is_junk_name(name)
        self.assertIsInstance(result, bool)


if __name__ == "__main__":
    unittest.main()
