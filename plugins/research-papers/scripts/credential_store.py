#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Gitignored credential/token store for authenticated source adapters.

Secrets never belong in git, in skill prose, or in committed config. This module
keeps one JSON file per source under ``<project-root>/.secrets/<source>.json``:

    {
      "source": "bookshare",
      "auth_method": "api",
      "secrets": { "api_key": "...", "username": "...", "password": "..." },
      "token":   { "access_token": "...", "token_type": "Bearer",
                   "expires_at": 0, "scope": "" }
    }

``secrets`` are long-lived inputs the user provides once; ``token`` is the
code-managed OAuth cache (absent until first auth). The directory is matched by a
``.secrets`` entry in the repo-root ``.gitignore`` -- that gitignore line, plus
keeping the directory outside any synced tree, is the real protection; the
POSIX ``0600``/``0700`` modes set here are best-effort and advisory on Windows.

Import-only for the most part (like ``_paper_id.py``), plus a small CLI for
populating and inspecting the store without ever printing secret values::

    uv run credential_store.py set  bookshare api_key --root .   # value via stdin
    uv run credential_store.py show bookshare --root .           # presence only
    uv run credential_store.py path bookshare --root .
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover - 3.10 fallback
    tomllib = None  # type: ignore[assignment]

STORE_DIRNAME = ".secrets"
CONFIG_FILENAME = ".research-papers.toml"


class CredentialError(Exception):
    """Raised when required secrets are absent. ``str()`` is safe to print."""


def _now() -> float:
    """Current wall-clock seconds. Indirected so tests can pin time."""
    return time.time()


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def store_dir(root: str | os.PathLike[str] = ".") -> Path:
    """Return ``<root>/.secrets`` (no side effects)."""
    return Path(root) / STORE_DIRNAME


def source_path(source: str, root: str | os.PathLike[str] = ".") -> Path:
    """Return the JSON path for ``source`` (does not create anything)."""
    return store_dir(root) / f"{source}.json"


def _ensure_store_dir(root: str | os.PathLike[str]) -> Path:
    d = store_dir(root)
    d.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(d, 0o700)
    except OSError:  # pragma: no cover - advisory only (e.g. Windows)
        pass
    return d


# ---------------------------------------------------------------------------
# Whole-record load / save
# ---------------------------------------------------------------------------

def load(source: str, root: str | os.PathLike[str] = ".") -> dict:
    """Return the source record dict, or ``{}`` if the file is absent."""
    path = source_path(source, root)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save(source: str, record: dict, root: str | os.PathLike[str] = ".") -> Path:
    """Atomically write ``record`` as JSON; best-effort 0600. Returns the path."""
    _ensure_store_dir(root)
    path = source_path(source, root)
    fd, tmp = tempfile.mkstemp(prefix=f".{source}-", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    try:
        os.chmod(path, 0o600)
    except OSError:  # pragma: no cover - advisory only (e.g. Windows)
        pass
    return path


# ---------------------------------------------------------------------------
# Secret accessors
# ---------------------------------------------------------------------------

def get_secret(
    source: str, key: str, root: str | os.PathLike[str] = ".", default=None
):
    """Return one stored secret, or ``default`` if absent."""
    return load(source, root).get("secrets", {}).get(key, default)


def set_secret(
    source: str, key: str, value: str, root: str | os.PathLike[str] = "."
) -> None:
    """Merge one secret into the record and persist it."""
    record = load(source, root)
    record.setdefault("source", source)
    record.setdefault("secrets", {})[key] = value
    save(source, record, root)


def require_secrets(
    source: str, keys: list[str], root: str | os.PathLike[str] = "."
) -> dict:
    """Return the requested secrets or raise ``CredentialError``.

    The error names the missing keys and the file to populate but never echoes
    any value (present or missing).
    """
    secrets = load(source, root).get("secrets", {})
    missing = [k for k in keys if not secrets.get(k)]
    if missing:
        raise CredentialError(
            f"Missing {source} credential(s): {', '.join(missing)}. "
            f"Populate {source_path(source, root)} "
            f"(e.g. `credential_store.py set {source} {missing[0]} --root <root>`)."
        )
    return {k: secrets[k] for k in keys}


# ---------------------------------------------------------------------------
# Token cache (auth-method agnostic)
# ---------------------------------------------------------------------------

def get_token(
    source: str, root: str | os.PathLike[str] = ".", skew: int = 60
) -> dict | None:
    """Return the cached token only if present and not within ``skew`` of expiry."""
    token = load(source, root).get("token")
    if not token:
        return None
    expires_at = token.get("expires_at")
    if expires_at is None:
        return token
    if expires_at - skew > _now():
        return token
    return None


def set_token(
    source: str, token: dict, root: str | os.PathLike[str] = "."
) -> None:
    """Persist ``token``; derive ``expires_at`` from ``expires_in`` when needed."""
    token = dict(token)
    if "expires_at" not in token and "expires_in" in token:
        try:
            token["expires_at"] = _now() + float(token["expires_in"])
        except (TypeError, ValueError):  # pragma: no cover - defensive
            pass
    record = load(source, root)
    record.setdefault("source", source)
    record["token"] = token
    save(source, record, root)


# ---------------------------------------------------------------------------
# Non-secret config (.research-papers.toml)
# ---------------------------------------------------------------------------

def _load_config(root: str | os.PathLike[str] | None) -> dict:
    """Load ``.research-papers.toml`` at ``root``; ``{}`` when absent/unparseable."""
    if root is None or tomllib is None:
        return {}
    cfg = Path(root) / CONFIG_FILENAME
    if not cfg.exists():
        return {}
    try:
        return tomllib.loads(cfg.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):  # pragma: no cover - defensive
        return {}


def config_for_source(name: str, root: str | os.PathLike[str] = ".") -> dict:
    """Return non-secret config for a source: ``[sources.<name>]`` over ``[<name>]``."""
    cfg = _load_config(root)
    merged = dict(cfg.get(name, {})) if isinstance(cfg.get(name), dict) else {}
    sources = cfg.get("sources", {})
    if isinstance(sources, dict) and isinstance(sources.get(name), dict):
        merged.update(sources[name])
    return merged


def auth_method(
    source: str, root: str | os.PathLike[str] = ".", default: str = "api"
) -> str:
    """Resolve the auth backend: stored record > config > ``default``."""
    record = load(source, root)
    if record.get("auth_method"):
        return record["auth_method"]
    cfg = config_for_source(source, root)
    if cfg.get("auth_method"):
        return cfg["auth_method"]
    return default


# ---------------------------------------------------------------------------
# CLI (setup / inspection — never prints secret values)
# ---------------------------------------------------------------------------

def _cmd_set(args) -> int:
    if args.from_stdin or not sys.stdin.isatty():
        value = sys.stdin.readline().rstrip("\n")
    else:  # pragma: no cover - interactive
        import getpass

        value = getpass.getpass(f"{args.source} {args.key}: ")
    if not value:
        print("error: empty value", file=sys.stderr)
        return 1
    set_secret(args.source, args.key, value, args.root)
    print(f"set {args.key} for {args.source} -> {source_path(args.source, args.root)}")
    return 0


def _cmd_show(args) -> int:
    record = load(args.source, args.root)
    if not record:
        print(f"{args.source}: no credentials stored ({source_path(args.source, args.root)})")
        return 0
    print(f"{args.source} ({source_path(args.source, args.root)}):")
    print(f"  auth_method: {record.get('auth_method', auth_method(args.source, args.root))}")
    for key, val in sorted(record.get("secrets", {}).items()):
        print(f"  {key}: {'set' if val else 'empty'}")
    token = record.get("token")
    if token:
        exp = token.get("expires_at")
        when = (
            time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(exp))
            if isinstance(exp, (int, float))
            else "unknown"
        )
        state = "valid" if get_token(args.source, args.root) else "expired"
        print(f"  token: {state} (until {when})")
    else:
        print("  token: none")
    return 0


def _cmd_path(args) -> int:
    print(source_path(args.source, args.root))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Credential store setup/inspection")
    parser.add_argument("--root", default=".", help="Project root (default: .)")
    # Also accept --root after the subcommand, so either order works.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", default=".", help="Project root (default: .)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_set = sub.add_parser("set", parents=[common],
                           help="Store one secret (value read from stdin)")
    p_set.add_argument("source")
    p_set.add_argument("key")
    p_set.add_argument("--from-stdin", action="store_true", help="Read value from stdin")
    p_set.set_defaults(func=_cmd_set)

    p_show = sub.add_parser("show", parents=[common],
                            help="Show presence of secrets/token (no values)")
    p_show.add_argument("source")
    p_show.set_defaults(func=_cmd_show)

    p_path = sub.add_parser("path", parents=[common],
                            help="Print the credential file path")
    p_path.add_argument("source")
    p_path.set_defaults(func=_cmd_path)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
