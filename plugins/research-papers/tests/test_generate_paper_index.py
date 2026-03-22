"""Tests for tag registry loading and validation in generate-paper-index.py."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

# Import the functions we'll add to generate-paper-index.py
# The script uses hyphens in the filename, so we need importlib
import importlib
import sys


@pytest.fixture()
def gpi_module():
    """Import generate-paper-index.py as a module."""
    script_path = Path(__file__).parent.parent / "scripts" / "generate-paper-index.py"
    spec = importlib.util.spec_from_file_location("generate_paper_index", script_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_load_tag_registry_parses_canonical_and_aliases(tmp_path, gpi_module):
    """load_tag_registry returns canonical set and alias->canonical map."""
    tags_yaml = tmp_path / "tags.yaml"
    tags_yaml.write_text(yaml.dump({
        "tags": {
            "argumentation": {},
            "nonmonotonic-reasoning": {"aliases": ["non-monotonic-reasoning", "nml"]},
        }
    }))
    canonical, aliases = gpi_module.load_tag_registry(tmp_path)
    assert "argumentation" in canonical
    assert "nonmonotonic-reasoning" in canonical
    assert aliases["non-monotonic-reasoning"] == "nonmonotonic-reasoning"
    assert aliases["nml"] == "nonmonotonic-reasoning"
    # Aliases are NOT in the canonical set
    assert "non-monotonic-reasoning" not in canonical


def test_load_tag_registry_missing_file_returns_empty(tmp_path, gpi_module):
    """No tags.yaml -> empty canonical set and empty alias map (graceful degradation)."""
    canonical, aliases = gpi_module.load_tag_registry(tmp_path)
    assert canonical == set()
    assert aliases == {}


def test_validate_tags_canonical_passes(gpi_module):
    """Tags that match canonical names produce no warnings."""
    canonical = {"argumentation", "nonmonotonic-reasoning"}
    aliases = {}
    warnings = gpi_module.validate_tags(["argumentation", "nonmonotonic-reasoning"], canonical, aliases)
    assert warnings == []


def test_validate_tags_alias_warns_and_returns_canonical(gpi_module):
    """Alias tags produce a warning with the canonical replacement."""
    canonical = {"nonmonotonic-reasoning"}
    aliases = {"non-monotonic-reasoning": "nonmonotonic-reasoning"}
    warnings = gpi_module.validate_tags(["non-monotonic-reasoning"], canonical, aliases)
    assert len(warnings) == 1
    assert "non-monotonic-reasoning" in warnings[0]
    assert "nonmonotonic-reasoning" in warnings[0]


def test_validate_tags_unknown_warns(gpi_module):
    """Unknown tags produce a warning."""
    canonical = {"argumentation"}
    aliases = {}
    warnings = gpi_module.validate_tags(["totally-new-tag"], canonical, aliases)
    assert len(warnings) == 1
    assert "totally-new-tag" in warnings[0]


def test_canonicalize_tag_resolves_alias(gpi_module):
    """canonicalize_tag maps alias -> canonical, passes through canonical unchanged."""
    aliases = {"non-monotonic-reasoning": "nonmonotonic-reasoning"}
    assert gpi_module.canonicalize_tag("non-monotonic-reasoning", aliases) == "nonmonotonic-reasoning"
    assert gpi_module.canonicalize_tag("argumentation", aliases) == "argumentation"
