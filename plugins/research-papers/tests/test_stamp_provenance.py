import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent / "scripts" / "stamp_provenance.py"
)
SPEC = importlib.util.spec_from_file_location("stamp_provenance", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

TS = "2026-03-27T14:00:00Z"


class StampMdTests(unittest.TestCase):
    def test_adds_produced_by_to_frontmatter(self) -> None:
        source = '---\ntitle: "Sample"\nyear: 2020\n---\n\n# Sample\n\nBody.\n'
        result, changed = MODULE.stamp_md(source, "claude-opus-4-6", "paper-reader", "4.0", TS)
        self.assertTrue(changed)
        self.assertIn('produced_by:', result)
        self.assertIn('agent: "claude-opus-4-6"', result)
        self.assertIn('skill: "paper-reader"', result)
        self.assertIn('plugin_version: "4.0"', result)
        self.assertIn(f'timestamp: "{TS}"', result)
        # Body preserved
        self.assertIn("# Sample", result)
        self.assertIn("Body.", result)

    def test_replaces_existing_produced_by(self) -> None:
        source = (
            '---\ntitle: "Sample"\n'
            'produced_by:\n  agent: "old-model"\n  skill: "old-skill"\n  timestamp: "old"\n'
            '---\n\n# Sample\n'
        )
        result, changed = MODULE.stamp_md(source, "claude-opus-4-6", "paper-reader", "4.0", TS)
        self.assertTrue(changed)
        self.assertNotIn("old-model", result)
        self.assertIn('agent: "claude-opus-4-6"', result)
        # Only one produced_by block
        self.assertEqual(result.count("produced_by:"), 1)

    def test_no_frontmatter_returns_unchanged(self) -> None:
        source = "# No frontmatter\n\nJust body.\n"
        result, changed = MODULE.stamp_md(source, "claude-opus-4-6", "paper-reader", "4.0", TS)
        self.assertFalse(changed)
        self.assertEqual(result, source)

    def test_omits_plugin_version_when_none(self) -> None:
        source = '---\ntitle: "Sample"\n---\n\nBody.\n'
        result, changed = MODULE.stamp_md(source, "claude-opus-4-6", "paper-reader", None, TS)
        self.assertTrue(changed)
        self.assertNotIn("plugin_version", result)
        self.assertIn('agent: "claude-opus-4-6"', result)

    def test_idempotent_on_second_run(self) -> None:
        source = '---\ntitle: "Sample"\n---\n\nBody.\n'
        first, _ = MODULE.stamp_md(source, "claude-opus-4-6", "paper-reader", "4.0", TS)
        second, changed = MODULE.stamp_md(first, "claude-opus-4-6", "paper-reader", "4.0", TS)
        self.assertFalse(changed)
        self.assertEqual(first, second)


class StampYamlTests(unittest.TestCase):
    def test_adds_produced_by_after_source_block(self) -> None:
        source = "source:\n  paper: TestPaper\nclaims:\n- id: claim1\n"
        result, changed = MODULE.stamp_yaml(source, "claude-opus-4-6", "extract-claims", "4.0", TS)
        self.assertTrue(changed)
        self.assertIn('produced_by:', result)
        self.assertIn('agent: "claude-opus-4-6"', result)
        # source block still present
        self.assertIn("source:", result)
        self.assertIn("paper: TestPaper", result)
        # claims still present
        self.assertIn("claims:", result)

    def test_replaces_existing_produced_by_in_yaml(self) -> None:
        source = (
            "source:\n  paper: TestPaper\n"
            "produced_by:\n  agent: \"old\"\n  skill: \"old\"\n"
            "claims:\n- id: claim1\n"
        )
        result, changed = MODULE.stamp_yaml(source, "claude-opus-4-6", "extract-claims", "4.0", TS)
        self.assertTrue(changed)
        self.assertNotIn('"old"', result)
        self.assertIn('agent: "claude-opus-4-6"', result)
        self.assertEqual(result.count("produced_by:"), 1)

    def test_prepends_when_no_source_block(self) -> None:
        source = "claims:\n- id: claim1\n"
        result, changed = MODULE.stamp_yaml(source, "claude-opus-4-6", "extract-claims", "4.0", TS)
        self.assertTrue(changed)
        self.assertTrue(result.startswith("produced_by:"))
        self.assertIn("claims:", result)

    def test_idempotent_on_second_run(self) -> None:
        source = "source:\n  paper: TestPaper\nclaims:\n- id: claim1\n"
        first, _ = MODULE.stamp_yaml(source, "claude-opus-4-6", "extract-claims", "4.0", TS)
        second, changed = MODULE.stamp_yaml(first, "claude-opus-4-6", "extract-claims", "4.0", TS)
        self.assertFalse(changed)
        self.assertEqual(first, second)


class FindPluginVersionTests(unittest.TestCase):
    def test_finds_version_from_plugin_json(self) -> None:
        # The script itself lives under plugins/research-papers/scripts/,
        # so walking up from it should find .claude-plugin/plugin.json.
        version = MODULE.find_plugin_version(SCRIPT_PATH)
        self.assertIsNotNone(version)
        self.assertEqual(version, "4.0")


if __name__ == "__main__":
    unittest.main()
