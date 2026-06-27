"""Unit tests for scripts/render_pages.py (B1 rendering + B6 portability).

render_pages.py keeps the house ImageMagick ``magick`` workflow as the primary
rasterizer and cascades to pdftoppm then PyMuPDF (the Ghostscript-free safety net)
when magick is missing or fails. It also detects the Python interpreter name and
forces UTF-8 stdout so text extraction does not crash on a cp1252 Windows console.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


def load_render_pages():
    path = SCRIPTS_DIR / "render_pages.py"
    spec = importlib.util.spec_from_file_location("render_pages", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["render_pages"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def rp():
    return load_render_pages()


def test_module_imports(rp):
    assert rp is not None


def test_pick_rasterizer_prefers_magick_then_pdftoppm_then_pymupdf(rp):
    # House workflow: magick first; PyMuPDF is the guaranteed Ghostscript-free fallback.
    assert rp.pick_rasterizer({"pymupdf", "pdftoppm", "magick"}) == "magick"
    assert rp.pick_rasterizer({"pymupdf", "pdftoppm"}) == "pdftoppm"
    assert rp.pick_rasterizer({"pymupdf"}) == "pymupdf"
    assert rp.pick_rasterizer(set()) is None


def test_detect_python_prefers_python3(rp):
    assert rp.detect_python({"python3", "python"}) == "python3"
    assert rp.detect_python({"python"}) == "python"
    assert rp.detect_python(set()) is None


def test_configure_utf8_stdout_allows_non_latin1(rp, capsys):
    # Must not raise UnicodeEncodeError on a non-Latin-1 glyph.
    rp.configure_utf8_stdout()
    print("em-dash — and o-macron ō")
    out = capsys.readouterr().out
    assert "—" in out


def test_render_cascades_when_primary_rasterizer_fails(rp, tmp_path, monkeypatch):
    # magick present but failing (e.g. no Ghostscript delegate) must fall through.
    calls: list[str] = []

    def boom(pdf, out, dpi, first, last):
        calls.append("magick")
        raise RuntimeError("no Ghostscript delegate")

    def ok(pdf, out, dpi, first, last):
        calls.append("pdftoppm")
        return [out / "page-000.png"]

    monkeypatch.setattr(rp, "_available_rasterizers", lambda: {"magick", "pdftoppm"})
    monkeypatch.setitem(rp._RENDERERS, "magick", boom)
    monkeypatch.setitem(rp._RENDERERS, "pdftoppm", ok)

    result = rp.render("x.pdf", tmp_path)
    assert calls == ["magick", "pdftoppm"]  # magick tried first, then cascaded
    assert result == [tmp_path / "page-000.png"]


def test_page_count_via_pymupdf(rp, tmp_path):
    fitz = pytest.importorskip("fitz")
    pdf = tmp_path / "two.pdf"
    doc = fitz.open()
    doc.new_page()
    doc.new_page()
    doc.save(str(pdf))
    doc.close()
    assert rp.page_count(str(pdf)) == 2
