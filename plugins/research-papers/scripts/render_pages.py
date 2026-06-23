#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pymupdf>=1.24"]
# ///
"""Cross-platform PDF page rendering and counting (B1, B6).

The primary rasterizer is PyMuPDF (``fitz``): pure-Python, needs no Ghostscript.
It falls back to ``pdftoppm`` (poppler), then ImageMagick ``magick`` (which
delegates PDF decoding to Ghostscript) only when neither is available. This
removes the hard Ghostscript dependency that blocked the reader on Windows.

The module also provides ``detect_python`` (so callers can invoke the right
interpreter name) and ``configure_utf8_stdout`` (so printing extracted text does
not crash on a cp1252 Windows console).

Usage:
  uv run scripts/render_pages.py count <pdf>
  uv run scripts/render_pages.py render <pdf> <out_dir> [--dpi 150] [--first N] [--last N]
  uv run scripts/render_pages.py rasterizer
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

# Preference order: pure-Python first, Ghostscript-dependent last.
RASTERIZER_PREFERENCE = ("pymupdf", "pdftoppm", "magick")


def configure_utf8_stdout() -> None:
    """Force UTF-8 on stdout/stderr so non-Latin-1 glyphs do not raise on Windows."""
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8")
            except (ValueError, OSError):
                pass


def detect_python(available=None):
    """Return the preferred interpreter name on PATH ('python3' then 'python').

    ``available`` may be passed (any iterable of names) for testing; otherwise it
    is probed via :func:`shutil.which`.
    """
    if available is None:
        available = {name for name in ("python3", "python") if shutil.which(name)}
    else:
        available = set(available)
    for name in ("python3", "python"):
        if name in available:
            return name
    return None


def _available_rasterizers() -> set[str]:
    found: set[str] = set()
    try:
        import fitz  # noqa: F401
        found.add("pymupdf")
    except Exception:
        pass
    if shutil.which("pdftoppm"):
        found.add("pdftoppm")
    if shutil.which("magick") or shutil.which("convert"):
        found.add("magick")
    return found


def pick_rasterizer(available=None):
    """Pick the best available rasterizer by preference order; None if none available."""
    if available is None:
        available = _available_rasterizers()
    else:
        available = set(available)
    for name in RASTERIZER_PREFERENCE:
        if name in available:
            return name
    return None


def page_count(pdf_path) -> int:
    """Return the page count via PyMuPDF (no poppler/``pdfinfo`` needed)."""
    import fitz

    with fitz.open(pdf_path) as doc:
        return doc.page_count


def _page_range(total: int, first, last) -> range:
    lo = 0 if first is None else max(0, first)
    hi = total - 1 if last is None else min(total - 1, last)
    return range(lo, hi + 1)


def _render_pymupdf(pdf_path, out: Path, dpi: int, first, last) -> list[Path]:
    import fitz

    written: list[Path] = []
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    with fitz.open(pdf_path) as doc:
        for i in _page_range(doc.page_count, first, last):
            pix = doc.load_page(i).get_pixmap(matrix=matrix)
            dest = out / f"page-{i:03d}.png"
            pix.save(str(dest))
            written.append(dest)
    return written


def _renumber_zero_based(out: Path, start: int) -> list[Path]:
    """Renumber sorted page-*.png produced by an external tool to 0-based page-%03d.png."""
    produced = sorted(out.glob("page-*.png"))
    written: list[Path] = []
    for offset, src in enumerate(produced):
        dest = out / f"page-{start + offset:03d}.png"
        if src != dest:
            src.replace(dest)
        written.append(dest)
    return written


def _render_pdftoppm(pdf_path, out: Path, dpi: int, first, last) -> list[Path]:
    cmd = ["pdftoppm", "-png", "-r", str(dpi)]
    if first is not None:
        cmd += ["-f", str(first + 1)]
    if last is not None:
        cmd += ["-l", str(last + 1)]
    cmd += [str(pdf_path), str(out / "page")]
    subprocess.run(cmd, check=True)
    return _renumber_zero_based(out, 0 if first is None else first)


def _render_magick(pdf_path, out: Path, dpi: int, first, last) -> list[Path]:
    spec = str(pdf_path)
    if first is not None or last is not None:
        lo = 0 if first is None else first
        hi = "" if last is None else last
        spec = f"{pdf_path}[{lo}-{hi}]"
    tool = "magick" if shutil.which("magick") else "convert"
    subprocess.run(
        [tool, "-density", str(dpi), spec, "-quality", "90",
         "-resize", "1960x1960>", str(out / "page-%03d.png")],
        check=True,
    )
    return _renumber_zero_based(out, 0 if first is None else first)


def render(pdf_path, out_dir, dpi: int = 150, first=None, last=None,
           rasterizer=None) -> list[Path]:
    """Render PDF pages to ``out_dir/page-%03d.png`` (0-based). Returns written paths."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rasterizer = rasterizer or pick_rasterizer()
    if rasterizer == "pymupdf":
        return _render_pymupdf(pdf_path, out, dpi, first, last)
    if rasterizer == "pdftoppm":
        return _render_pdftoppm(pdf_path, out, dpi, first, last)
    if rasterizer == "magick":
        return _render_magick(pdf_path, out, dpi, first, last)
    raise RuntimeError(
        "No PDF rasterizer available. Install PyMuPDF (`pip install pymupdf`) or "
        "poppler (`pdftoppm`), or ImageMagick + Ghostscript as a last resort."
    )


def main(argv=None) -> int:
    configure_utf8_stdout()
    parser = argparse.ArgumentParser(description="Cross-platform PDF rendering/counting")
    sub = parser.add_subparsers(dest="command", required=True)

    p_count = sub.add_parser("count", help="Print the page count")
    p_count.add_argument("pdf")

    p_render = sub.add_parser("render", help="Render pages to <out_dir>/page-NNN.png")
    p_render.add_argument("pdf")
    p_render.add_argument("out_dir")
    p_render.add_argument("--dpi", type=int, default=150)
    p_render.add_argument("--first", type=int, default=None, help="0-based first page")
    p_render.add_argument("--last", type=int, default=None, help="0-based last page")

    sub.add_parser("rasterizer", help="Print the chosen rasterizer")

    args = parser.parse_args(argv)
    if args.command == "count":
        print(page_count(args.pdf))
    elif args.command == "render":
        written = render(args.pdf, args.out_dir, dpi=args.dpi,
                         first=args.first, last=args.last)
        print(len(written))
    elif args.command == "rasterizer":
        print(pick_rasterizer() or "none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
