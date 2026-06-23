"""Tests for F11: lit-review draft<->bibtex key symmetry + citation-stripped word count."""
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
def lr():
    return _load("lit_review", "lit_review.py")


def test_key_symmetry_flags_missing(lr):
    draft = "We cite [@a] and also [@b]."
    bib = "@article{a, title={x}}"
    sym = lr.key_symmetry(draft, bib)
    assert "b" in sym["missing"]
    assert sym["orphan"] == set()


def test_key_symmetry_flags_orphan(lr):
    draft = "We cite [@a]."
    bib = "@article{a, title={x}}\n@inproceedings{c, title={y}}"
    sym = lr.key_symmetry(draft, bib)
    assert "c" in sym["orphan"]
    assert sym["missing"] == set()


def test_key_symmetry_clean(lr):
    draft = "We cite [@a] and [@b]."
    bib = "@article{a,...}\n@book{b,...}"
    sym = lr.key_symmetry(draft, bib)
    assert sym["missing"] == set() and sym["orphan"] == set()


def test_citation_stripped_word_count(lr):
    # "We cite [@key2020] three words." -> "We cite three words" == 4 words
    assert lr.citation_stripped_word_count("We cite [@key2020] three words.") == 4


def test_citation_stripped_word_count_multi_key(lr):
    # markers removed: "Foo bar baz" == 3
    assert lr.citation_stripped_word_count("Foo [@a; @b] bar baz") == 3
