"""Tests for F14 (chapter scope) + F15 (document_type / BibTeX) + F16 (theory profile)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PLUGIN_ROOT / "scripts"


def _load(name: str, filename: str):
    path = SCRIPTS_DIR / filename
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def rp():
    return _load("render_pages", "render_pages.py")


@pytest.fixture()
def eb():
    return _load("export_bibtex", "export_bibtex.py")


@pytest.fixture()
def manifest():
    return _load("paper_db_manifest", "paper_db_manifest.py")


# PyMuPDF get_toc format: [level, title, start_page].
TOC = [[1, "Front Matter", 1], [1, "Thick Description", 3], [2, "A Subsection", 10], [1, "Chapter 2", 34]]


def test_resolve_chapter_range_by_title(rp):
    assert rp.resolve_chapter_range(TOC, "Thick Description") == (3, 33)


def test_resolve_chapter_range_by_number(rp):
    # 2nd top-level entry is "Thick Description".
    assert rp.resolve_chapter_range(TOC, 2) == (3, 33)


def test_resolve_chapter_range_last_chapter_open_end(rp):
    assert rp.resolve_chapter_range(TOC, "Chapter 2") == (34, None)


def test_resolve_chapter_range_unknown_returns_none(rp):
    assert rp.resolve_chapter_range(TOC, "No Such Chapter") is None


def test_manifest_declares_document_types(manifest):
    types = manifest.DEFAULT_MANIFEST.document_types
    for t in ("article", "book", "book_chapter", "thesis", "report"):
        assert t in types
    assert manifest.DEFAULT_MANIFEST.document_type_default == "article"
    # cite_key-first from B5 is preserved.
    assert manifest.DEFAULT_MANIFEST.metadata_first_key == "cite_key"


def test_bibtex_incollection_for_chapter(eb):
    md = {
        "document_type": "book_chapter", "title": "Thick Description",
        "authors": ["Clifford Geertz"], "year": "1973",
        "container_title": "The Interpretation of Cultures",
        "publisher": "Basic Books", "pages": "3-30", "address": "New York",
    }
    out = eb._synthesize_bibtex(md, "Geertz_1973_ThickDescription")
    assert out.startswith("@incollection{")
    assert "booktitle = {The Interpretation of Cultures}" in out
    assert "publisher = {Basic Books}" in out
    assert "pages = {3-30}" in out


def test_bibtex_book_for_book(eb):
    md = {"document_type": "book", "title": "The Interpretation of Cultures",
          "authors": ["Clifford Geertz"], "year": "1973", "publisher": "Basic Books"}
    out = eb._synthesize_bibtex(md, "Geertz_1973_Interpretation")
    assert out.startswith("@book{")


def test_bibtex_article_default(eb):
    out = eb._synthesize_bibtex({"title": "X", "authors": ["A B"], "year": "2020"}, "B_2020_X")
    assert out.startswith("@article{")


def test_reader_documents_chapter_scope_and_theory_profile():
    reader = (PLUGIN_ROOT / "skills" / "paper-reader" / "SKILL.md").read_text(encoding="utf-8")
    assert "--chapter" in reader and "--pages" in reader
    assert "Ingestion scope" in reader
    assert "--profile theory" in reader
    assert "Load-Bearing Propositions" in reader
