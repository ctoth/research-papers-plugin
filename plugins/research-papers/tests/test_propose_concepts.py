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
    concept: rate_ratio
    value: 0.88
    unit: "dimensionless"
  - id: claim2
    type: parameter
    concept: event_rate
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
    concept: hazard_ratio
    value: 1.14
    unit: "dimensionless"
  - id: claim2
    type: parameter
    concept: event_rate
    value: 12.7
    unit: "%"
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


class TestInferForm(unittest.TestCase):
    """Tests for infer_form."""

    def test_infer_form_from_units_hz(self) -> None:
        self.assertEqual(PROPOSE_MODULE.infer_form("anything", {"Hz": 3}), "frequency")

    def test_infer_form_from_units_ratio(self) -> None:
        self.assertEqual(PROPOSE_MODULE.infer_form("anything", {"ratio": 2}), "ratio")

    def test_infer_form_from_units_percent(self) -> None:
        self.assertEqual(PROPOSE_MODULE.infer_form("anything", {"%": 5}), "score")

    def test_infer_form_from_units_db(self) -> None:
        self.assertEqual(PROPOSE_MODULE.infer_form("anything", {"dB": 1}), "level")

    def test_infer_form_from_units_count(self) -> None:
        self.assertEqual(PROPOSE_MODULE.infer_form("anything", {"count": 1}), "count")

    def test_infer_form_from_name_f0(self) -> None:
        self.assertEqual(PROPOSE_MODULE.infer_form("f0_frequency", {}), "frequency")

    def test_infer_form_from_name_duration(self) -> None:
        self.assertEqual(PROPOSE_MODULE.infer_form("duration_ms", {}), "time")

    def test_infer_form_from_name_accuracy(self) -> None:
        self.assertEqual(PROPOSE_MODULE.infer_form("accuracy_score", {}), "score")

    def test_infer_form_unit_priority_over_name(self) -> None:
        """Unit-based inference takes priority over name-based."""
        result = PROPOSE_MODULE.infer_form("some_frequency", {"dB": 3})
        self.assertEqual(result, "level")

    def test_infer_form_no_match(self) -> None:
        self.assertIsNone(PROPOSE_MODULE.infer_form("xyzzy_concept", {}))


class TestIsJunkName(unittest.TestCase):
    """Tests for is_junk_name."""

    def test_pure_numbers_are_junk(self) -> None:
        self.assertTrue(PROPOSE_MODULE.is_junk_name("123"))
        self.assertTrue(PROPOSE_MODULE.is_junk_name("4.5"))

    def test_single_char_is_junk(self) -> None:
        self.assertTrue(PROPOSE_MODULE.is_junk_name("x"))

    def test_known_short_names_pass(self) -> None:
        self.assertFalse(PROPOSE_MODULE.is_junk_name("f0"))
        self.assertFalse(PROPOSE_MODULE.is_junk_name("oq"))
        self.assertFalse(PROPOSE_MODULE.is_junk_name("iou"))

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

    def test_collects_units(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            papers = _make_papers_dir(Path(tmpdir))
            concepts = PROPOSE_MODULE.extract_concepts(papers)
            self.assertIn("%", concepts["event_rate"]["units"])


class TestPropose(unittest.TestCase):
    """Tests for propose (the main pipeline)."""

    def test_skips_existing_concepts(self) -> None:
        """Concepts already in output_dir are not recreated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            papers = _make_papers_dir(Path(tmpdir) / "papers")
            output = Path(tmpdir) / "concepts"
            output.mkdir()

            # Pre-create a concept file
            import yaml
            existing = {
                "id": "concept1",
                "canonical_name": "event_rate",
                "status": "proposed",
                "definition": "Existing concept.",
                "domain": "cvd",
                "form": "rate",
            }
            (output / "event_rate.yaml").write_text(
                yaml.dump(existing, default_flow_style=False),
                encoding="utf-8",
            )

            stats = PROPOSE_MODULE.propose(
                papers_dir=papers,
                output_dir=output,
                domain="cvd",
            )
            self.assertGreaterEqual(stats["skipped_existing"], 1)

    def test_dry_run_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            papers = _make_papers_dir(Path(tmpdir) / "papers")
            output = Path(tmpdir) / "concepts"

            PROPOSE_MODULE.propose(
                papers_dir=papers,
                output_dir=output,
                domain="cvd",
                dry_run=True,
            )
            # Output dir should not be created in dry run
            if output.exists():
                files = list(output.glob("*.yaml"))
                self.assertEqual(len(files), 0)


class TestPksBatchMode(unittest.TestCase):
    """Tests for the --paper-dir --pks-batch output mode."""

    def test_pks_batch_single_paper(self) -> None:
        """Produces concepts.yaml in pks batch format."""
        import yaml

        with tempfile.TemporaryDirectory() as tmpdir:
            paper_dir = Path(tmpdir) / "Bowman_2018_EffectsAspirinPrimaryPrevention"
            paper_dir.mkdir()
            (paper_dir / "claims.yaml").write_text(
                SAMPLE_CLAIMS_YAML, encoding="utf-8"
            )

            result = PROPOSE_MODULE.propose_pks_batch(
                paper_dir=paper_dir,
                domain="cvd",
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
                domain="cvd",
            )

            names = {c["local_name"] for c in result["concepts"]}
            # These come from our sample claims
            self.assertIn("rate_ratio", names)
            self.assertIn("event_rate", names)
            self.assertIn("blood_pressure", names)

    def test_pks_batch_reuses_existing_registry(self) -> None:
        """When registry has a concept, proposed_name matches canonical."""
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
                domain="cvd",
            )

            rr = next(
                c for c in result["concepts"] if c["local_name"] == "rate_ratio"
            )
            self.assertEqual(rr["proposed_name"], "rate_ratio")

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
                domain="cvd",
                output_path=output_path,
            )

            self.assertTrue(output_path.exists())
            data = yaml.safe_load(output_path.read_text(encoding="utf-8"))
            self.assertIn("concepts", data)


class TestHypothesisProperties(unittest.TestCase):
    """Property-based tests."""

    @given(name=st.from_regex(r"[a-z][a-z_]{2,30}", fullmatch=True))
    @settings(max_examples=100)
    def test_infer_form_never_crashes(self, name: str) -> None:
        """infer_form never raises on arbitrary concept names."""
        result = PROPOSE_MODULE.infer_form(name, {})
        self.assertIsInstance(result, (str, type(None)))

    @given(name=st.text(min_size=0, max_size=50))
    @settings(max_examples=100)
    def test_is_junk_name_never_crashes(self, name: str) -> None:
        """is_junk_name never raises on arbitrary strings."""
        result = PROPOSE_MODULE.is_junk_name(name)
        self.assertIsInstance(result, bool)


if __name__ == "__main__":
    unittest.main()
