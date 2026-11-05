"""English Year 1–6 official SOW/audio provenance regression, source-only.

No Telegram app imports, database reads/writes, file transmissions or
teacher-pedagogical approvals. Do not turn metadata checks into a claim
that the recording has been listened to or delivered.
"""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
INDEX=json.loads((ROOT/"audits/english_y1_y6_960_sow_audio_index_20261105.json").read_text(encoding="utf-8"))
RISKS=json.loads((ROOT/"audits/english_y1_y6_audio_source_risk_register_20261105.json").read_text(encoding="utf-8"))
COUNT_EXPLICIT={1:0,2:0,3:0,4:65,5:62,6:7}
COUNT_REFS={1:0,2:0,3:0,4:85,5:87,6:7}

class EnglishPrimaryAllYearsSourceAudioAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.years={int(v["year"]):v for v in INDEX["years"]}

    def test_each_year_has_exactly_160_sow_lessons(self):
        self.assertEqual(set(self.years),set(range(1,7)))
        self.assertEqual(sum(y["lesson_count"] for y in self.years.values()),960)
        for year,y in self.years.items():
            with self.subTest(year=year):
                self.assertEqual(y["lesson_count"],160)
                self.assertEqual(len(y["entries"]),160)
                self.assertEqual({l["lesson"] for l in y["entries"]},set(range(1,161)))
                self.assertEqual(y["lessons_with_explicit_audio_refs"],
                                 COUNT_EXPLICIT[year])
                self.assertEqual(y["explicit_ref_count"],COUNT_REFS[year])
                self.assertTrue(all(l["classification"] in (
                    "SOW_EXPLICIT_AUDIO_REFERENCE",
                    "SOW_AUDIO_DISCUSSION_WITHOUT_PARSEABLE_NUMBER",
                    "SOW_NO_EXPLICIT_AUDIO_REFERENCE_NOT_NO_AUDIO") for l in y["entries"]))
                self.assertTrue("SOW" in y["source"]["title"].upper() or "SCHEME OF WORK" in y["source"]["title"].upper())

    def test_year1_to_3_sow_silent_does_not_conclude_no_audio(self):
        for year in (1,2,3):
            y=self.years[year]
            self.assertEqual(y["explicit_ref_count"],0)
            self.assertTrue(all(l["classification"]!="NO_AUDIO" for l in y["entries"]))
        self.assertIn("KP2027", " ".join(INDEX["key_warnings"]))

    def test_year4_printed_conflicts_remain_visible(self):
        rows={l["lesson"]:l for l in self.years[4]["entries"]}
        self.assertEqual([(r["disc_or_audio_volume"],r["track"])
                          for r in rows[29]["sow_explicit_audio_references"]],
                         [(None,35),(None,36)])
        self.assertEqual([(r["disc_or_audio_volume"],r["track"])
                          for r in rows[30]["sow_explicit_audio_references"]],[(2,29)])
        self.assertEqual([r["track"] for r in rows[103]["sow_explicit_audio_references"]],[26])
        self.assertEqual([r["track"] for r in rows[104]["sow_explicit_audio_references"]],[27,28])

    def test_year5_and_6_distinct_audio_notation_and_sample_routes(self):
        y5={l["lesson"]:l for l in self.years[5]["entries"]}
        y6={l["lesson"]:l for l in self.years[6]["entries"]}
        self.assertEqual([(r["disc_or_audio_volume"],r["track"])
                          for r in y5[29]["sow_explicit_audio_references"]],[(3,2),(3,3)])
        self.assertEqual([(r["disc_or_audio_volume"],r["track"])
                          for r in y5[30]["sow_explicit_audio_references"]],[(3,4)])
        self.assertEqual([(r["disc_or_audio_volume"],r["track"])
                          for r in y6[89]["sow_explicit_audio_references"]],[(1,28)])
        self.assertEqual([(r["disc_or_audio_volume"],r["track"])
                          for r in y6[93]["sow_explicit_audio_references"]],[(1,29)])
        self.assertEqual([(r["disc_or_audio_volume"],r["track"])
                          for r in y6[99]["sow_explicit_audio_references"]],[(2,2)])

    def test_wrong_textbook_roots_are_not_silently_approved(self):
        issues={v["id"]:v for v in RISKS["confirmed_risks"]}
        self.assertEqual(RISKS["release_status"],
                         "AUDIT_STAGING_ONLY_NO_TELEGRAM_OR_PRODUCTION_APPROVAL")
        self.assertEqual(len(issues),8)
        w=issues["Y4_WRONG_BOOK_24"]
        self.assertIn("24/24 WMA",w["exact_issue"])
        self.assertEqual(set(w["source_folder_ids"]),{
            "1tbbr7hbvZfbF3ZhxpIIdMAnLBR_MZS50",
            "1EQxVxNqvyg-dKi_pLTtEomOFwuUTC-cv"})
        self.assertEqual(w["status"],
                         "SOURCE_BOOK_IDENTITY_CONFIRMED_AUDIO_CONTENT_AND_TELEGRAM_SEND_UNVERIFIED")
        y6=issues["Y6_AS5_FOLDER_MISMATCH"]
        self.assertIn("AS5_Uxx",y6["exact_issue"])
        self.assertEqual(y6["status"],"SOURCE_LABEL_MISMATCH_NOT_PROOF_OF_BOT_WRONG_SEND")
        y5=issues["Y5_TRACKS_FOUND_NOT_PLAYED"]
        self.assertEqual(len(y5["source_ids"]),3)
        self.assertNotIn("FINAL_READY",str(RISKS))

    def test_zero_claims_of_real_playback_or_live_telegram(self):
        self.assertIn("not 960/960",RISKS["limitations"][0])
        for source in RISKS["reviewed_book_sources"]:
            self.assertNotIn("FULL_TB_SB_AUDIO_VERIFIED",source["audit_level"])
        self.assertTrue(all("SOW_MENTION_ONLY_NOT_TB_AUDIO_PLAYBACK"
                            ==ref["verified_level"]
                            for y in self.years.values() for l in y["entries"]
                            for ref in l["sow_explicit_audio_references"]))

if __name__=="__main__":
    unittest.main()
