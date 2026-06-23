"""Tests for the reusable source-adapter template and its contract.

A "source adapter" is a fetch script that retrieves an artifact into
``papers/<dirname>/`` and writes ``metadata.json``, conforming to a uniform
stdout/exit contract so authed and unauthed sources behave identically. The
template lives under ``templates/source-adapter/``.

This file guards the *template* (files present, placeholder drift, contract
documented, auth boundary). The runtime behaviour of the reference adapter
(``fetch_book.py``) is covered by ``test_fetch_book.py``; here we additionally
make a static check against it once it exists.
"""

import re
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = PLUGIN_ROOT / "templates" / "source-adapter"
SCRIPTS_DIR = PLUGIN_ROOT / "scripts"

EXPECTED_FILES = {
    "HOWTO.md",
    "SKILL.md.tmpl",
    "fetch_source.py.tmpl",
    "fetch_source_authed.py.tmpl",
    "source_auth.py.tmpl",
    "test_source_adapter.py.tmpl",
}

# The uniform stdout contract every fetch script returns (see HOWTO.md).
CONTRACT_KEYS = [
    "success",
    "source",
    "directory",
    "dirname",
    "artifact_path",
    "artifact_type",
    "metadata_path",
    "downloaded",
    "fallback_needed",
]

PLACEHOLDER_RE = re.compile(r"\{\{([A-Z_]+)\}\}")


def _tmpl_files():
    return sorted(TEMPLATE_DIR.glob("*.tmpl"))


class TemplateFilesExistTest(unittest.TestCase):
    def test_all_template_files_present(self) -> None:
        self.assertTrue(TEMPLATE_DIR.is_dir(), f"missing template dir: {TEMPLATE_DIR}")
        present = {p.name for p in TEMPLATE_DIR.iterdir()}
        self.assertTrue(
            EXPECTED_FILES.issubset(present),
            f"missing template files: {EXPECTED_FILES - present}",
        )


class PlaceholderDriftTest(unittest.TestCase):
    """Every {{PLACEHOLDER}} used in a .tmpl must be documented in HOWTO.md."""

    def test_every_placeholder_documented_in_howto(self) -> None:
        howto = (TEMPLATE_DIR / "HOWTO.md").read_text(encoding="utf-8")
        documented = set(PLACEHOLDER_RE.findall(howto))
        used = set()
        for tmpl in _tmpl_files():
            used |= set(PLACEHOLDER_RE.findall(tmpl.read_text(encoding="utf-8")))
        undocumented = used - documented
        self.assertEqual(
            undocumented,
            set(),
            f"placeholders used in templates but not documented in HOWTO.md: {undocumented}",
        )


class ContractDocumentedTest(unittest.TestCase):
    def test_howto_documents_every_contract_key(self) -> None:
        howto = (TEMPLATE_DIR / "HOWTO.md").read_text(encoding="utf-8")
        for key in CONTRACT_KEYS:
            self.assertIn(key, howto, f"HOWTO.md must document contract key '{key}'")


class AuthBoundaryTest(unittest.TestCase):
    """Unauthed adapters stay dependency-free; authed ones go through the store."""

    def test_unauthed_template_does_not_touch_credential_store(self) -> None:
        src = (TEMPLATE_DIR / "fetch_source.py.tmpl").read_text(encoding="utf-8")
        self.assertNotIn("credential_store", src)

    def test_authed_template_uses_credential_store_and_auth_helper(self) -> None:
        src = (TEMPLATE_DIR / "fetch_source_authed.py.tmpl").read_text(encoding="utf-8")
        self.assertIn("credential_store", src)
        self.assertIn("_auth", src)


class FetchTemplateShapeTest(unittest.TestCase):
    def test_both_fetch_templates_emit_json_and_reuse_generate_dirname(self) -> None:
        for name in ("fetch_source.py.tmpl", "fetch_source_authed.py.tmpl"):
            src = (TEMPLATE_DIR / name).read_text(encoding="utf-8")
            with self.subTest(template=name):
                self.assertIn("generate_dirname", src)
                self.assertIn("json.dumps", src)
                self.assertIn("metadata.json", src)


class ReferenceAdapterTest(unittest.TestCase):
    """Once the reference adapter exists, it must speak the documented contract."""

    def test_fetch_book_declares_contract_and_reuses_helpers(self) -> None:
        ref = SCRIPTS_DIR / "fetch_book.py"
        if not ref.exists():
            self.skipTest("fetch_book.py not implemented yet (Unit 4)")
        src = ref.read_text(encoding="utf-8")
        for key in CONTRACT_KEYS:
            self.assertIn(key, src, f"fetch_book.py must set contract key '{key}'")
        self.assertIn("generate_dirname", src)
        self.assertIn("credential_store", src)


if __name__ == "__main__":
    unittest.main()
