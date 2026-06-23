"""Tests for B2 (markdown-link index headers) and B3 (structural lint index check)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PLUGIN_ROOT / "scripts"


@pytest.fixture()
def gpi():
    path = SCRIPTS_DIR / "generate-paper-index.py"
    spec = importlib.util.spec_from_file_location("generate_paper_index", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --- B2: header format + title loading ---

def test_load_notes_title_from_frontmatter(gpi, tmp_path):
    notes = tmp_path / "notes.md"
    notes.write_text("---\ntitle: Pretty Title Here\nyear: 2024\n---\nbody\n", encoding="utf-8")
    assert gpi.load_notes_title(notes) == "Pretty Title Here"


def test_load_notes_title_strips_quotes(gpi, tmp_path):
    notes = tmp_path / "notes.md"
    notes.write_text('---\ntitle: "Quoted Title"\n---\n', encoding="utf-8")
    assert gpi.load_notes_title(notes) == "Quoted Title"


def test_load_notes_title_missing_returns_empty(gpi, tmp_path):
    notes = tmp_path / "notes.md"
    notes.write_text("no frontmatter here\n", encoding="utf-8")
    assert gpi.load_notes_title(notes) == ""


def test_render_index_header_is_markdown_link(gpi):
    header = gpi.render_index_header("Author_2024_ShortTitle", "Pretty Title", ["a", "b"])
    assert header == "## [Pretty Title](Author_2024_ShortTitle/notes.md)  (a, b)"


def test_render_index_header_two_space_gap_before_tags(gpi):
    header = gpi.render_index_header("Dir_X", "T", ["x"])
    assert "](Dir_X/notes.md)  (x)" in header  # exactly two spaces


def test_render_index_header_falls_back_to_dirname(gpi):
    header = gpi.render_index_header("Dir_X", "", [])
    assert header == "## [Dir_X](Dir_X/notes.md)"


# --- B3: lint structural index check (contract) ---

LINT = PLUGIN_ROOT / "skills" / "lint-paper" / "SKILL.md"


def test_lint_drops_weak_substring_grep():
    text = LINT.read_text(encoding="utf-8")
    assert 'grep -c "## $(basename $paper_dir)" papers/index.md' not in text


def test_lint_validates_link_target_to_notes_md():
    text = LINT.read_text(encoding="utf-8")
    assert "notes\\.md" in text  # the structural grep validates the link target
