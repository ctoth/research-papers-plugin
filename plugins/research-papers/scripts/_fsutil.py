#!/usr/bin/env python3
"""Cloud-sync-safe file operations (F3).

``papers/`` often lives in an odrive / Google Drive / Dropbox synced folder.
A raw move can race the sync daemon and destroy the source before the
destination is durable. These helpers always copy, verify (size + sha256), and
only then remove the source, so a sync race cannot lose data.

Import-only module (no CLI, no launcher needed). Reused by F2 (PDF adoption),
F3 (sync-safe ops), and F13 (adopt).
"""
from __future__ import annotations

import hashlib
import shutil
from pathlib import Path


class IntegrityError(Exception):
    """Raised when a copied file does not match its source (size or hash)."""


def sha256(path) -> str:
    """Return the hex sha256 of a file, read in chunks."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _verify(src, dst) -> None:
    """Raise IntegrityError unless dst matches src in size and sha256."""
    s, d = Path(src), Path(dst)
    s_size, d_size = s.stat().st_size, d.stat().st_size
    if s_size != d_size:
        raise IntegrityError(f"size mismatch: {s} ({s_size}) != {d} ({d_size})")
    if sha256(s) != sha256(d):
        raise IntegrityError(f"hash mismatch: {s} != {d}")


def copy_verify(src, dst) -> Path:
    """Copy src -> dst (creating parents) and verify integrity. Returns dst."""
    s, d = Path(src), Path(dst)
    d.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(s, d)
    _verify(s, d)
    return d


def safe_move(src, dst) -> Path:
    """Copy-verify src -> dst, then remove the source. Never a raw move/rename."""
    d = copy_verify(src, dst)
    Path(src).unlink()
    return d
