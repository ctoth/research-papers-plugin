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


BS = load_module("book_scaffold", SCRIPTS_DIR / "book_scaffold.py")


class ScaffoldChapterTests(unittest.TestCase):
    def test_scaffold_chapter_writes_book_chapter_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            book = Path(tmp) / "papers" / "Geertz_1973_Interpretation"
            book.mkdir(parents=True)
            d = BS.scaffold_chapter(book, "Geertz_1973_ThickDescription",
                                    {"title": "Thick Description", "year": "1973"})
            self.assertEqual(d, book / "chapters" / "Geertz_1973_ThickDescription")
            meta = json.loads((d / "metadata.json").read_text(encoding="utf-8"))
            self.assertEqual(list(meta.keys())[0], "cite_key")  # cite_key first (B5)
            self.assertEqual(meta["cite_key"], "Geertz_1973_ThickDescription")
            self.assertEqual(meta["document_type"], "book_chapter")
            self.assertEqual(meta["parent_book"], "Geertz_1973_Interpretation")
            self.assertEqual(meta["title"], "Thick Description")

    def test_scaffold_dir_equals_cite_key(self) -> None:
        # F4 invariant carries to chapters: the chapter dir name == its cite_key.
        with tempfile.TemporaryDirectory() as tmp:
            book = Path(tmp) / "papers" / "Book"
            book.mkdir(parents=True)
            d = BS.scaffold_chapter(book, "Author_2001_SomeChapter", {})
            self.assertEqual(d.name, "Author_2001_SomeChapter")


class SelectChaptersTests(unittest.TestCase):
    def test_defaults_to_all_when_no_topic(self) -> None:
        chapters = ["Ch1", "Ch2", "Ch3"]
        self.assertEqual(BS.select_chapters(chapters, topic=None), chapters)


class BookIndexTests(unittest.TestCase):
    def test_generate_book_index_links_each_chapter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            book = Path(tmp) / "papers" / "Geertz_1973_Interpretation"
            book.mkdir(parents=True)
            for key, desc in [("Geertz_1973_ThickDescription", "On thick description."),
                              ("Geertz_1973_DeepPlay", "On the Balinese cockfight.")]:
                d = BS.scaffold_chapter(book, key, {"title": key})
                (d / "description.md").write_text(f"---\ntags: []\n---\n{desc}\n", encoding="utf-8")
            index = BS.generate_book_index(book)
            self.assertIn("chapters/Geertz_1973_ThickDescription/notes.md", index)
            self.assertIn("chapters/Geertz_1973_DeepPlay/notes.md", index)
            self.assertIn("On the Balinese cockfight.", index)


if __name__ == "__main__":
    unittest.main()
