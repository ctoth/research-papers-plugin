#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["requests>=2.28"]
# ///
"""Bookshare authentication: acquire and cache an OAuth2 access token.

Sits between fetch_book.py and credential_store.py so the fetch script never reads
.secrets/ directly. Two pluggable backends:

  - "api"     : Bookshare OAuth2 *password grant* against the token endpoint.
                HTTP Basic auth = (api_key, ""), body grant_type=password with the
                member's username/password. Requires a developer api_key and
                trusted-client approval from Bookshare.
  - "browser" : returns a captured-session marker; wire up a driven login
                (e.g. Playwright) for members without an api_key.

Tokens are cached (with expiry) via credential_store; a valid cached token short-
circuits re-authentication.

CLI:
  uv run bookshare_auth.py token --root . [--auth-method api|browser]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import credential_store  # noqa: E402

SOURCE = "bookshare"
AUTH_BASE = "https://auth.bookshare.org/oauth/token"
SECRET_KEYS = ["api_key", "username", "password"]


def acquire_token_api(api_key: str, username: str, password: str,
                      auth_base: str = AUTH_BASE) -> dict:
    """Exchange member credentials for an access token (OAuth2 password grant).

    The api_key is the HTTP Basic username (blank password); the member's
    credentials travel in the request body, never the URL.
    """
    resp = requests.post(
        auth_base,
        auth=(api_key, ""),
        data={"grant_type": "password", "username": username, "password": password},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def _auth_base(root: str) -> str:
    cfg = credential_store.config_for_source(SOURCE, root)
    return cfg.get("auth_base", AUTH_BASE)


def get_token_or_authenticate(root: str = ".", auth_method: str = "api") -> dict | None:
    """Return a valid cached token, or authenticate and cache a fresh one."""
    cached = credential_store.get_token(SOURCE, root)
    if cached:
        return cached

    if auth_method == "browser":
        # A driven login (e.g. Playwright) would capture cookies/storage here.
        return {"auth_method": "browser", "session": "TODO"}

    secrets = credential_store.require_secrets(SOURCE, SECRET_KEYS, root)
    token = acquire_token_api(
        secrets["api_key"], secrets["username"], secrets["password"],
        auth_base=_auth_base(root),
    )
    credential_store.set_token(SOURCE, token, root)
    return token


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Bookshare authentication")
    sub = p.add_subparsers(dest="cmd", required=True)
    p_tok = sub.add_parser("token", help="Acquire/refresh a token; print validity only")
    p_tok.add_argument("--root", default=".")
    p_tok.add_argument("--auth-method", choices=["api", "browser"], default="api")
    args = p.parse_args(argv)

    try:
        token = get_token_or_authenticate(root=args.root, auth_method=args.auth_method)
    except credential_store.CredentialError as exc:
        print(json.dumps({"success": False, "error": str(exc)}, indent=2))
        return 1

    exp = (token or {}).get("expires_at")
    when = (time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(exp))
            if isinstance(exp, (int, float)) else None)
    # Never print the token itself.
    print(json.dumps({"success": bool(token), "auth_method": args.auth_method,
                      "token_valid_until": when}, indent=2))
    return 0 if token else 1


if __name__ == "__main__":
    sys.exit(main())
