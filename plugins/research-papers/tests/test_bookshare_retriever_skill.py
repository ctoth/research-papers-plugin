"""Structural guards for the bookshare-retriever skill prose and sample config.

Not a behavioral test -- it checks that the SKILL.md drives the documented scripts
in order and that the sample config documents the source without leaking secrets.
"""

import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL = PLUGIN_ROOT / "skills" / "bookshare-retriever" / "SKILL.md"
CONFIG_EXAMPLE = REPO_ROOT / ".research-papers.toml.example"


class SkillProseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(SKILL.exists(), f"missing skill: {SKILL}")
        self.text = SKILL.read_text(encoding="utf-8")

    def test_frontmatter_names_the_skill(self) -> None:
        self.assertIn("name: bookshare-retriever", self.text)

    def test_drives_the_scripts(self) -> None:
        self.assertIn("credential_store.py show bookshare", self.text)
        self.assertIn("fetch_book.py", self.text)

    def test_browser_is_the_default_backend(self) -> None:
        # Browser is the default experience: works with just username/password.
        self.assertIn("browser", self.text.lower())
        self.assertIn("bookshare_browser.py", self.text)
        # The API path (api_key) is documented as the alternative.
        self.assertIn("--auth-method api", self.text)

    def test_documents_epub_and_flags(self) -> None:
        self.assertIn("book.epub", self.text)
        self.assertIn("--convert", self.text)
        self.assertIn("--guest", self.text)

    def test_convert_step_uses_chrome_print_to_pdf(self) -> None:
        self.assertIn("--print-to-pdf", self.text)
        self.assertIn("paper.pdf", self.text)

    def test_never_instructs_printing_secret_values(self) -> None:
        # The skill must tell the model not to print secret values.
        self.assertIn("Never print", self.text)


class ConfigExampleTest(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(CONFIG_EXAMPLE.exists(), f"missing: {CONFIG_EXAMPLE}")
        self.text = CONFIG_EXAMPLE.read_text(encoding="utf-8")

    def test_documents_source_tables(self) -> None:
        self.assertIn("[sources.bookshare]", self.text)
        self.assertIn("auth_method", self.text)
        self.assertIn("convert_to_pdf", self.text)
        self.assertIn("[bookshare]", self.text)
        self.assertIn("api_base", self.text)
        self.assertIn("auth_base", self.text)

    def test_contains_no_secret_values(self) -> None:
        lowered = self.text.lower()
        # The sample must never carry real credentials.
        self.assertNotIn("stylizers16", self.text)
        self.assertNotIn("brandonkeithbiggs", lowered)
        # No assignment that hands a value to api_key/password.
        for forbidden in ('api_key = "', "api_key='", 'password = "', "password='"):
            self.assertNotIn(forbidden, self.text)


if __name__ == "__main__":
    unittest.main()
