"""Tests for F10: deterministic core of citation-claim verification.

The LLM verdict itself is agent-driven (covered by a SKILL.md contract); the
extraction, keymap resolution, and report schema are unit-tested here.
"""
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
def vc():
    return _load("verify_citations", "verify_citations.py")


def test_extract_citations_maps_key_to_citing_sentence(vc):
    draft = "Alenichev captions archival images [@alenichev2023]. Other work differs [@smith2020]."
    out = vc.extract_citations(draft)
    assert "alenichev2023" in out and "smith2020" in out
    assert "captions archival images" in out["alenichev2023"][0]


def test_resolve_key_via_keymap(vc, tmp_path):
    papers = tmp_path / "papers"
    (papers / "Alen_2023_X").mkdir(parents=True)
    (papers / "Alen_2023_X" / "metadata.json").write_text(
        '{"cite_key": "alenichev2023", "title": "X"}', encoding="utf-8")
    assert vc.resolve_key("alenichev2023", papers) == "Alen_2023_X"


def test_render_report_schema(vc):
    r = vc.GradeReport(key="alenichev2023", verdict="MISATTRIBUTED",
                       snippet="captions, does not generate", fix="say 'captions'")
    out = vc.render_report([r])
    assert "alenichev2023" in out and "MISATTRIBUTED" in out and "captions" in out


def test_render_report_rejects_unknown_verdict(vc):
    with pytest.raises(ValueError):
        vc.render_report([vc.GradeReport(key="x", verdict="BOGUS")])


def test_verdicts_are_the_four_expected(vc):
    assert set(vc.VERDICTS) == {"SUPPORTED", "PARTIAL", "UNSUPPORTED", "MISATTRIBUTED"}


# Contract: the grading rubric lives in a skill, fanned out one subagent per paper.
def test_grading_skill_documents_rubric():
    skill = PLUGIN_ROOT / "skills" / "verify-citations" / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    for verdict in ("SUPPORTED", "PARTIAL", "UNSUPPORTED", "MISATTRIBUTED"):
        assert verdict in text
    assert "subagent" in text.lower()
