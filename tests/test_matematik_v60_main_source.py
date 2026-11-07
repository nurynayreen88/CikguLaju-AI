"""Source-only regression: no production, DB or RPT integration."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from rph_standalone.matematik import v60_source_loader as source


class MatematikV60MainSource(unittest.TestCase):
    def test_585_independent_lesson_digests_and_shape(self):
        self.assertEqual(source.verify_all(), 585)
        for year in range(2, 7):
            docs = source.load_year(year)
            self.assertEqual(len(docs), 117)
            for number, text in enumerate(docs, 1):
                with self.subTest(year=year, lesson=number):
                    self.assertTrue(text.startswith(f"# RPH Matematik Tahun {year} — Lesson {number:03d}"))
                    self.assertIn("**SP:**", text)
                    self.assertIn("**Set induksi", text)
                    self.assertIn("**Objektif:**", text)
                    self.assertIn("**Penutup", text)
                    self.assertEqual(source.get_lesson(year, number), text)

    def test_manifest_is_exact_zip_source_and_holds_academic_release(self):
        m = source.manifest()
        self.assertEqual(m["source_archive_sha256"],
            "a641d7aff88b375f4786807a10eed384d9b6b22fea632d11ad9f2bc97fec5271")
        self.assertFalse(m["final_ready"])
        self.assertFalse(m["academic_signoff_complete"])
        self.assertFalse(m["production_modified"])
        self.assertEqual(sum(x["lessons"] for x in m["year_packs"].values()),585)

    def test_no_inplace_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "math_rph_v60"
            self.assertEqual(source.export_markdown(output), 585)
            self.assertEqual(len(list(output.glob("Tahun_*/*.md"))),585)
            self.assertEqual((output/"Tahun_4"/"lesson_014.md").read_text(),source.get_lesson(4,14))
            with self.assertRaises(FileExistsError):
                source.export_markdown(output)

    def test_invalid_inputs_rejected(self):
        for bad in (False, True, 0, 1, 7, 2.0, "2", None):
            with self.subTest(year=bad), self.assertRaises(ValueError):
                source.load_year(bad)
        for bad in (False, True, -1, 0, 118, 2.3, "1", None):
            with self.subTest(lesson=bad), self.assertRaises(ValueError):
                source.get_lesson(2, bad)

    def test_tampered_pack_is_fail_closed(self):
        original_root = source.ROOT
        try:
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)
                for file in original_root.iterdir():
                    (root/file.name).write_bytes(file.read_bytes())
                changed=root/"Tahun_4.json.zlib.b64.txt"
                changed.write_bytes(changed.read_bytes().replace(b"a",b"b",1))
                source.ROOT=root
                source.manifest.cache_clear(); source.load_year.cache_clear()
                with self.assertRaises(source.SourceIntegrityError):
                    source.load_year(4)
        finally:
            source.ROOT=original_root
            source.manifest.cache_clear(); source.load_year.cache_clear()


if __name__=="__main__":unittest.main()
