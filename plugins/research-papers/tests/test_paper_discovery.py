import importlib.util
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


DISC = load_module("paper_discovery", SCRIPTS_DIR / "paper_discovery.py")


def _mk(d: Path, *files: str) -> None:
    d.mkdir(parents=True, exist_ok=True)
    for f in files:
        (d / f).write_text("x", encoding="utf-8")


class DiscoveryTests(unittest.TestCase):
    def _corpus(self, root: Path) -> Path:
        papers = root / "papers"
        _mk(papers / "Norm_2020_A", "metadata.json", "notes.md")
        book = papers / "Geertz_1973_Interpretation"
        _mk(book, "metadata.json", "notes.md")
        _mk(book / "chapters" / "Geertz_1973_ThickDescription", "metadata.json", "notes.md")
        _mk(book / "chapters" / "Geertz_1973_DeepPlay", "metadata.json", "notes.md")
        _mk(papers / "tagged" / "ignore_me", "notes.md")  # tagged tree, skipped
        return papers

    def test_candidate_dirs_include_book_and_chapters_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            papers = self._corpus(Path(tmp))
            names = sorted(d.name for d in DISC.discover_metadata_dirs(papers))
            self.assertEqual(
                names,
                ["Geertz_1973_DeepPlay", "Geertz_1973_Interpretation",
                 "Geertz_1973_ThickDescription", "Norm_2020_A"],
            )

    def test_chapters_container_is_not_a_paper(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            papers = self._corpus(Path(tmp))
            names = [d.name for d in DISC.discover_metadata_dirs(papers)]
            self.assertNotIn("chapters", names)

    def test_book_not_double_counted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            papers = self._corpus(Path(tmp))
            dirs = DISC.discover_metadata_dirs(papers)
            self.assertEqual(len(dirs), 4)  # book + 2 chapters + 1 normal paper

    def test_tagged_tree_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            papers = self._corpus(Path(tmp))
            names = [d.name for d in DISC.discover_notes_dirs(papers)]
            self.assertNotIn("ignore_me", names)

    def test_relpath_is_posix_nested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            papers = self._corpus(Path(tmp))
            chapter = papers / "Geertz_1973_Interpretation" / "chapters" / "Geertz_1973_DeepPlay"
            self.assertEqual(DISC.relpath(chapter, papers), "Geertz_1973_Interpretation/chapters/Geertz_1973_DeepPlay")
            self.assertEqual(DISC.relpath(papers / "Norm_2020_A", papers), "Norm_2020_A")

    def test_chapterless_collection_matches_flat_glob(self) -> None:
        # Backward compatibility: with no chapters/, discovery == one-level dirs.
        with tempfile.TemporaryDirectory() as tmp:
            papers = Path(tmp) / "papers"
            _mk(papers / "A_2020_X", "metadata.json")
            _mk(papers / "B_2019_Y", "metadata.json")
            names = sorted(d.name for d in DISC.discover_metadata_dirs(papers))
            self.assertEqual(names, ["A_2020_X", "B_2019_Y"])


if __name__ == "__main__":
    unittest.main()
