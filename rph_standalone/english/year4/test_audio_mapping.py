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

    def test_no_guessing_for_unverified(self):
        self.assertEqual(mod.resolve_lesson_audio(1), [])
        self.assertEqual(mod.resolve_lesson_audio(160), [])

    def test_bad_lesson_numbers(self):
        for value in (0, 161, None, "invalid", True):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    mod.resolve_lesson_audio(value)


if __name__ == "__main__":
    unittest.main()
