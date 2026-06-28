"""Contract tests for the split paper-retriever (core + pluggable access skills).

The core retriever handles open-access retrieval and hands off paywalled papers to
whichever ``paper-retriever-*`` access skill is enabled. sci-hub lives in its own access
skill (enabled by default), not inlined in the core.
"""
from __future__ import annotations

from pathlib import Path

SKILLS = Path(__file__).resolve().parent.parent / "skills"


def _text(skill: str) -> str:
    return (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")


def test_access_skills_exist():
    assert (SKILLS / "paper-retriever-scihub" / "SKILL.md").exists()
    assert (SKILLS / "paper-retriever-institutional" / "SKILL.md").exists()


def test_core_hands_off_and_does_not_inline_scihub():
    core = _text("paper-retriever")
    assert "paper-retriever-scihub" in core
    assert "paper-retriever-institutional" in core
    # The sci-hub mechanics moved out of the core into the access skill.
    assert "sci-hub.st" not in core


def test_scihub_access_skill_holds_the_scihub_mechanics():
    s = _text("paper-retriever-scihub")
    assert "sci-hub.st" in s
    # Access-skill contract: it only places paper.pdf; the core materializes metadata.
    assert "paper.pdf" in s


def test_institutional_access_skill_is_proxy_aware():
    s = _text("paper-retriever-institutional").lower()
    assert "ezproxy" in s or "openathens" in s or "proxy" in s


def test_access_skills_declare_a_name_in_frontmatter():
    for skill in (
        "paper-retriever-scihub",
        "paper-retriever-institutional",
        "paper-retriever-bookshare",
    ):
        head = "\n".join(_text(skill).splitlines()[:8])
        assert f"name: {skill}" in head


def test_bookshare_skill_drives_the_cli_and_is_download_only():
    s = _text("paper-retriever-bookshare")
    # Drives the published bookshare CLI via the creds wrapper, not bespoke API code.
    assert "bookshare_cli.py" in s
    assert "search" in s and "download" in s
    # Download-only: produces an EPUB, does not pretend to make a PDF here.
    assert "book.epub" in s and "download-only" in s.lower()


def test_bookshare_wrapper_loads_secrets_and_forwards_to_cli():
    wrapper = (
        SKILLS / "paper-retriever-bookshare" / "scripts" / "bookshare_cli.py"
    ).read_text(encoding="utf-8")
    assert ".secrets/bookshare.json" in wrapper
    assert "BOOKSHARE_" in wrapper
    assert "bookshare.main" in wrapper


def test_secrets_dir_is_gitignored():
    gitignore = (
        Path(__file__).resolve().parents[3] / ".gitignore"
    ).read_text(encoding="utf-8")
    assert ".secrets/" in gitignore
