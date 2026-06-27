"""Contract tests for B4: sci-hub removed from the retrieval waterfall."""
from __future__ import annotations

from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
RETRIEVER = PLUGIN_ROOT / "skills" / "paper-retriever" / "SKILL.md"


def _text() -> str:
    return RETRIEVER.read_text(encoding="utf-8")


def test_no_scihub_anywhere():
    lowered = _text().lower()
    assert "sci-hub" not in lowered
    assert "scihub" not in lowered


def test_terminal_fallback_is_supply_a_pdf():
    assert "supply a PDF" in _text()


def test_title_based_open_repository_fallback():
    lowered = _text().lower()
    assert "unpaywall" in lowered
    assert "open-repository" in lowered or "open repository" in lowered or "open-access" in lowered
