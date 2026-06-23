"""Tests for F7: born-digital / large-document text-first reading path."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PLUGIN_ROOT / "scripts"


def _load_render_pages():
    path = SCRIPTS_DIR / "render_pages.py"
    spec = importlib.util.spec_from_file_location("render_pages", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["render_pages"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def rp():
    return _load_render_pages()


def test_should_use_text_path_true_for_clean_text_layer(rp):
    assert rp.should_use_text_path({"total_pages": 100, "text_pages": 98, "figure_dense": False}) is True


def test_should_use_text_path_false_for_scanned(rp):
    assert rp.should_use_text_path({"total_pages": 100, "text_pages": 8}) is False


def test_should_use_text_path_false_for_figure_dense(rp):
    assert rp.should_use_text_path({"total_pages": 100, "text_pages": 100, "figure_dense": True}) is False


def test_should_use_text_path_false_for_empty(rp):
    assert rp.should_use_text_path({"total_pages": 0, "text_pages": 0}) is False


def test_get_text_extracts_from_text_layer(rp, tmp_path):
    fitz = pytest.importorskip("fitz")
    pdf = tmp_path / "born_digital.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Hello text layer extraction")
    doc.save(str(pdf))
    doc.close()
    assert "Hello text layer extraction" in rp.get_text(str(pdf))


# Contract: the reader documents a text-first branch.
def test_reader_documents_text_first_branch():
    reader = (PLUGIN_ROOT / "skills" / "paper-reader" / "SKILL.md").read_text(encoding="utf-8")
    assert "text layer" in reader.lower()
    assert "get_text" in reader
    assert "should_use_text_path" in reader or "text-first" in reader.lower()
