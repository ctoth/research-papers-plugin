"""Tests for scripts/build_keymap.py (B5: mandatory cite_key + papers/keymap.tsv).

cite_key must be the first key of every metadata.json; a keymap.tsv
(cite_key<TAB>dir) lets downstream tools resolve @key -> dir without parsing
directory names (whose years disagree with published cite-key years).
"""
from __future__ import annotations

import importlib.util
import json
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
def bk():
    return _load("build_keymap", "build_keymap.py")


def _write_paper(papers_dir: Path, name: str, metadata: dict) -> Path:
    d = papers_dir / name
    d.mkdir(parents=True)
    (d / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return d


def test_validate_cite_key_first_true(bk):
    text = json.dumps({"cite_key": "fan2018", "title": "X", "year": "2018"})
    assert bk.validate_cite_key_first(text) is True


def test_validate_cite_key_first_false_when_not_first(bk):
    text = json.dumps({"title": "X", "cite_key": "fan2018", "year": "2018"})
    assert bk.validate_cite_key_first(text) is False


def test_validate_cite_key_first_false_when_absent(bk):
    text = json.dumps({"title": "X", "year": "2018"})
    assert bk.validate_cite_key_first(text) is False


def test_extract_bibtex_key(bk):
    blob = "@article{Lee2022ImageExplorerMT,\n  title={x}\n}"
    assert bk.extract_bibtex_key(blob) == "Lee2022ImageExplorerMT"
    assert bk.extract_bibtex_key("no bibtex here") is None


def test_derive_cite_key_prefers_existing(bk):
    assert bk.derive_cite_key({"cite_key": "hirota2025societal"}, "Hirota_2022_Foo") == "hirota2025societal"


def test_derive_cite_key_from_bibtex_blob(bk):
    md = {"bibtex": "@article{Lee2022ImageExplorerMT, title={x}}"}
    assert bk.derive_cite_key(md, "Lee_2022_ImageExplorer") == "Lee2022ImageExplorerMT"


def test_derive_cite_key_generates_when_no_bibtex(bk):
    md = {"authors": ["Jane Fan"], "year": "2018"}
    assert bk.derive_cite_key(md, "Fan_2018_Foo") == "Fan_2018"


def test_build_keymap_emits_sorted_tsv(bk, tmp_path):
    papers = tmp_path / "papers"
    _write_paper(papers, "Zeta_2020_B", {"cite_key": "zeta2020b", "title": "B"})
    _write_paper(papers, "Alpha_2019_A", {"cite_key": "alpha2019a", "title": "A"})
    tsv = bk.build_keymap(papers)
    lines = [ln for ln in tsv.splitlines() if ln.strip()]
    assert lines == ["alpha2019a\tAlpha_2019_A", "zeta2020b\tZeta_2020_B"]


def test_backfill_inserts_cite_key_first(bk, tmp_path):
    papers = tmp_path / "papers"
    _write_paper(papers, "Fan_2018_Foo", {"title": "Foo", "authors": ["Jane Fan"], "year": "2018"})
    changed = bk.backfill(papers, write=True)
    assert "Fan_2018_Foo" in changed
    md = json.loads((papers / "Fan_2018_Foo" / "metadata.json").read_text(encoding="utf-8"))
    assert list(md.keys())[0] == "cite_key"
    assert md["cite_key"] == "Fan_2018"


def test_backfill_uses_embedded_bibtex_key(bk, tmp_path):
    papers = tmp_path / "papers"
    _write_paper(papers, "Lee_2022_ImageExplorer",
                 {"title": "X", "bibtex": "@inproceedings{Lee2022ImageExplorerMT, title={x}}"})
    bk.backfill(papers, write=True)
    md = json.loads((papers / "Lee_2022_ImageExplorer" / "metadata.json").read_text(encoding="utf-8"))
    assert md["cite_key"] == "Lee2022ImageExplorerMT"


def test_keymap_discovers_nested_chapters(bk, tmp_path):
    # F1: a book dir plus nested chapter paper dirs are all discovered, and each
    # chapter cite_key maps to its book/chapters/<dir> relative path (not the leaf).
    papers = tmp_path / "papers"
    _write_paper(papers, "Geertz_1973_Interpretation",
                 {"cite_key": "Geertz_1973_Interpretation", "title": "Book"})
    book = papers / "Geertz_1973_Interpretation"
    ch_a = book / "chapters" / "Geertz_1973_ThickDescription"
    ch_a.mkdir(parents=True)
    (ch_a / "metadata.json").write_text(
        json.dumps({"cite_key": "Geertz_1973_ThickDescription", "title": "Ch"}), encoding="utf-8")
    tsv = {ln.split("\t")[0]: ln.split("\t")[1] for ln in bk.build_keymap(papers).splitlines() if ln.strip()}
    assert tsv["Geertz_1973_ThickDescription"] == "Geertz_1973_Interpretation/chapters/Geertz_1973_ThickDescription"
    assert tsv["Geertz_1973_Interpretation"] == "Geertz_1973_Interpretation"
    # Book counted once; chapters add to (not replace) the book entry.
    assert len(tsv) == 2


def test_manifest_declares_cite_key_first():
    mod = _load("paper_db_manifest", "paper_db_manifest.py")
    assert mod.DEFAULT_MANIFEST.metadata_first_key == "cite_key"
    assert "cite_key" in mod.DEFAULT_MANIFEST.metadata_required
