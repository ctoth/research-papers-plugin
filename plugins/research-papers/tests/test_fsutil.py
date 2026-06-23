"""Tests for scripts/_fsutil.py (cloud-sync-safe copy-verify-then-remove)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


def _load(name: str, filename: str):
    path = SCRIPTS_DIR / filename
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def fs():
    return _load("_fsutil", "_fsutil.py")


def test_copy_verify_copies_and_keeps_source(fs, tmp_path):
    src = tmp_path / "src.bin"
    src.write_bytes(b"hello world" * 100)
    dst = tmp_path / "out" / "dst.bin"
    fs.copy_verify(src, dst)
    assert dst.read_bytes() == src.read_bytes()
    assert src.exists()  # copy, never move


def test_safe_move_copies_then_removes_source(fs, tmp_path):
    src = tmp_path / "src.bin"
    src.write_bytes(b"data" * 50)
    dst = tmp_path / "dst.bin"
    fs.safe_move(src, dst)
    assert dst.exists() and not src.exists()
    assert dst.read_bytes() == b"data" * 50


def test_verify_raises_on_size_mismatch(fs, tmp_path):
    src = tmp_path / "src"
    src.write_bytes(b"aaaa")
    dst = tmp_path / "dst"
    dst.write_bytes(b"aa")
    with pytest.raises(fs.IntegrityError):
        fs._verify(src, dst)


def test_verify_raises_on_hash_mismatch(fs, tmp_path):
    src = tmp_path / "src"
    src.write_bytes(b"aaaa")
    dst = tmp_path / "dst"
    dst.write_bytes(b"bbbb")  # same size, different bytes
    with pytest.raises(fs.IntegrityError):
        fs._verify(src, dst)
