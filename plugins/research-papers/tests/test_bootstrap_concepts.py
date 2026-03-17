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


# Will fail until bootstrap_concepts.py exists — that's the TDD point.
BOOTSTRAP_MODULE = load_module("bootstrap_concepts", SCRIPTS_DIR / "bootstrap_concepts.py")

# ---------------------------------------------------------------------------
# Inline test data
# ---------------------------------------------------------------------------

SAMPLE_CLAIMS_YAML_1 = """\
source:
  paper: Author_2000_GlottalModel
claims:
  - id: claim1
    type: parameter
    concept: fundamental_frequency
    value: 120
  - id: claim2
    type: parameter
    concept: open_quotient
    value: 0.5
  - id: claim3
    type: property
    concept: spectral_tilt
"""

SAMPLE_CLAIMS_YAML_2 = """\
source:
  paper: Author_2005_VocalTract
claims:
  - id: claim1
    type: parameter
    concept: formant_frequency
    value: 500
  - id: claim2
    type: parameter
    concept: fundamental_frequency
    value: 100
  - id: claim3
    type: property
    concept: vocal_tract_length
"""

# Strategy for generating concept-like names: lowercase letters and underscores
concept_name_strategy = st.from_regex(r"[a-z][a-z_]{2,20}", fullmatch=True)
concept_names_strategy = st.lists(concept_name_strategy, min_size=1, max_size=20, unique=True)


def _make_claims_dir(root: Path) -> Path:
    """Create a directory with sample claims.yaml files."""
    paper1 = root / "Author_2000_GlottalModel"
    paper1.mkdir(parents=True, exist_ok=True)
    (paper1 / "claims.yaml").write_text(SAMPLE_CLAIMS_YAML_1, encoding="utf-8")

    paper2 = root / "Author_2005_VocalTract"
    paper2.mkdir(parents=True, exist_ok=True)
    (paper2 / "claims.yaml").write_text(SAMPLE_CLAIMS_YAML_2, encoding="utf-8")

    return root


class TestExtractConceptNames(unittest.TestCase):
    """Tests for extract_concept_names."""

    def test_extract_concept_names_from_claims(self) -> None:
        """Given claims.yaml files with various concept fields, extracts all unique names."""
        with tempfile.TemporaryDirectory() as tmpdir:
            claims_dir = _make_claims_dir(Path(tmpdir))

            names = BOOTSTRAP_MODULE.extract_concept_names(claims_dir)

            self.assertIsInstance(names, set)
            self.assertIn("fundamental_frequency", names)
            self.assertIn("open_quotient", names)
            self.assertIn("spectral_tilt", names)
            self.assertIn("formant_frequency", names)
            self.assertIn("vocal_tract_length", names)
            # fundamental_frequency appears in both files but should only be in set once
            self.assertEqual(len(names), 5)


class TestGroupSimilarConcepts(unittest.TestCase):
    """Tests for group_similar_concepts."""

    def test_group_similar_concepts_groups_variants(self) -> None:
        """Similar names like fundamental_frequency, fundamental_freq, f0_frequency are grouped."""
        names = {"fundamental_frequency", "fundamental_freq", "f0_frequency", "open_quotient"}

        groups = BOOTSTRAP_MODULE.group_similar_concepts(names)

        # Find the group that contains fundamental_frequency
        fund_group = None
        for g in groups:
            if "fundamental_frequency" in g["members"]:
                fund_group = g
                break

        self.assertIsNotNone(fund_group, "No group found containing fundamental_frequency")
        self.assertIn("fundamental_freq", fund_group["members"])
        self.assertIn("f0_frequency", fund_group["members"])

    def test_dedup_is_idempotent(self) -> None:
        """Running group_similar_concepts twice produces the same result."""
        names = {"fundamental_frequency", "fundamental_freq", "open_quotient", "spectral_tilt"}

        groups_1 = BOOTSTRAP_MODULE.group_similar_concepts(names)
        # Extract canonical names from first run
        canonical_names_1 = {g["canonical_name"] for g in groups_1}
        groups_2 = BOOTSTRAP_MODULE.group_similar_concepts(canonical_names_1)
        canonical_names_2 = {g["canonical_name"] for g in groups_2}

        self.assertEqual(canonical_names_1, canonical_names_2)

    def test_every_name_in_exactly_one_group(self) -> None:
        """All input names appear in exactly one output group."""
        names = {"fundamental_frequency", "fundamental_freq", "open_quotient", "spectral_tilt"}

        groups = BOOTSTRAP_MODULE.group_similar_concepts(names)

        all_members = []
        for g in groups:
            all_members.extend(g["members"])

        # Every input name is present
        for name in names:
            self.assertIn(name, all_members)

        # No duplicates
        self.assertEqual(len(all_members), len(set(all_members)))

    def test_canonical_name_is_group_member(self) -> None:
        """canonical_name for each group is one of its members."""
        names = {"fundamental_frequency", "fundamental_freq", "open_quotient"}

        groups = BOOTSTRAP_MODULE.group_similar_concepts(names)

        for g in groups:
            self.assertIn(g["canonical_name"], g["members"])

    def test_single_names_get_own_group(self) -> None:
        """Unique names that don't match anything get their own singleton group."""
        names = {"fundamental_frequency", "spectral_tilt"}

        groups = BOOTSTRAP_MODULE.group_similar_concepts(names)

        # Each name should be in its own group (they're not similar)
        for g in groups:
            if "spectral_tilt" in g["members"]:
                self.assertEqual(len(g["members"]), 1)
                self.assertEqual(g["canonical_name"], "spectral_tilt")


class TestBootstrapPipeline(unittest.TestCase):
    """Tests for the full bootstrap pipeline."""

    def test_bootstrap_returns_groups(self) -> None:
        """bootstrap(claims_dir) returns list of group dicts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            claims_dir = _make_claims_dir(Path(tmpdir))

            result = BOOTSTRAP_MODULE.bootstrap(claims_dir)

            self.assertIsInstance(result, list)
            self.assertGreater(len(result), 0)
            for g in result:
                self.assertIn("canonical_name", g)
                self.assertIn("members", g)


class TestHypothesisProperties(unittest.TestCase):
    """Property-based tests using Hypothesis."""

    @given(names=concept_names_strategy)
    @settings(max_examples=50)
    def test_dedup_idempotent_property(self, names: list[str]) -> None:
        """dedup(dedup(x)) == dedup(x) for any input."""
        name_set = set(names)
        groups_1 = BOOTSTRAP_MODULE.group_similar_concepts(name_set)
        canonical_1 = {g["canonical_name"] for g in groups_1}
        groups_2 = BOOTSTRAP_MODULE.group_similar_concepts(canonical_1)
        canonical_2 = {g["canonical_name"] for g in groups_2}

        self.assertEqual(canonical_1, canonical_2)

    @given(names=concept_names_strategy)
    @settings(max_examples=50)
    def test_every_input_in_exactly_one_group_property(self, names: list[str]) -> None:
        """Every input name appears in exactly one output group."""
        name_set = set(names)
        groups = BOOTSTRAP_MODULE.group_similar_concepts(name_set)

        all_members = []
        for g in groups:
            all_members.extend(g["members"])

        for name in name_set:
            count = all_members.count(name)
            self.assertEqual(count, 1, f"{name} appears {count} times, expected 1")

    @given(names=concept_names_strategy)
    @settings(max_examples=50)
    def test_canonical_is_member_property(self, names: list[str]) -> None:
        """canonical_name is always a member of its group."""
        name_set = set(names)
        groups = BOOTSTRAP_MODULE.group_similar_concepts(name_set)

        for g in groups:
            self.assertIn(
                g["canonical_name"],
                g["members"],
                f"canonical_name {g['canonical_name']} not in members {g['members']}",
            )


if __name__ == "__main__":
    unittest.main()
