"""Tests for the cross-platform skill helper-script launchers.

The canonical helper scripts live once in plugins/research-papers/scripts/.
Each skill that invokes one gets a tiny generated launcher at
skills/<skill>/scripts/<name>.py (see tools/sync_skill_launchers.py) that runs
the canonical implementation via runpy, located relative to its own __file__.
This replaces git symlinks, which break on Windows (core.symlinks=false
materializes them as text placeholders).
"""

import importlib.util
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = PLUGIN_ROOT / "tools"
SCRIPTS_DIR = PLUGIN_ROOT / "scripts"
SKILLS_DIR = PLUGIN_ROOT / "skills"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


gen = load_module("sync_skill_launchers", TOOLS_DIR / "sync_skill_launchers.py")


class LauncherMechanismTest(unittest.TestCase):
    """The rendered launcher runs its canonical target as __main__, argv passed through."""

    def test_launcher_execs_target_as_main_with_argv(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            canon_dir = root / "scripts"
            canon_dir.mkdir()
            canonical = canon_dir / "foo.py"
            canonical.write_text(
                textwrap.dedent(
                    '''\
                    import sys

                    def main():
                        print("SENTINEL-RAN")
                        print("ARGV0=" + sys.argv[0])
                        print("ARGS=" + ",".join(sys.argv[1:]))

                    if __name__ == "__main__":
                        main()
                    '''
                ),
                encoding="utf-8",
            )
            skill_scripts = root / "skills" / "myskill" / "scripts"
            skill_scripts.mkdir(parents=True)
            launcher = skill_scripts / "foo.py"
            launcher.write_text(gen.render_launcher(canonical), encoding="utf-8", newline="\n")

            proc = subprocess.run(
                [sys.executable, str(launcher), "alpha", "beta"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("SENTINEL-RAN", proc.stdout)
            self.assertIn("ARGS=alpha,beta", proc.stdout)

            argv0 = next(
                line[len("ARGV0=") :]
                for line in proc.stdout.splitlines()
                if line.startswith("ARGV0=")
            )
            self.assertEqual(
                Path(argv0).resolve(),
                canonical.resolve(),
                "launcher should rewrite sys.argv[0] to the canonical target path",
            )


class DriftGuardTest(unittest.TestCase):
    """Every on-disk launcher must be byte-identical to the generator output."""

    def test_on_disk_launchers_match_generator(self):
        for skill, names in gen.MANIFEST.items():
            for name in names:
                launcher = SKILLS_DIR / skill / "scripts" / name
                canonical = SCRIPTS_DIR / name
                with self.subTest(skill=skill, name=name):
                    self.assertTrue(launcher.exists(), f"missing launcher: {launcher}")
                    self.assertEqual(
                        launcher.read_text(encoding="utf-8"),
                        gen.render_launcher(canonical),
                        f"{skill}/scripts/{name} is stale; "
                        "regenerate via tools/sync_skill_launchers.py",
                    )


class DependencyParityTest(unittest.TestCase):
    """Each launcher's PEP 723 block must match its canonical script's block."""

    def test_launcher_pep723_matches_canonical(self):
        for skill, names in gen.MANIFEST.items():
            for name in names:
                canonical_block = gen.extract_pep723(
                    (SCRIPTS_DIR / name).read_text(encoding="utf-8")
                )
                launcher_block = gen.extract_pep723(
                    (SKILLS_DIR / skill / "scripts" / name).read_text(encoding="utf-8")
                )
                with self.subTest(skill=skill, name=name):
                    self.assertEqual(launcher_block, canonical_block)


class NoSymlinkRegressionTest(unittest.TestCase):
    """No symlink or symlink-placeholder file may remain under skills/*/scripts/."""

    def test_no_symlinks_or_placeholders(self):
        offenders = []
        for p in SKILLS_DIR.rglob("*.py"):
            if p.is_symlink():
                offenders.append(f"symlink: {p}")
                continue
            head = p.read_text(encoding="utf-8", errors="replace")[:3]
            if head == "../":
                offenders.append(f"placeholder: {p}")
        self.assertEqual(offenders, [], f"symlink/placeholder files remain: {offenders}")

    def test_obsolete_paper_id_copies_removed(self):
        for skill in ("paper-reader", "paper-retriever", "process-leads"):
            stale = SKILLS_DIR / skill / "scripts" / "_paper_id.py"
            with self.subTest(skill=skill):
                self.assertFalse(stale.exists(), f"{stale} should have been removed")


class ResolutionTest(unittest.TestCase):
    """Each launcher resolves (via parents[3]) to an existing canonical script."""

    def test_each_launcher_resolves_to_canonical(self):
        for skill, names in gen.MANIFEST.items():
            for name in names:
                launcher = SKILLS_DIR / skill / "scripts" / name
                target = launcher.resolve().parents[3] / "scripts" / name
                with self.subTest(skill=skill, name=name):
                    self.assertTrue(target.exists(), f"target missing: {target}")
                    self.assertEqual(target.resolve(), (SCRIPTS_DIR / name).resolve())


if __name__ == "__main__":
    unittest.main()
