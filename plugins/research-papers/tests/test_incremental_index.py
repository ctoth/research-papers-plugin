"""Tests for F5: incremental, format-preserving index/tags maintenance."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import yaml

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PLUGIN_ROOT / "scripts"


@pytest.fixture()
def gpi():
    path = SCRIPTS_DIR / "generate-paper-index.py"
    spec = importlib.util.spec_from_file_location("generate_paper_index", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_insert_entry_places_sorted_preserving_neighbor_bytes(gpi):
    index = (
        "## [Alpha](Alpha_2019_A/notes.md)  (x)\nAlpha desc\n\n"
        "## [Charlie](Charlie_2021_C/notes.md)  (y)\nCharlie desc\n\n"
    )
    result = gpi.insert_entry(index, "Beta_2020_B", "Beta", ["z"], "Beta desc")
    # Neighbors are byte-for-byte unchanged.
    assert "## [Alpha](Alpha_2019_A/notes.md)  (x)\nAlpha desc\n\n" in result
    assert "## [Charlie](Charlie_2021_C/notes.md)  (y)\nCharlie desc\n\n" in result
    # Beta is inserted between them (case-sensitive sort by dir name).
    assert result.index("Alpha_2019_A") < result.index("Beta_2020_B") < result.index("Charlie_2021_C")
    assert "## [Beta](Beta_2020_B/notes.md)  (z)" in result


def test_insert_entry_idempotent(gpi):
    index = "## [Alpha](Alpha_2019_A/notes.md)  (x)\nAlpha desc\n\n"
    once = gpi.insert_entry(index, "Beta_2020_B", "Beta", ["z"], "Beta desc")
    twice = gpi.insert_entry(once, "Beta_2020_B", "Beta", ["z"], "Beta desc")
    assert once == twice


def test_insert_entry_replaces_existing(gpi):
    index = "## [Beta](Beta_2020_B/notes.md)  (old)\nold desc\n\n"
    result = gpi.insert_entry(index, "Beta_2020_B", "Beta New", ["new"], "new desc")
    assert "old" not in result
    assert "## [Beta New](Beta_2020_B/notes.md)  (new)" in result


def test_bump_tag_counts_increments_and_registers(gpi):
    text = "tags:\n  context:\n    count: 2\n  ethnography:\n    count: 1\n"
    out = gpi.bump_tag_counts(text, ["context", "interpretive-theory"])
    data = yaml.safe_load(out)
    assert data["tags"]["context"]["count"] == 3
    assert data["tags"]["ethnography"]["count"] == 1
    assert data["tags"]["interpretive-theory"]["count"] == 1
    assert list(data["tags"].keys()) == ["context", "ethnography", "interpretive-theory"]


def test_insert_paper_does_not_rebuild_tagged(gpi, tmp_path, monkeypatch):
    papers = tmp_path / "papers"
    d = papers / "Beta_2020_B"
    d.mkdir(parents=True)
    (d / "notes.md").write_text("---\ntitle: Beta\n---\n", encoding="utf-8")
    (d / "description.md").write_text("---\ntags: [z]\n---\nBeta desc\n", encoding="utf-8")
    (papers / "index.md").write_text(
        "## [Alpha](Alpha_2019_A/notes.md)  (x)\nAlpha desc\n\n", encoding="utf-8")

    def boom(*a, **k):
        raise AssertionError("rmtree must not be called by --insert")

    monkeypatch.setattr(gpi.shutil, "rmtree", boom)
    gpi.insert_paper(papers, "Beta_2020_B")
    text = (papers / "index.md").read_text(encoding="utf-8")
    assert "Beta_2020_B/notes.md" in text
    assert "Alpha_2019_A/notes.md" in text
    assert not (papers / "tagged").exists()
