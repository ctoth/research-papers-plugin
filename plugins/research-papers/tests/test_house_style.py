"""Tests for F4: house-style em-dash lint (content .md only) + separator config."""
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
def hs():
    return _load("house_style", "house_style.py")


@pytest.fixture()
def gpi():
    return _load("generate_paper_index", "generate-paper-index.py")


def test_em_dash_flagged_in_content_md(hs, tmp_path):
    papers = tmp_path / "papers"
    d = papers / "A_2024_X"
    d.mkdir(parents=True)
    (d / "notes.md").write_text("a clean line\nhas an — em dash\n", encoding="utf-8")
    hits = hs.find_content_em_dashes(papers)
    assert any(h[0] == "A_2024_X/notes.md" for h in hits)


def test_em_dash_not_flagged_in_skillmd_or_scripts(hs, tmp_path):
    papers = tmp_path / "papers"
    d = papers / "A_2024_X"
    d.mkdir(parents=True)
    (d / "notes.md").write_text("clean content\n", encoding="utf-8")
    # These are NOT content .md and must be exempt even with em-dashes present.
    (d / "helper.py").write_text("# code with an — em dash\n", encoding="utf-8")
    (d / "SKILL.md").write_text("skill prose — with em dash\n", encoding="utf-8")
    files = {h[0] for h in hs.find_content_em_dashes(papers)}
    assert not any("helper.py" in f or "SKILL.md" in f for f in files)


def test_index_md_is_scanned(hs, tmp_path):
    papers = tmp_path / "papers"
    papers.mkdir()
    (papers / "index.md").write_text("## [T](D/notes.md)\nan — em dash\n", encoding="utf-8")
    files = {h[0] for h in hs.find_content_em_dashes(papers)}
    assert "index.md" in files


def test_separator_default_is_hyphen(hs, tmp_path):
    assert hs.separator(tmp_path) == " - "


def test_separator_from_config(hs, tmp_path):
    (tmp_path / ".research-papers.toml").write_text(
        '[house_style]\nseparator = " :: "\n', encoding="utf-8")
    assert hs.separator(tmp_path) == " :: "


def test_generate_index_warning_has_no_em_dash(gpi):
    warnings = gpi.validate_tags(["alias-tag"], {"canon"}, {"alias-tag": "canon"})
    assert warnings
    assert all("—" not in w for w in warnings)
