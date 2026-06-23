"""Tests for Bookshare token acquisition + caching (scripts/bookshare_auth.py).

No real network: `requests` is stubbed and `requests.post` is patched. Credential
state is sandboxed under a tempfile project root via the same credential_store the
module under test imports.
"""

import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"

if "requests" not in sys.modules:
    _stub = types.ModuleType("requests")
    _stub.post = None
    sys.modules["requests"] = _stub


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


AUTH = load_module("bookshare_auth_module", SCRIPTS_DIR / "bookshare_auth.py")
CRED = AUTH.credential_store  # same module instance the code uses


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def _ok_post(payload):
    return MagicMock(return_value=FakeResponse(payload))


class AcquireTokenTest(unittest.TestCase):
    def test_sends_basic_auth_and_password_grant(self) -> None:
        post = _ok_post(
            {"access_token": "T", "token_type": "Bearer", "expires_in": 3600,
             "scope": "basic"}
        )
        with patch.object(AUTH.requests, "post", post):
            token = AUTH.acquire_token_api(
                "KEY", "user@example.com", "pw",
                auth_base="https://auth.example/oauth/token",
            )
        self.assertEqual(token["access_token"], "T")
        # HTTP Basic = (api_key, "")
        self.assertEqual(post.call_args.kwargs.get("auth"), ("KEY", ""))
        data = post.call_args.kwargs.get("data")
        self.assertEqual(data.get("grant_type"), "password")
        self.assertEqual(data.get("username"), "user@example.com")
        self.assertEqual(data.get("password"), "pw")
        # URL is the token endpoint; the password is never in the URL.
        self.assertEqual(post.call_args.args[0], "https://auth.example/oauth/token")
        self.assertNotIn("pw", post.call_args.args[0])


class GetTokenOrAuthenticateTest(unittest.TestCase):
    def test_cache_hit_returns_without_network(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            with patch.object(CRED, "_now", return_value=1000.0):
                CRED.set_token("bookshare", {"access_token": "CACHED", "expires_in": 3600}, td)
            post = MagicMock(side_effect=AssertionError("network must not be called"))
            with patch.object(AUTH.requests, "post", post):
                with patch.object(CRED, "_now", return_value=1500.0):
                    tok = AUTH.get_token_or_authenticate(root=td, auth_method="api")
            self.assertEqual(tok["access_token"], "CACHED")
            post.assert_not_called()

    def test_cache_miss_authenticates_and_caches(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            CRED.save(
                "bookshare",
                {"secrets": {"api_key": "KEY", "username": "u", "password": "pw"}},
                td,
            )
            post = _ok_post({"access_token": "FRESH", "expires_in": 3600})
            with patch.object(AUTH.requests, "post", post):
                tok = AUTH.get_token_or_authenticate(root=td, auth_method="api")
            self.assertEqual(tok["access_token"], "FRESH")
            post.assert_called_once()
            # Now cached for next time.
            self.assertEqual(CRED.get_token("bookshare", td)["access_token"], "FRESH")

    def test_missing_secrets_raises_credential_error(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            post = MagicMock(side_effect=AssertionError("network must not be called"))
            with patch.object(AUTH.requests, "post", post):
                with self.assertRaises(CRED.CredentialError):
                    AUTH.get_token_or_authenticate(root=td, auth_method="api")
            post.assert_not_called()

    def test_browser_method_returns_session_marker_without_network(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            post = MagicMock(side_effect=AssertionError("network must not be called"))
            with patch.object(AUTH.requests, "post", post):
                tok = AUTH.get_token_or_authenticate(root=td, auth_method="browser")
            self.assertEqual(tok.get("auth_method"), "browser")
            self.assertIn("session", tok)
            post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
