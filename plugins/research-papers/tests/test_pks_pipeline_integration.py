"""Integration tests validating artifact-format contracts between pipeline stages.

These tests no longer use the legacy sync helper as the contract surface.
They validate the artifacts directly against the current skill boundaries.
"""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "research-papers"
SCRIPTS_DIR = PLUGIN_ROOT / "scripts"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PROPOSE_MODULE = load_module("propose_concepts", SCRIPTS_DIR / "propose_concepts.py")


def _make_full_paper_dir(root: Path) -> Path:
    paper_dir = root / "Bowman_2018_EffectsAspirinPrimaryPrevention"
    paper_dir.mkdir(parents=True, exist_ok=True)

    import json

    metadata = {
        "title": "Effects of Aspirin for Primary Prevention",
        "authors": ["ASCEND Study Collaborative Group"],
        "year": 2018,
        "doi": "10.1056/NEJMoa1804988",
    }
    (paper_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    (paper_dir / "notes.md").write_text("# Effects of Aspirin\n\nASCEND trial notes.", encoding="utf-8")
    (paper_dir / "paper.pdf").write_bytes(b"%PDF-1.4 placeholder")

    claims = {
        "source": {"paper": "Bowman_2018_EffectsAspirinPrimaryPrevention"},
        "claims": [
            {"id": "claim1", "type": "parameter", "output_concept": "rate_ratio", "value": 0.88, "unit": "dimensionless"},
            {"id": "claim2", "type": "parameter", "output_concept": "event_rate", "value": 8.5, "unit": "%"},
        ],
    }
    (paper_dir / "claims.yaml").write_text(
        yaml.dump(claims, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )

    concepts = {
        "concepts": [
            {
                "local_name": "event_rate",
                "proposed_name": "event_rate",
                "definition": "Rate of events in a population.",
                "form": "rate",
            },
            {
                "local_name": "rate_ratio",
                "proposed_name": "rate_ratio",
                "definition": "Ratio of event rates between groups.",
                "form": "ratio",
            },
        ]
    }
    (paper_dir / "concepts.yaml").write_text(
        yaml.dump(concepts, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )

    justifications = {
        "source": {"paper": "Bowman_2018_EffectsAspirinPrimaryPrevention"},
        "justifications": [
            {
                "id": "just1",
                "conclusion": "claim1",
                "premises": ["claim2"],
                "rule_kind": "empirical_support",
                "provenance": {"page": 5, "section": "Results"},
            }
        ],
    }
    (paper_dir / "justifications.yaml").write_text(
        yaml.dump(justifications, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )

    stances = {
        "source": {"paper": "Bowman_2018_EffectsAspirinPrimaryPrevention"},
        "stances": [
            {
                "source_claim": "claim1",
                "target": "McNeil_2018_EffectAspirinMortality:claim1",
                "type": "rebuts",
                "strength": "strong",
                "note": "ASCEND's benefit finding challenges ASPREE's harm signal.",
            }
        ],
    }
    (paper_dir / "stances.yaml").write_text(
        yaml.dump(stances, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )

    return paper_dir


class TestConceptsYamlMatchesPipelineContract(unittest.TestCase):
    def test_concepts_yaml_generated_from_claims_has_required_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            paper_dir = Path(tmpdir) / "TestPaper"
            paper_dir.mkdir()

            claims = {
                "source": {"paper": "TestPaper"},
                "claims": [
                    {"id": "c1", "type": "parameter", "output_concept": "rate_ratio", "value": 1.0}
                ],
            }
            (paper_dir / "claims.yaml").write_text(
                yaml.dump(claims, default_flow_style=False), encoding="utf-8"
            )

            result = PROPOSE_MODULE.propose_pks_batch(
                paper_dir=paper_dir,
                output_path=paper_dir / "concepts.yaml",
            )

            self.assertIn("concepts", result)
            self.assertEqual(result["concepts"][0]["local_name"], "rate_ratio")
            self.assertTrue((paper_dir / "concepts.yaml").exists())


class TestStancesYamlMatchesPipelineContract(unittest.TestCase):
    def test_stance_artifact_shape_matches_extract_stances_skill(self) -> None:
        skill = (PLUGIN_ROOT / "skills" / "extract-stances" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("source_claim", skill)
        self.assertIn("target", skill)
        self.assertIn("type", skill)

        with tempfile.TemporaryDirectory() as tmpdir:
            paper_dir = Path(tmpdir) / "TestPaper"
            paper_dir.mkdir()
            stances = {
                "source": {"paper": "TestPaper"},
                "stances": [
                    {"source_claim": "claim1", "target": "OtherPaper:claim2", "type": "supports"}
                ],
            }
            (paper_dir / "stances.yaml").write_text(
                yaml.dump(stances, default_flow_style=False),
                encoding="utf-8",
            )

            loaded = yaml.safe_load((paper_dir / "stances.yaml").read_text(encoding="utf-8"))
            self.assertIn("source", loaded)
            self.assertIn("stances", loaded)
            self.assertEqual(loaded["stances"][0]["source_claim"], "claim1")


class TestFullArtifactSetMatchesPaperProcessStages(unittest.TestCase):
    def test_full_artifacts_match_current_skill_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            paper_dir = _make_full_paper_dir(Path(tmpdir))

            source_bootstrap = (PLUGIN_ROOT / "skills" / "source-bootstrap" / "SKILL.md").read_text(
                encoding="utf-8"
            )
            paper_process = (PLUGIN_ROOT / "skills" / "paper-process" / "SKILL.md").read_text(
                encoding="utf-8"
            )

            self.assertTrue((paper_dir / "paper.pdf").exists())
            self.assertTrue((paper_dir / "notes.md").exists())
            self.assertTrue((paper_dir / "metadata.json").exists())
            self.assertTrue((paper_dir / "claims.yaml").exists())
            self.assertTrue((paper_dir / "concepts.yaml").exists())
            self.assertTrue((paper_dir / "justifications.yaml").exists())
            self.assertTrue((paper_dir / "stances.yaml").exists())

            self.assertIn("paper.pdf", source_bootstrap)
            self.assertIn("notes.md", source_bootstrap)
            self.assertIn("metadata.json", source_bootstrap)
            self.assertIn("source-bootstrap", paper_process)
            self.assertIn("extract-stances", paper_process)
            self.assertIn("source-promote", paper_process)


class TestConceptNamesRoundtrip(unittest.TestCase):
    def test_concept_names_match_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            paper_dir = Path(tmpdir) / "TestPaper"
            paper_dir.mkdir()

            claims = {
                "source": {"paper": "TestPaper"},
                "claims": [
                    {"id": "c1", "type": "parameter", "output_concept": "hazard_ratio", "value": 1.14},
                    {"id": "c2", "type": "parameter", "output_concept": "event_rate", "value": 12.7},
                ],
            }
            (paper_dir / "claims.yaml").write_text(
                yaml.dump(claims, default_flow_style=False), encoding="utf-8"
            )

            result = PROPOSE_MODULE.propose_pks_batch(paper_dir=paper_dir)
            concept_names = {c["local_name"] for c in result["concepts"]}

            for claim in claims["claims"]:
                concept_ref = claim.get("output_concept")
                if concept_ref:
                    self.assertIn(concept_ref, concept_names)


if __name__ == "__main__":
    unittest.main()
