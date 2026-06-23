"""Tests for F8 (collection-verify) + F9 (processed-ledger) via lint_paper_schema."""
from __future__ import annotations

import importlib.util
import json
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
def lint():
    return _load("lint_paper_schema", "lint_paper_schema.py")


def _make_paper(papers: Path, name: str, *, cite_key_first=True, metadata=True,
                abstract_ok=True, emdash=False) -> Path:
    d = papers / name
    d.mkdir(parents=True)
    notes_body = "see — dash" if emdash else "clean body"
    (d / "notes.md").write_text(f"---\ntitle: T\nyear: 2024\n---\n{notes_body}\n", encoding="utf-8")
    (d / "description.md").write_text("---\ntags: [alpha]\n---\ndesc\n", encoding="utf-8")
    if abstract_ok:
        (d / "abstract.md").write_text(
            "## Original Text (Verbatim)\nx\n\n## Our Interpretation\ny\n", encoding="utf-8")
    else:
        (d / "abstract.md").write_text("just an abstract, no sections\n", encoding="utf-8")
    (d / "citations.md").write_text("cites\n", encoding="utf-8")
    if metadata:
        md = {"cite_key": "t2024", "title": "T"} if cite_key_first else {"title": "T", "cite_key": "t2024"}
        (d / "metadata.json").write_text(json.dumps(md), encoding="utf-8")
    return d


def _codes(violations):
    return {v.code for v in violations}


def test_clean_collection_has_no_violations(lint, tmp_path):
    papers = tmp_path / "papers"
    papers.mkdir()
    _make_paper(papers, "A_2024_X")
    (papers / "index.md").write_text("## [A](A_2024_X/notes.md)\n\n", encoding="utf-8")
    (papers / "_reader_done.tsv").write_text("t2024\tA_2024_X\n", encoding="utf-8")
    assert _codes(lint.lint_collection(papers)) == set()


def test_count_mismatch_index(lint, tmp_path):
    papers = tmp_path / "papers"
    papers.mkdir()
    _make_paper(papers, "A_2024_X")
    (papers / "index.md").write_text(
        "## [A](A_2024_X/notes.md)\n\n## [B](B_2024_Y/notes.md)\n\n", encoding="utf-8")
    assert "COUNT_MISMATCH" in _codes(lint.lint_collection(papers))


def test_ledger_count_mismatch(lint, tmp_path):
    papers = tmp_path / "papers"
    papers.mkdir()
    _make_paper(papers, "A_2024_X")
    (papers / "index.md").write_text("## [A](A_2024_X/notes.md)\n\n", encoding="utf-8")
    (papers / "_reader_done.tsv").write_text("t2024\tA_2024_X\nextra\tB_2024_Y\n", encoding="utf-8")
    assert "COUNT_MISMATCH" in _codes(lint.lint_collection(papers))


def test_cite_key_not_first(lint, tmp_path):
    papers = tmp_path / "papers"
    papers.mkdir()
    _make_paper(papers, "A_2024_X", cite_key_first=False)
    assert "CITE_KEY_NOT_FIRST" in _codes(lint.lint_collection(papers))


def test_metadata_missing(lint, tmp_path):
    papers = tmp_path / "papers"
    papers.mkdir()
    _make_paper(papers, "A_2024_X", metadata=False)
    assert "METADATA_MISSING" in _codes(lint.lint_collection(papers))


def test_abstract_sections(lint, tmp_path):
    papers = tmp_path / "papers"
    papers.mkdir()
    _make_paper(papers, "A_2024_X", abstract_ok=False)
    assert "ABSTRACT_SECTIONS" in _codes(lint.lint_collection(papers))


def test_em_dash_flagged_in_content(lint, tmp_path):
    papers = tmp_path / "papers"
    papers.mkdir()
    _make_paper(papers, "A_2024_X", emdash=True)
    assert "EM_DASH" in _codes(lint.lint_collection(papers))


def test_tag_not_registered(lint, tmp_path):
    papers = tmp_path / "papers"
    papers.mkdir()
    _make_paper(papers, "A_2024_X")  # uses tag 'alpha'
    (papers / "tags.yaml").write_text("tags:\n  beta:\n    count: 1\n", encoding="utf-8")
    assert "TAG_NOT_REGISTERED" in _codes(lint.lint_collection(papers))


# F9 contract: the reader appends the processed-ledger entry.
def test_reader_appends_processed_ledger():
    reader = PLUGIN_ROOT / "skills" / "paper-reader" / "SKILL.md"
    assert "_reader_done.tsv" in reader.read_text(encoding="utf-8")
