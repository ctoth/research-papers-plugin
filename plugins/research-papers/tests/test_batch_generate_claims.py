import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# Will fail until batch_generate_claims.py exists — that's the TDD point.
BATCH_MODULE = load_module("batch_generate_claims", SCRIPTS_DIR / "batch_generate_claims.py")

# ---------------------------------------------------------------------------
# Inline test data
# ---------------------------------------------------------------------------

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

## Equations

$$
E(t) = E_0 \\cdot e^{\\alpha t} \\cdot \\sin(\\omega_g t)
$$

## Testable Properties

- F0 perturbation affects perceived naturalness
"""

SAMPLE_NOTES_MD_2 = """\
---
title: "A Vocal Tract Model"
authors: "B. Author"
year: 2005
venue: "Speech Communication"
---

# A Vocal Tract Model

## One-Sentence Summary
A model of vocal tract resonance.

## Parameters

| Name | Symbol | Units | Default | Range |
|------|--------|-------|---------|-------|
| Formant frequency | F1 | Hz | 500 | 200-900 |

## Testable Properties

- Formant spacing correlates with vowel identity
"""

SAMPLE_CLAIMS_YAML = """\
source:
  paper: Author_2000_GlottalModel
claims:
  - id: claim1
    type: parameter
    concept: fundamental_frequency
"""


def _make_paper_dir(root: Path, name: str, notes_md: str) -> Path:
    """Create a paper subdirectory with a notes.md file."""
    paper_dir = root / name
    paper_dir.mkdir(parents=True, exist_ok=True)
    (paper_dir / "notes.md").write_text(notes_md, encoding="utf-8")
    return paper_dir


class TestBatchGenerateClaims(unittest.TestCase):
    """Tests for batch_generate_claims.batch_generate."""

    def test_processes_directory_with_notes(self) -> None:
        """Dir with 2 paper subdirs that have notes.md -> processes both."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _make_paper_dir(root, "Author_2000_GlottalModel", SAMPLE_NOTES_MD)
            _make_paper_dir(root, "Author_2005_VocalTract", SAMPLE_NOTES_MD_2)

            result = BATCH_MODULE.batch_generate(root)

            self.assertEqual(result["processed"], 2)
            self.assertTrue((root / "Author_2000_GlottalModel" / "claims.yaml").exists())
            self.assertTrue((root / "Author_2005_VocalTract" / "claims.yaml").exists())

    def test_skips_papers_without_notes(self) -> None:
        """Dir with 1 paper that has notes.md and 1 without -> only processes the one with notes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _make_paper_dir(root, "Author_2000_GlottalModel", SAMPLE_NOTES_MD)
            # Create a dir without notes.md
            no_notes_dir = root / "Author_2010_NoNotes"
            no_notes_dir.mkdir()
            (no_notes_dir / "description.md").write_text("Just a description.", encoding="utf-8")

            result = BATCH_MODULE.batch_generate(root)

            self.assertEqual(result["processed"], 1)
            self.assertFalse((no_notes_dir / "claims.yaml").exists())

    def test_skip_existing_flag(self) -> None:
        """Dir with paper that already has claims.yaml -> skip_existing=True skips it."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paper_dir = _make_paper_dir(root, "Author_2000_GlottalModel", SAMPLE_NOTES_MD)
            (paper_dir / "claims.yaml").write_text(SAMPLE_CLAIMS_YAML, encoding="utf-8")

            # With skip_existing=True, should skip
            result_skip = BATCH_MODULE.batch_generate(root, skip_existing=True)
            self.assertEqual(result_skip["skipped"], 1)
            self.assertEqual(result_skip["processed"], 0)

            # Without skip_existing (default False), should overwrite
            result_overwrite = BATCH_MODULE.batch_generate(root, skip_existing=False)
            self.assertEqual(result_overwrite["processed"], 1)
            self.assertEqual(result_overwrite["skipped"], 0)

    def test_reports_summary_counts(self) -> None:
        """Verify return dict has correct processed/skipped/errors counts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _make_paper_dir(root, "Author_2000_GlottalModel", SAMPLE_NOTES_MD)
            _make_paper_dir(root, "Author_2005_VocalTract", SAMPLE_NOTES_MD_2)

            result = BATCH_MODULE.batch_generate(root)

            self.assertIn("processed", result)
            self.assertIn("skipped", result)
            self.assertIn("errors", result)
            self.assertIsInstance(result["processed"], int)
            self.assertIsInstance(result["skipped"], int)
            self.assertIsInstance(result["errors"], int)
            self.assertEqual(result["processed"], 2)
            self.assertEqual(result["skipped"], 0)
            self.assertEqual(result["errors"], 0)

    def test_empty_directory(self) -> None:
        """Empty dir -> processed=0, skipped=0, errors=0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            result = BATCH_MODULE.batch_generate(root)

            self.assertEqual(result["processed"], 0)
            self.assertEqual(result["skipped"], 0)
            self.assertEqual(result["errors"], 0)


if __name__ == "__main__":
    unittest.main()
