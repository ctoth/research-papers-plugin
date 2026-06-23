"""Tests for the gitignored credential/token store (scripts/credential_store.py).

The store keeps one JSON file per source under <project-root>/.secrets/, holding
long-lived secrets plus a cached OAuth token. Nothing here touches the network;
all paths are sandboxed under a tempfile project root. Mirrors the load-by-path
+ tempfile conventions of test_fetch_paper.py / test_skill_launchers.py.
"""

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
REPO_ROOT = Path(__file__).resolve().parents[3]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


CRED = load_module("credential_store_module", SCRIPTS_DIR / "credential_store.py")


class StoreDirTest(unittest.TestCase):
    def test_store_dir_is_dot_secrets_under_root(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(CRED.store_dir(td), Path(td) / ".secrets")

    def test_source_path_is_named_json_under_store_dir(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(
                CRED.source_path("bookshare", td),
                Path(td) / ".secrets" / "bookshare.json",
            )


class RoundTripTest(unittest.TestCase):
    def test_save_then_load_returns_same_record(self) -> None:
        record = {
            "source": "bookshare",
            "auth_method": "api",
            "secrets": {"api_key": "K", "username": "u", "password": "p"},
        }
        with tempfile.TemporaryDirectory() as td:
            path = CRED.save("bookshare", record, td)
            self.assertTrue(Path(path).exists())
            self.assertEqual(CRED.load("bookshare", td), record)

    def test_load_missing_returns_empty_dict(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(CRED.load("bookshare", td), {})

    def test_set_secret_merges_without_clobbering(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            CRED.set_secret("bookshare", "username", "u", td)
            CRED.set_secret("bookshare", "password", "p", td)
            self.assertEqual(CRED.get_secret("bookshare", "username", td), "u")
            self.assertEqual(CRED.get_secret("bookshare", "password", td), "p")

    def test_get_secret_default_when_absent(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            self.assertIsNone(CRED.get_secret("bookshare", "api_key", td))
            self.assertEqual(
                CRED.get_secret("bookshare", "api_key", td, default="x"), "x"
            )


class RequireSecretsTest(unittest.TestCase):
    def test_returns_requested_secrets_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            CRED.save(
                "bookshare",
                {"secrets": {"api_key": "K", "username": "u", "password": "p"}},
                td,
            )
            got = CRED.require_secrets(
                "bookshare", ["api_key", "username", "password"], td
            )
            self.assertEqual(got, {"api_key": "K", "username": "u", "password": "p"})

    def test_raises_credential_error_listing_missing_without_leaking_values(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            CRED.save("bookshare", {"secrets": {"api_key": "SUPERSECRET"}}, td)
            with self.assertRaises(CRED.CredentialError) as ctx:
                CRED.require_secrets(
                    "bookshare", ["api_key", "username", "password"], td
                )
            msg = str(ctx.exception)
            # Names the missing keys and the file to populate...
            self.assertIn("username", msg)
            self.assertIn("password", msg)
            self.assertIn("bookshare.json", msg)
            # ...but never echoes the secret value that *was* present.
            self.assertNotIn("SUPERSECRET", msg)


class TokenCacheTest(unittest.TestCase):
    def test_get_token_none_when_absent(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            self.assertIsNone(CRED.get_token("bookshare", td))

    def test_set_token_computes_expires_at_from_expires_in(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            with patch.object(CRED, "_now", return_value=1000.0):
                CRED.set_token(
                    "bookshare",
                    {"access_token": "T", "token_type": "Bearer", "expires_in": 3600},
                    td,
                )
            stored = CRED.load("bookshare", td)["token"]
            self.assertEqual(stored["expires_at"], 1000.0 + 3600)
            self.assertEqual(stored["access_token"], "T")

    def test_get_token_returns_valid_token_before_expiry(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            with patch.object(CRED, "_now", return_value=1000.0):
                CRED.set_token("bookshare", {"access_token": "T", "expires_in": 3600}, td)
            with patch.object(CRED, "_now", return_value=2000.0):
                tok = CRED.get_token("bookshare", td)
            self.assertIsNotNone(tok)
            self.assertEqual(tok["access_token"], "T")

    def test_get_token_none_after_expiry_with_skew(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            with patch.object(CRED, "_now", return_value=1000.0):
                CRED.set_token("bookshare", {"access_token": "T", "expires_in": 100}, td)
            # now=1041, expires_at=1100, skew=60 -> 1100-60=1040 <= 1041 -> expired
            with patch.object(CRED, "_now", return_value=1041.0):
                self.assertIsNone(CRED.get_token("bookshare", td, skew=60))
            # now=1039 -> 1040 > 1039 -> still valid
            with patch.object(CRED, "_now", return_value=1039.0):
                self.assertIsNotNone(CRED.get_token("bookshare", td, skew=60))


class ConfigTest(unittest.TestCase):
    def test_config_for_source_absent_file_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(CRED.config_for_source("bookshare", td), {})

    def test_config_for_source_reads_sources_table(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / ".research-papers.toml").write_text(
                '[sources.bookshare]\nauth_method = "browser"\n', encoding="utf-8"
            )
            cfg = CRED.config_for_source("bookshare", td)
            self.assertEqual(cfg.get("auth_method"), "browser")

    def test_auth_method_prefers_record_then_config_then_default(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            # default when nothing set
            self.assertEqual(CRED.auth_method("bookshare", td), "api")
            # config wins over default
            (Path(td) / ".research-papers.toml").write_text(
                '[sources.bookshare]\nauth_method = "browser"\n', encoding="utf-8"
            )
            self.assertEqual(CRED.auth_method("bookshare", td), "browser")
            # explicit record wins over config
            CRED.save("bookshare", {"auth_method": "api"}, td)
            self.assertEqual(CRED.auth_method("bookshare", td), "api")


class GitignoreSafetyTest(unittest.TestCase):
    """Regression guard: the credential dir must stay out of version control."""

    def test_repo_gitignore_ignores_dot_secrets(self) -> None:
        gitignore = REPO_ROOT / ".gitignore"
        lines = [
            ln.strip() for ln in gitignore.read_text(encoding="utf-8").splitlines()
        ]
        self.assertIn(
            ".secrets",
            lines,
            ".secrets must be listed in the repo-root .gitignore so credentials "
            "are never committed",
        )


@unittest.skipUnless(os.name == "posix", "POSIX file permissions")
class PermissionsTest(unittest.TestCase):
    def test_saved_file_is_user_only_readable(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = CRED.save("bookshare", {"secrets": {"api_key": "K"}}, td)
            self.assertEqual(Path(path).stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
