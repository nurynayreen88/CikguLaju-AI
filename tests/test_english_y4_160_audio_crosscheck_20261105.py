"""Independent offline regression for 160 Year 4 SOW lesson/audio audit.

Audit source: KPM Year 4 SOW PDF and five authenticated Drive source
folders, captured 2026-11-05 in audits/*.json. CI cannot verify audio
speech, availability to a Telegram user, or unreviewed TB pages.
NO production hooks, DB writes, credits or live sends.
"""
import ast
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
INDEX=json.loads((ROOT/"audits/english_y4_sow_160_audio_index_20261105.json").read_text(encoding="utf-8"))
AUDIT=json.loads((ROOT/"audits/english_y4_160_audio_drive_crosscheck_20261105.json").read_text(encoding="utf-8"))
APP=ROOT/"app.py"

class AllYear4AudioAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lessons={int(x["lesson"]):x for x in AUDIT["lessons"]}
        cls.source={int(x["lesson"]):x for x in INDEX["entries"]}

    def test_all_160_lesson_sources_are_present_exactly_once(self):
        self.assertEqual(set(self.lessons),set(range(1,161)))
        self.assertEqual(set(self.source),set(range(1,161)))
        self.assertEqual(len(list((ROOT/"rph_standalone/english/year4").glob("lesson_???.md"))),160)
        for n in range(1,161):
            self.assertEqual(self.source[n]["sow_track_references"],
                             self.lessons[n]["sow_track_references"])
            self.assertIn("Scheme of Work",self.source[n]["source"])

    def test_legacy_map_matches_actual_app_and_is_not_auto_approved(self):
        tree=ast.parse(APP.read_text(encoding="utf-8"))
        names={"_EN4_AUDIO_ALL_V25259"}
        mapping=None
        for node in tree.body:
            if isinstance(node,ast.Assign) and any(
                isinstance(target,ast.Name) and target.id in names
                for target in node.targets):
                mapping=ast.literal_eval(node.value)
        self.assertIsNotNone(mapping)
        report=self.lessons
        for n in range(1,161):
            saved=report[n]["legacy_audio"]
            actual=mapping.get(n) or mapping.get(str(n)) or []
            self.assertEqual(len(saved),len(actual),(n,"route count mismatch"))
            for row,old in zip(saved,actual):
                self.assertEqual(
                    (row["legacy_file_id"],row["declared_disc"],row["declared_track"]),
                    (old["storage_file_id"],
                     int(old["audio_reference"].split("Track")[0].strip().replace("CD","")),
                     int(old["audio_reference"].split("Track")[1].strip())),n)
                self.assertIn(row["classification"],(
                    "REVIEW_OR_HOLD","SOW_AND_ASSET_LABEL_ONLY_NOT_SPEECH_VERIFIED"))
        self.assertEqual(AUDIT["status"],"AUDIT_ONLY_NOT_RELEASE_APPROVAL")

    def test_sow_audio_gap_and_known_tb_mismatches_are_visible(self):
        cov=AUDIT["coverage"]
        self.assertEqual((cov["sow_lessons"],cov["sow_lessons_mentioning_tracks"]),(160,65))
        self.assertEqual((cov["legacy_map_v25259_lessons"],
                          cov["legacy_map_v25259_audio_references"]),(56,69))
        self.assertEqual(set(x["lesson"] for x in
            AUDIT["missing_legacy_media_for_sow_audio_lessons"]),
            {13,20,65,66,68,70,76,104,139})
        l29=self.lessons[29]["legacy_audio"]
        self.assertEqual(len(l29),2)
        for a in l29:
            self.assertIn("TB_P193_CONFIRMS_CD3_NOT_CD1",a["flags"])
            self.assertEqual(a["drive_inventory"]["format"],"WMA")
        l30=self.lessons[30]["legacy_audio"]
        self.assertEqual(len(l30),1)
        self.assertIn("TB_P39_AND_USER_CONFIRM_CD1_NOT_CD2",l30[0]["flags"])
        self.assertEqual(self.source[30]["sow_track_references"][0]["disc"],2)
        self.assertEqual([a["declared_track"] for a in
                          self.lessons[103]["legacy_audio"]],[26,27,28])
        self.assertEqual([a["track"] for a in
                          self.source[104]["sow_track_references"]],[27,28])
        self.assertEqual(len(self.lessons[104]["legacy_audio"]),0)

    def test_source_format_is_not_falsely_treated_as_mp3(self):
        all_rows=[x for l in self.lessons.values() for x in l["legacy_audio"]]
        self.assertEqual(len(all_rows),69)
        self.assertEqual(sum(r["drive_inventory"]["format"]=="WMA" for r in all_rows),24)
        self.assertEqual(sum(r["drive_inventory"]["format"]=="MP3" for r in all_rows),45)
        self.assertEqual(AUDIT["coverage"]["matched_drive_refs"],69)
        self.assertEqual(AUDIT["coverage"]["legacy_wma_refs"],24)
        self.assertEqual(AUDIT["coverage"]["legacy_mp3_refs"],45)
        for row in all_rows:
            self.assertEqual(row["drive_inventory"]["disc"],"CD"+str(row["declared_disc"]))
            self.assertEqual(row["drive_inventory"]["track"],row["declared_track"])
            if row["drive_inventory"]["format"]=="WMA":
                self.assertIn("WMA_SOURCE_WITH_LEGACY_MP3_SENDER",row["flags"])
        self.assertIn('suffix=".mp3"',APP.read_text(encoding="utf-8"))
        self.assertFalse(any(r["classification"]=="FINAL_READY" for r in all_rows))

    def test_wma_mp3_candidates_are_not_deployed_or_trusted_without_tb_and_delivery(self):
        d=json.loads((ROOT/"audits/english_y4_legacy_wma_to_mp3_candidates_20261105.json").read_text(encoding="utf-8"))
        self.assertEqual(d["status"],"CANDIDATE_ONLY_NO_RUNTIME_USE")
        self.assertEqual(d["counts"]["wma_route_rows"],24)
        self.assertEqual(d["counts"]["canonical_mp3_candidate_found"],24)
        self.assertEqual(d["counts"]["block_wrong_disc_l29"],2)
        self.assertEqual(d["counts"]["block_wrong_lesson_l103"],2)
        self.assertEqual(d["counts"]["source_format_candidates"],20)
        candidate_ids={e["old_drive_id"] for e in d["candidates"]}
        actual_ids={e["legacy_file_id"]
                    for x in self.lessons.values() for e in x["legacy_audio"]
                    if e["drive_inventory"]["format"]=="WMA"}
        self.assertEqual(candidate_ids,actual_ids)
        self.assertTrue(all(e["mp3_candidate"]["name"].endswith(".mp3")
                            and "NOT_APPROVED" in e["classification"]
                            or e["classification"].startswith("BLOCK_")
                            for e in d["candidates"]))
        self.assertTrue(all(not row["delivery_verified"] for row in d["known_direct_tb_paths"]))

if __name__=="__main__":
    unittest.main()
