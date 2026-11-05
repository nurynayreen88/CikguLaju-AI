"""Source-specific QA: Year4 Lesson29 printed-reading plan is usable with audio held.

This does not approve actual CD3 media content or Telegram sending; the
existing Year4 wrong-book guard must continue to stop legacy CD1 routes.
No app import, DB, users, credits, network, or original audio changes.
"""
import unittest
from pathlib import Path
from types import SimpleNamespace

from web.english_y4_wrong_book_audio_hold_20261105 import HOLD_LESSONS, install

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "rph_standalone" / "english" / "year4" / "lesson_029.md"

class EnglishYear4L29PrintedReading(unittest.TestCase):
    def test_true_teacher_book_disc_and_printed_reading_instructions(self):
        text = SOURCE.read_text(encoding="utf-8")
        for anchor in (
            "SB p.129", "TB p.193",
            "Class CD3 Track 35 (Vocabulary)",
            "Class CD3 Track 36 (Activity 1)",
            "printed school texts",
            "Reading 3.2.2", "Reading 3.2.4",
            "READY FOR PRINTED-TEXT READING PRACTICE",
            "final teacher approval pending",
            "HOLD FOR AUDIO RELEASE",
            "1RNYuEKqaS5YZ9e4TDpnCH73I0scaPVIC",
            "1VVehPZAvRph_YUTfbBglELLBkFOx9e3J",
        ):
            self.assertIn(anchor, text)
        self.assertNotIn("CD1 designation requires independent", text)
        self.assertIn("do not play or send either recording", text)
        self.assertIn("do not claim the unverified CD3 recording has been heard", text)
        self.assertNotIn("FINAL READY", text)
        self.assertIn(29, HOLD_LESSONS)

    def test_existing_live_provenance_guard_blocks_l29_media_only(self):
        forwarded = []
        notices = []
        def available(state):
            state["audio_storage_file_id"] = "LEGACY_SUPER_MINDS1_CD1_35"
            return ["media", "rph", "rph_word", "textbook"]
        def send(cid, state, key):
            forwarded.append((cid, key))
            return True
        rt = SimpleNamespace(
            _available_materials_v2528=available,
            _send_reference_material_v2528=send,
            _send_reference_material=send,
            send=lambda cid, message: notices.append((cid, message)),
        )
        self.assertTrue(install(rt))
        selection = {"subject": "English", "year": "Year 4", "lesson_no": "029"}
        self.assertNotIn("media", rt._available_materials_v2528(selection))
        self.assertNotIn("audio_storage_file_id", selection)
        self.assertFalse(rt._send_reference_material_v2528(42, selection, "media"))
        self.assertFalse(rt._send_reference_material(42, selection, "media"))
        self.assertEqual(len(notices), 2)
        self.assertEqual(forwarded, [])
        self.assertTrue(rt._send_reference_material_v2528(42, selection, "rph_word"))
        self.assertTrue(rt._send_reference_material_v2528(42, selection, "rph"))
        self.assertEqual([x[1] for x in forwarded], ["rph_word", "rph"])
        other = {"subject": "English", "year": "Year 2", "lesson_no": 29}
        self.assertIn("media", rt._available_materials_v2528(other))
        self.assertTrue(rt._send_reference_material(42, other, "media"))

if __name__ == "__main__":
    unittest.main()
