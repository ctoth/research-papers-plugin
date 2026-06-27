"""Contract tests for F1: the paper-process --light (notes-only) flow."""
from __future__ import annotations

import re
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
PAPER_PROCESS = PLUGIN_ROOT / "skills" / "paper-process" / "SKILL.md"


def _text() -> str:
    return PAPER_PROCESS.read_text(encoding="utf-8")


def _light_section() -> str:
    """The body under the '## ... Light ...' heading, up to the next ## heading."""
    m = re.search(r"(?ms)^##[^\n]*[Ll]ight[^\n]*\n(.*?)(?=^## |\Z)", _text())
    return m.group(1) if m else ""


def test_light_flag_documented():
    assert "--light" in _text()
    assert "--notes-only" in _text()


def test_light_section_exists():
    assert _light_section().strip()


def test_light_section_runs_the_four_note_skills():
    section = _light_section()
    for skill in ("paper-retriever", "paper-reader", "tag-papers", "reconcile"):
        assert skill in section, f"light flow must invoke {skill}"


def test_light_section_skips_propstore():
    section = _light_section().lower()
    assert "skip" in section
    for term in ("source-bootstrap", "extract-claims", "source-promote", "pks"):
        assert term in section, f"light flow must state it skips {term}"
