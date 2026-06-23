"""Tests for F2/F3/F6: PDF identity verification + synced_root config + skill prose."""
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
def pa():
    return _load("pdf_adoption", "pdf_adoption.py")


# --- F6: identity verification ---

def test_compare_identity_matches(pa):
    assert pa.compare_identity(
        "Image Explorer Multi-Modal Accessibility",
        "ImageExplorer: A Multi-Modal Image Exploration system for Accessibility, by Lee et al.",
    ) is True


def test_compare_identity_rejects_mismatch(pa):
    assert pa.compare_identity(
        "Thick Description Geertz Interpretation",
        "A totally different paper about quantum error correction in superconductors",
    ) is False


# --- F3: synced_root config ---

def test_synced_root_default_false(pa, tmp_path):
    assert pa.synced_root(tmp_path) is False


def test_synced_root_from_config(pa, tmp_path):
    (tmp_path / ".research-papers.toml").write_text("[sync]\nsynced_root = true\n", encoding="utf-8")
    assert pa.synced_root(tmp_path) is True


# --- F2/F6/F3: skill prose contracts ---

def test_process_new_papers_documents_from_pdf():
    text = (PLUGIN_ROOT / "skills" / "process-new-papers" / "SKILL.md").read_text(encoding="utf-8")
    assert "--from-pdf" in text
    assert "copy-verify" in text.lower()
    assert "halt" in text.lower()


def test_reader_halts_on_identity_mismatch():
    text = (PLUGIN_ROOT / "skills" / "paper-reader" / "SKILL.md").read_text(encoding="utf-8")
    assert "compare_identity" in text or ("identity" in text.lower() and "halt" in text.lower())


def test_reconcile_single_writer_when_synced():
    text = (PLUGIN_ROOT / "skills" / "reconcile" / "SKILL.md").read_text(encoding="utf-8")
    assert "synced_root" in text
    assert "single-writer" in text.lower() or "single writer" in text.lower()
