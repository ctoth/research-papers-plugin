#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["bookshare>=0.13"]
# ///
"""Drive the published ``bookshare`` CLI with credentials from .secrets/bookshare.json.

Thin glue so the bookshare-access skill can run `bookshare search/download` without
hand-managing credentials. Loads ``api_key`` / ``username`` / ``password`` from the
gitignored ``.secrets/bookshare.json`` into the ``BOOKSHARE_*`` environment (without
overriding values already set in the environment), then forwards all arguments to the
bookshare CLI.

Usage mirrors the bookshare CLI exactly, e.g.:
  uv run scripts/bookshare_cli.py search "<title>" --json
  uv run scripts/bookshare_cli.py download <id> -o "papers/<dirname>/book.epub"
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import bookshare

_SECRETS = Path(".secrets/bookshare.json")
_KEYS = ("api_key", "username", "password")


def _load_secrets() -> None:
    if not _SECRETS.exists():
        return
    data = json.loads(_SECRETS.read_text(encoding="utf-8"))
    for key in _KEYS:
        env = f"BOOKSHARE_{key.upper()}"
        if data.get(key) and not os.environ.get(env):
            os.environ[env] = str(data[key])


if __name__ == "__main__":
    _load_secrets()
    raise SystemExit(bookshare.main(sys.argv[1:]))
