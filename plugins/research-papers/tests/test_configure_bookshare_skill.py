"""Structural guards for the configure-bookshare skill.

It must collect the user's Bookshare username + password, store them via
credential_store (without echoing the password), and select the browser backend.
"""

import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILL = PLUGIN_ROOT / "skills" / "configure-bookshare" / "SKILL.md"
LAUNCHER = PLUGIN_ROOT / "skills" / "configure-bookshare" / "scripts" / "credential_store.py"


class ConfigureSkillTest(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(SKILL.exists(), f"missing skill: {SKILL}")
        self.text = SKILL.read_text(encoding="utf-8")

    def test_frontmatter_names_the_skill(self) -> None:
        self.assertIn("name: configure-bookshare", self.text)

    def test_collects_username_and_password(self) -> None:
        low = self.text.lower()
        self.assertIn("username", low)
        self.assertIn("password", low)

    def test_stores_both_credentials_via_credential_store(self) -> None:
        self.assertIn("credential_store.py set bookshare username --from-stdin", self.text)
        self.assertIn("credential_store.py set bookshare password --from-stdin", self.text)

    def test_selects_browser_backend_as_default(self) -> None:
        self.assertIn("credential_store.py auth-method bookshare browser", self.text)

    def test_protects_the_password(self) -> None:
        # The skill must instruct not to echo/print the password and note where it lands.
        self.assertIn("Never", self.text)
        self.assertIn(".secrets", self.text)

    def test_launcher_present_for_credential_store(self) -> None:
        # The skill invokes credential_store.py via uv run, so it needs a launcher.
        self.assertTrue(LAUNCHER.exists(), f"missing launcher: {LAUNCHER}")


if __name__ == "__main__":
    unittest.main()
