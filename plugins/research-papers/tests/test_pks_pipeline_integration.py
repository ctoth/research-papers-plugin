"""Integration tests validating format contracts between pipeline stages.

These test that the file formats produced by one stage are accepted by the next,
without requiring pks to be installed. We validate against sync_propstore_source.py's
build_sync_commands() as the contract enforcer.
"""
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SYNC_MODULE = load_module("sync_propstore_source", SCRIPTS_DIR / "sync_propstore_source.py")
PROPOSE_MODULE = load_module("propose_concepts", SCRIPTS_DIR / "propose_concepts.py")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_full_paper_dir(root: Path) -> Path:
    """Create a paper directory with all pipeline artifacts."""
    paper_dir = root / "Bowman_2018_EffectsAspirinPrimaryPrevention"
    paper_dir.mkdir(parents=True, exist_ok=True)

    # metadata.json
    import json
    metadata = {
        "title": "Effects of Aspirin for Primary Prevention",
        "authors": ["ASCEND Study Collaborative Group"],
        "year": 2018,
        "doi": "10.1056/NEJMoa1804988",
    }
    (paper_dir / "metadata.json").write_text(
        json.dumps(metadata), encoding="utf-8"
    )

    # notes.md
    (paper_dir / "notes.md").write_text(
        "# Effects of Aspirin\n\nASCEND trial notes.", encoding="utf-8"
    )

    # paper.pdf (empty placeholder)
    (paper_dir / "paper.pdf").write_bytes(b"%PDF-1.4 placeholder")

    # claims.yaml
    claims = {
        "source": {"paper": "Bowman_2018_EffectsAspirinPrimaryPrevention"},
        "claims": [
            {
                "id": "claim1",
                "type": "parameter",
                "concept": "rate_ratio",
                "value": 0.88,
                "unit": "dimensionless",
            },
            {
                "id": "claim2",
                "type": "parameter",
                "concept": "event_rate",
                "value": 8.5,
                "unit": "%",
            },
        ],
    }
    (paper_dir / "claims.yaml").write_text(
        yaml.dump(claims, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )

    # concepts.yaml (pks batch format)
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

    # justifications.yaml
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

    # stances.yaml (standalone format, not embedded)
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


class TestConceptsYamlMatchesSyncSchema(unittest.TestCase):
    """Output of propose_pks_batch matches what sync_propstore_source.py expects."""

    def test_concepts_yaml_recognized_by_sync(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            paper_dir = Path(tmpdir) / "TestPaper"
            paper_dir.mkdir()

            claims = {
                "source": {"paper": "TestPaper"},
                "claims": [
                    {"id": "c1", "type": "parameter", "concept": "rate_ratio", "value": 1.0}
                ],
            }
            (paper_dir / "claims.yaml").write_text(
                yaml.dump(claims, default_flow_style=False), encoding="utf-8"
            )

            # Produce concepts.yaml via propose_pks_batch
            PROPOSE_MODULE.propose_pks_batch(
                paper_dir=paper_dir,
                output_path=paper_dir / "concepts.yaml",
            )

            # Verify sync script picks it up
            commands = SYNC_MODULE.build_sync_commands(paper_dir)
            cmd_strs = [" ".join(c) for c in commands]
            has_add_concepts = any("add-concepts" in s for s in cmd_strs)
            self.assertTrue(has_add_concepts, f"No add-concepts command found in: {cmd_strs}")


class TestStancesYamlMatchesSyncSchema(unittest.TestCase):
    """Standalone stances.yaml is recognized by sync_propstore_source.py."""

    def test_standalone_stances_recognized(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            paper_dir = Path(tmpdir) / "TestPaper"
            paper_dir.mkdir()

            stances = {
                "source": {"paper": "TestPaper"},
                "stances": [
                    {
                        "source_claim": "claim1",
                        "target": "OtherPaper:claim2",
                        "type": "supports",
                    }
                ],
            }
            (paper_dir / "stances.yaml").write_text(
                yaml.dump(stances, default_flow_style=False), encoding="utf-8"
            )

            commands = SYNC_MODULE.build_sync_commands(paper_dir)
            cmd_strs = [" ".join(c) for c in commands]
            has_add_stance = any("add-stance" in s for s in cmd_strs)
            self.assertTrue(has_add_stance, f"No add-stance command found in: {cmd_strs}")


class TestFullArtifactSetProducesCompleteCommandPlan(unittest.TestCase):
    """Paper dir with all artifacts produces the full pks source command sequence."""

    def test_full_artifacts_produce_7_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            paper_dir = _make_full_paper_dir(Path(tmpdir))

            commands = SYNC_MODULE.build_sync_commands(paper_dir)

            # Should have: init, write-notes, write-metadata, add-concepts,
            # add-claim, add-justification, add-stance = 7 commands
            cmd_ops = []
            for cmd in commands:
                cmd_str = " ".join(cmd)
                if "source init" in cmd_str:
                    cmd_ops.append("init")
                elif "write-notes" in cmd_str:
                    cmd_ops.append("write-notes")
                elif "write-metadata" in cmd_str:
                    cmd_ops.append("write-metadata")
                elif "add-concepts" in cmd_str:
                    cmd_ops.append("add-concepts")
                elif "add-claim" in cmd_str:
                    cmd_ops.append("add-claim")
                elif "add-justification" in cmd_str:
                    cmd_ops.append("add-justification")
                elif "add-stance" in cmd_str:
                    cmd_ops.append("add-stance")

            self.assertEqual(len(cmd_ops), 7, f"Expected 7 commands, got: {cmd_ops}")
            self.assertEqual(
                cmd_ops,
                ["init", "write-notes", "write-metadata", "add-concepts",
                 "add-claim", "add-justification", "add-stance"],
            )

    def test_finalize_and_promote_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            paper_dir = _make_full_paper_dir(Path(tmpdir))

            commands = SYNC_MODULE.build_sync_commands(paper_dir, promote=True)
            cmd_strs = [" ".join(c) for c in commands]

            has_finalize = any("finalize" in s for s in cmd_strs)
            has_promote = any("promote" in s for s in cmd_strs)
            self.assertTrue(has_finalize)
            self.assertTrue(has_promote)


class TestConceptNamesRoundtrip(unittest.TestCase):
    """Concepts proposed by propose_pks_batch can be referenced in claims.yaml."""

    def test_concept_names_match_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            paper_dir = Path(tmpdir) / "TestPaper"
            paper_dir.mkdir()

            claims = {
                "source": {"paper": "TestPaper"},
                "claims": [
                    {"id": "c1", "type": "parameter", "concept": "hazard_ratio", "value": 1.14},
                    {"id": "c2", "type": "parameter", "concept": "event_rate", "value": 12.7},
                ],
            }
            (paper_dir / "claims.yaml").write_text(
                yaml.dump(claims, default_flow_style=False), encoding="utf-8"
            )

            result = PROPOSE_MODULE.propose_pks_batch(paper_dir=paper_dir)
            concept_names = {c["local_name"] for c in result["concepts"]}

            # Every concept referenced in claims should appear in concepts.yaml
            for claim in claims["claims"]:
                concept_ref = claim.get("concept")
                if concept_ref:
                    self.assertIn(
                        concept_ref, concept_names,
                        f"Claim references '{concept_ref}' but concepts.yaml doesn't have it",
                    )


if __name__ == "__main__":
    unittest.main()
