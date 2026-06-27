"""Tests for scripts/_textutil.py (em-dash detector, shared by F4 and F8)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


def _load(name: str, filename: str):
    path = SCRIPTS_DIR / filename
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def tu():
    return _load("_textutil", "_textutil.py")


def test_find_em_dashes_reports_line_and_col(tu):
    text = "clean line\nhas — dash\n"
    assert tu.find_em_dashes(text) == [(2, 4)]  # line 2, 0-based col 4


def test_find_em_dashes_empty_when_clean(tu):
    assert tu.find_em_dashes("a - b hyphen only\n") == []


def test_find_em_dashes_multiple(tu):
    text = "— first\nsecond\nthird —\n"
    assert tu.find_em_dashes(text) == [(1, 0), (3, 6)]
