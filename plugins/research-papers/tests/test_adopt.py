"""Tests for F13: adopt a cross-collection paper into a collection (compose F3+F5+F12)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


def _load(name: str, filename: str):
    path = SCRIPTS_DIR / filename
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def adopt():
    return _load("adopt", "adopt.py")


def _make_src(tmp_path: Path) -> Path:
    src = tmp_path / "mainbib" / "Lee_2022_ImageExplorer"
    src.mkdir(parents=True)
    (src / "notes.md").write_text("---\ntitle: Image Explorer\n---\nbody\n", encoding="utf-8")
    (src / "description.md").write_text("---\ntags: [accessibility]\n---\nA paper.\n", encoding="utf-8")
    (src / "metadata.json").write_text(
        '{"cite_key": "lee2022imageexplorer", "title": "Image Explorer"}', encoding="utf-8")
    return src


def _make_collection(tmp_path: Path) -> Path:
    papers = tmp_path / "papers"
    papers.mkdir()
    (papers / "index.md").write_text(
        "## [Aaa](Aaa_2020_X/notes.md)  (x)\nAaa desc\n\n", encoding="utf-8")
    (papers / "tags.yaml").write_text("tags:\n  accessibility:\n    count: 0\n", encoding="utf-8")
    return papers


def test_adopt_copy_verifies_dir(adopt, tmp_path):
    src = _make_src(tmp_path)
    _make_collection(tmp_path)
    adopt.adopt(src, tmp_path)
    dest = tmp_path / "papers" / "Lee_2022_ImageExplorer"
    assert (dest / "notes.md").read_text(encoding="utf-8") == (src / "notes.md").read_text(encoding="utf-8")
    assert (dest / "metadata.json").exists()


def test_adopt_inserts_index_entry(adopt, tmp_path):
    src = _make_src(tmp_path)
    papers = _make_collection(tmp_path)
    adopt.adopt(src, tmp_path)
    index = (papers / "index.md").read_text(encoding="utf-8")
    assert "## [Image Explorer](Lee_2022_ImageExplorer/notes.md)  (accessibility)" in index
    # Existing entry preserved.
    assert "## [Aaa](Aaa_2020_X/notes.md)  (x)" in index


def test_adopt_bumps_tag_counts(adopt, tmp_path):
    import yaml
    src = _make_src(tmp_path)
    papers = _make_collection(tmp_path)
    adopt.adopt(src, tmp_path)
    data = yaml.safe_load((papers / "tags.yaml").read_text(encoding="utf-8"))
    assert data["tags"]["accessibility"]["count"] == 1


def test_adopt_removes_from_candidate_pool(adopt, tmp_path):
    src = _make_src(tmp_path)
    _make_collection(tmp_path)
    pool = tmp_path / "candidate_citations.bibtex"
    pool.write_text(
        "@article{lee2022imageexplorer, title={x}}\n@article{other2021, title={y}}\n", encoding="utf-8")
    adopt.adopt(src, tmp_path, candidate_bibtex=pool)
    remaining = pool.read_text(encoding="utf-8")
    assert "lee2022imageexplorer" not in remaining
    assert "other2021" in remaining
