"""Contract tests for paper-reader rendering/portability prose (B1, B6).

These assert on the SKILL.md text (the agent-executed procedure), mirroring the
existing test_source_workflow_contracts.py style.
"""
from __future__ import annotations

from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
READER = PLUGIN_ROOT / "skills" / "paper-reader" / "SKILL.md"


def _reader_text() -> str:
    return READER.read_text(encoding="utf-8")


def test_reader_names_non_ghostscript_rasterizer():
    text = _reader_text().lower()
    assert "pymupdf" in text or "fitz" in text
    assert "pdftoppm" in text


def test_reader_uses_render_pages_script():
    assert "render_pages.py" in _reader_text()


def test_reader_detects_interpreter_not_bare_python3():
    text = _reader_text()
    # The silent, Windows-broken bare invocation must be gone.
    assert 'python3 "$HASH_SCRIPT"' not in text
    # A portable interpreter-detection must be present.
    assert "command -v python3 || command -v python" in text


def test_reader_prefers_pymupdf_page_count_over_pdfinfo_only():
    # page count must no longer depend solely on pdfinfo (poppler absent on Windows)
    text = _reader_text()
    assert "render_pages.py" in text and "count" in text.lower()
