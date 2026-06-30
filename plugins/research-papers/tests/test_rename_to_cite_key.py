import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


RENAME = load_module("rename_to_cite_key", SCRIPTS_DIR / "rename_to_cite_key.py")


def _write_paper(papers_dir: Path, dirname: str, cite_key: str) -> Path:
    d = papers_dir / dirname
    d.mkdir(parents=True, exist_ok=True)
    (d / "metadata.json").write_text(
        json.dumps({"cite_key": cite_key, "title": dirname}, indent=2) + "\n",
        encoding="utf-8",
    )
    (d / "notes.md").write_text("# notes\n", encoding="utf-8")
    return d


class PlanRenamesTests(unittest.TestCase):
    def test_plan_lists_only_mismatched(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            papers = Path(tmp) / "papers"
            _write_paper(papers, "Foo_2019_Bar", "foo2020bar")
            _write_paper(papers, "ok_key", "ok_key")
            renames = RENAME.plan_renames(papers)
            self.assertEqual(renames, [("Foo_2019_Bar", "foo2020bar")])


class DryRunTests(unittest.TestCase):
    def test_dryrun_lists_planned_renames_and_touches_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            papers = Path(tmp) / "papers"
            _write_paper(papers, "Foo_2019_Bar", "foo2020bar")
            rc = RENAME.main(["--papers-dir", str(papers)])
            self.assertEqual(rc, 0)
            # Dry run is the default: the dir must still exist under its old name.
            self.assertTrue((papers / "Foo_2019_Bar").is_dir())
            self.assertFalse((papers / "foo2020bar").exists())


class WriteTests(unittest.TestCase):
    def test_write_renames_and_rewrites_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            papers = Path(tmp) / "papers"
            _write_paper(papers, "Foo_2019_Bar", "foo2020bar")
            # A sibling paper whose notes.md cross-links the mismatched dir.
            sibling = _write_paper(papers, "sib2021", "sib2021")
            (sibling / "notes.md").write_text(
                "# sib\n\nSee [../Foo_2019_Bar/notes.md](../Foo_2019_Bar/notes.md) "
                "and [[Foo_2019_Bar]].\n",
                encoding="utf-8",
            )
            (papers / "index.md").write_text(
                "## [Bar](Foo_2019_Bar/notes.md)  (tag)\nDesc.\n\n"
                "## [Sib](sib2021/notes.md)\nDesc.\n\n",
                encoding="utf-8",
            )
            (papers / "_reader_done.tsv").write_text(
                "Foo_2019_Bar\tdone\nsib2021\tdone\n", encoding="utf-8"
            )
            (papers / "keymap.tsv").write_text(
                "foo2020bar\tFoo_2019_Bar\nsib2021\tsib2021\n", encoding="utf-8"
            )

            renames = RENAME.apply_renames(papers, write=True)
            self.assertEqual(renames, [("Foo_2019_Bar", "foo2020bar")])

            # Directory renamed.
            self.assertFalse((papers / "Foo_2019_Bar").exists())
            self.assertTrue((papers / "foo2020bar" / "notes.md").exists())

            # No file may still reference the old name.
            for ref_file in [
                papers / "index.md",
                papers / "_reader_done.tsv",
                papers / "keymap.tsv",
                papers / "sib2021" / "notes.md",
            ]:
                self.assertNotIn(
                    "Foo_2019_Bar",
                    ref_file.read_text(encoding="utf-8"),
                    f"stale reference remains in {ref_file.name}",
                )
            self.assertIn("foo2020bar/notes.md", (papers / "index.md").read_text(encoding="utf-8"))
            self.assertIn("[[foo2020bar]]", (papers / "sib2021" / "notes.md").read_text(encoding="utf-8"))

    def test_write_idempotent_on_compliant_corpus(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            papers = Path(tmp) / "papers"
            _write_paper(papers, "foo2020bar", "foo2020bar")
            before = (papers / "foo2020bar" / "metadata.json").read_text(encoding="utf-8")
            renames = RENAME.apply_renames(papers, write=True)
            self.assertEqual(renames, [])
            self.assertTrue((papers / "foo2020bar").is_dir())
            self.assertEqual(before, (papers / "foo2020bar" / "metadata.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
