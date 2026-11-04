"""Non-destructive English 2026-11-04 RPH delta gate.

Reuses existing full 960-file text audit; verifies only source-tested fixes,
not book-audio playback, teacher signoff, Telegram credentials, payment or
production deployment. Year1 KP2027 is excluded from Year2–6 hard gates.
"""
import unittest

from tools.audit_english_800_text_quality_20261104 import audit

class CurrentEnglishMaturityDelta(unittest.TestCase):
    def test_no_regression_of_recently_corrected_800_sources(self):
        r=audit()
        self.assertEqual(r["total_year2_6"],800)
        self.assertEqual(r["hard_issue_occurrences"],0)
        years={int(y):v["summary"] for y,v in r["years"].items()}
        for y in range(2,7):
            self.assertEqual(years[y]["files"],160)
            self.assertEqual(years[y]["sow_matched"],years[y]["fixed_sow"])
            self.assertEqual(years[y]["hard_issue_lessons"],{})
        self.assertEqual(years[2]["quality_flag_lessons"].get(
            "stale_sow_verification_pending_header",[]),[])
        self.assertEqual(years[3]["quality_flag_lessons"].get(
            "generic_instruction",[]),[])
        self.assertEqual(years[5]["quality_flag_lessons"].get(
            "phase_minutes_not_extractable",[]),[])
        self.assertEqual(years[5]["timing60"],160)
        for n in (1,2,3,4,6,7,8,9,11,12,13,14):
            self.assertNotIn(n, years[6]["quality_flag_lessons"].get(
                "generic_instruction",[]))
        self.assertEqual(years[4]["teacher_choice"],10)
        self.assertEqual(years[5]["teacher_choice"],9)
        self.assertEqual(years[6]["teacher_choice"],14)
        self.assertFalse(r["final_pedagogy_verified"])
        self.assertFalse(r["real_telegram_delivery_verified"])
        self.assertFalse(r["spoken_audio_verified"])
if __name__=="__main__":
    unittest.main()
