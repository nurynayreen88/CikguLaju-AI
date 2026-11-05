"""Year4 L29 CLIL audio source: TB p193 is CD3, not legacy CD1.

Read-only safety audit: this does NOT approve or send any audio.
"""
import ast
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
LESSON=ROOT/"rph_standalone/english/year4/lesson_029.md"
APP=ROOT/"app.py"
SRC_IDS={"1RNYuEKqaS5YZ9e4TDpnCH73I0scaPVIC",
         "1VVehPZAvRph_YUTfbBglELLBkFOx9e3J"}

class Lesson29ClilSourceAudit(unittest.TestCase):
    def test_teacher_book_193_correct_disc_and_source_scope(self):
        text=LESSON.read_text(encoding="utf-8")
        self.assertIn("SB p.129",text)
        self.assertIn("TB p.193",text)
        self.assertIn("CD3 Track 35 (Vocabulary)",text)
        self.assertIn("CD3 Track 36 (Activity 1)",text)
        self.assertIn("CD3 Tracks 35/36",text)
        self.assertIn("NOT READY FOR AUDIO RELEASE",text)
        self.assertIn("legacy Telegram maps wrongly label both as CD1",text)
        for fid in SRC_IDS:
            self.assertIn(fid,text)
        self.assertNotIn("CD1 designation requires independent",text)

    def test_legacy_y4_l29_routes_are_documented_not_approved(self):
        tree=ast.parse(APP.read_text(encoding="utf-8"),filename=str(APP))
        maps={}
        for node in tree.body:
            if not isinstance(node,ast.Assign):
                continue
            for target in node.targets:
                if isinstance(target,ast.Name) and target.id in (
                    "_EN4_AUDIO_ALL_V25257","_EN4_AUDIO_ALL_V25258",
                    "_EN4_AUDIO_ALL_V25259",
                ):
                    maps[target.id]=ast.literal_eval(node.value)
        self.assertEqual(len(maps),3)
        for label, mapping in maps.items():
            with self.subTest(map=label):
                entries=mapping.get(29) or mapping.get("29") or []
                self.assertEqual(
                    {r["audio_reference"] for r in entries},
                    {"CD1 Track 35","CD1 Track 36"})
                self.assertFalse(any(
                    r["storage_file_id"] in SRC_IDS for r in entries))
        # The wrong CD1 route remains an uncorrected production legacy map.
        # A subsequent isolated guarded callback patch is required before
        # releasing native audio; this source audit must not fake that work.

if __name__=="__main__":
    unittest.main()
