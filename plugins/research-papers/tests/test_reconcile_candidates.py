"""Tests for F12: candidate-pool reconcile (graduation detection)."""
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
def rc():
    return _load("reconcile_candidates", "reconcile_candidates.py")


def test_graduates_detected_and_removed(rc):
    bib = "@article{a, title={x}}\n@article{b, title={y}}"
    draft = "We now cite [@a]."
    new_bib, graduated = rc.reconcile_candidates(bib, draft)
    assert "a" in graduated
    assert "a" not in rc.extract_keys(new_bib)
    assert "b" in rc.extract_keys(new_bib)  # genuine candidate untouched


def test_no_graduates_leaves_pool_intact(rc):
    bib = "@article{a, title={x}}"
    draft = "Cites nothing from the pool."
    new_bib, graduated = rc.reconcile_candidates(bib, draft)
    assert graduated == set()
    assert rc.extract_keys(new_bib) == {"a"}


def test_fix_pool_count(rc):
    md = "Candidate pool: 5 works not yet cited."
    assert rc.fix_pool_count(md, 3) == "Candidate pool: 3 works not yet cited."
