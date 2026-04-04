import importlib.util
import json
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


class TestInferOrigin(unittest.TestCase):
    def test_prefers_doi_from_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            paper_dir = Path(tmpdir) / "Halpin_2010_OwlSameAsIsntSame"
            paper_dir.mkdir()
            metadata = {"doi": "10.1007/978-3-642-17746-0_20"}
            origin_type, origin_value = SYNC_MODULE.infer_origin(paper_dir, metadata)
            self.assertEqual(origin_type, "doi")
            self.assertEqual(origin_value, "10.1007/978-3-642-17746-0_20")

    def test_falls_back_to_pdf_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            paper_dir = Path(tmpdir) / "Halpin_2010_OwlSameAsIsntSame"
            paper_dir.mkdir()
            (paper_dir / "paper.pdf").write_bytes(b"%PDF-1.4\n")
            origin_type, origin_value = SYNC_MODULE.infer_origin(paper_dir, {})
            self.assertEqual(origin_type, "file")
            self.assertTrue(origin_value.endswith("paper.pdf"))


class TestBuildSyncCommands(unittest.TestCase):
    def test_builds_full_command_plan_from_available_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            paper_dir = Path(tmpdir) / "Halpin_2010_OwlSameAsIsntSame"
            paper_dir.mkdir()
            (paper_dir / "paper.pdf").write_bytes(b"%PDF-1.4\n")
            (paper_dir / "notes.md").write_text("# Notes\n", encoding="utf-8")
            (paper_dir / "metadata.json").write_text(
                json.dumps({"doi": "10.1007/978-3-642-17746-0_20"}),
                encoding="utf-8",
            )
            (paper_dir / "claims.yaml").write_text(
                yaml.safe_dump({"source": {"paper": paper_dir.name}, "claims": []}, sort_keys=False),
                encoding="utf-8",
            )
            (paper_dir / "justifications.yaml").write_text(
                yaml.safe_dump({"source": {"paper": paper_dir.name}, "justifications": []}, sort_keys=False),
                encoding="utf-8",
            )
            (paper_dir / "stances.yaml").write_text(
                yaml.safe_dump({"source": {"paper": paper_dir.name}, "stances": []}, sort_keys=False),
                encoding="utf-8",
            )
            (paper_dir / "concepts.yaml").write_text(
                yaml.safe_dump(
                    {
                        "concepts": [
                            {
                                "local_name": "claims_identical",
                                "definition": "A weak identity relation.",
                                "form": "structural",
                            }
                        ]
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )

            commands = SYNC_MODULE.build_sync_commands(paper_dir, finalize=True)

            self.assertEqual(commands[0][:4], ["pks", "source", "init", paper_dir.name])
            self.assertIn("--origin-type", commands[0])
            self.assertIn("--content-file", commands[0])
            self.assertTrue(any(command[:3] == ["pks", "source", "write-notes"] for command in commands))
            self.assertTrue(any(command[:3] == ["pks", "source", "write-metadata"] for command in commands))
            self.assertTrue(any(command[:3] == ["pks", "source", "add-concepts"] for command in commands))
            self.assertTrue(any(command[:3] == ["pks", "source", "add-claim"] for command in commands))
            self.assertTrue(any(command[:3] == ["pks", "source", "add-justification"] for command in commands))
            self.assertTrue(any(command[:3] == ["pks", "source", "add-stance"] for command in commands))
            self.assertEqual(commands[-1], ["pks", "source", "finalize", paper_dir.name])

    def test_includes_content_file_even_when_origin_is_doi(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            paper_dir = Path(tmpdir) / "Halpin_2010_OwlSameAsIsntSame"
            paper_dir.mkdir()
            (paper_dir / "paper.pdf").write_bytes(b"%PDF-1.4\n")
            (paper_dir / "metadata.json").write_text(
                json.dumps({"doi": "10.1007/978-3-642-17746-0_20"}),
                encoding="utf-8",
            )

            commands = SYNC_MODULE.build_sync_commands(paper_dir)

            self.assertIn("--origin-type", commands[0])
            self.assertEqual(
                commands[0][commands[0].index("--origin-type") + 1],
                "doi",
            )
            self.assertIn("--content-file", commands[0])
            self.assertTrue(commands[0][commands[0].index("--content-file") + 1].endswith("paper.pdf"))

    def test_promote_implies_finalize_then_promote(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            paper_dir = Path(tmpdir) / "Halpin_2010_OwlSameAsIsntSame"
            paper_dir.mkdir()
            commands = SYNC_MODULE.build_sync_commands(paper_dir, promote=True)
            self.assertEqual(commands[-2], ["pks", "source", "finalize", paper_dir.name])
            self.assertEqual(commands[-1], ["pks", "source", "promote", paper_dir.name])


if __name__ == "__main__":
    unittest.main()
