"""Regression checks for the Year 4 offline audio resolver."""
import unittest
from pathlib import Path
import importlib.util

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("audio_resolver", HERE / "resolve_audio_assets.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class AudioResolverTests(unittest.TestCase):
    def test_verified_lessons(self):
        self.assertEqual(len(mod.resolve_lesson_audio(30)), 1)
        self.assertEqual(len(mod.resolve_lesson_audio(65)), 2)
        self.assertEqual(len(mod.resolve_lesson_audio(97)), 2)
        self.assertEqual(mod.resolve_lesson_audio("097")[0]["teacher_book_page"], 108)

    def test_cd1_cd2_track_29_not_confused(self):
        a = mod.resolve_lesson_audio(30)[0]
        b = mod.resolve_lesson_audio(105)[0]
        self.assertEqual((a["disc"], a["track"]), ("CD1", 29))
        self.assertEqual((b["disc"], b["track"]), ("CD2", 29))
        self.assertNotEqual(a["drive_file_id"], b["drive_file_id"])

    def test_track_21_reused_correctly(self):
        a = mod.resolve_lesson_audio(97)
        b = mod.resolve_lesson_audio(98)
        x = next(v for v in a if v["track"] == 21)
        y = next(v for v in b if v["track"] == 21)
        self.assertEqual(x["drive_file_id"], y["drive_file_id"])

    def test_teacher_book_page_provenance(self):
        import json
        mapping = json.loads((HERE / "QA_VERIFIED_LESSON_AUDIO_MAPPING_20261031.json").read_text(encoding="utf-8"))
        self.assertEqual(set(mapping["teacher_book_page_by_lesson"]), set(mapping["lessons"]))
        self.assertTrue(all(isinstance(page, int) and page > 0 for page in mapping["teacher_book_page_by_lesson"].values()))

    def test_all_manifest_ids_unique(self):
        import json
        manifest = json.loads((HERE / "QA_CLASS_CD_ASSET_MANIFEST_20261031.json").read_text(encoding="utf-8"))
        ids = [entry["file_id"] for disc in manifest["discs"].values() for entry in disc["tracks"].values()]
        self.assertEqual(len(ids), 220)
        self.assertEqual(len(set(ids)), 220)

    def test_all_mapped_audio_resolves(self):
        import json
        mapping = json.loads((HERE / "QA_VERIFIED_LESSON_AUDIO_MAPPING_20261031.json").read_text(encoding="utf-8"))
        self.assertEqual(len(mapping["lessons"]), 14)
        self.assertEqual(sum(len(v) for v in mapping["lessons"].values()), 20)
        for lesson, entries in mapping["lessons"].items():
            resolved = mod.resolve_lesson_audio(lesson)
            self.assertEqual([(v["disc"], v["track"]) for v in resolved],
                             [(v["disc"], v["track"]) for v in entries])

    def test_no_guessing_for_unverified(self):
        self.assertEqual(mod.resolve_lesson_audio(1), [])
        self.assertEqual(mod.resolve_lesson_audio(160), [])

    def test_bad_lesson_numbers(self):
        for value in (0, 161, None, "invalid", True, 97.5, "97.0", "-1", " 97 "):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    mod.resolve_lesson_audio(value)


if __name__ == "__main__":
    unittest.main()
