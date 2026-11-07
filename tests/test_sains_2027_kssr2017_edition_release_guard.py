"""Independent official-KPM-code check must block legacy Sains release."""
import unittest
from rpt_2027.common.sains_kssr2017_edition_release_guard import edition_conflict,require_verified_kssr2017_sains

class SainsKSSR2017EditionReleaseGuard(unittest.TestCase):
    def test_source_contradiction_never_becomes_final_ready(self):
        d=edition_conflict()
        self.assertFalse(d["academic_release_ready"])
        self.assertFalse(d["ready_for_web_telegram"])
        self.assertTrue(d["no_auto_remap"])
        self.assertEqual(d["requires_full_reverification_years"],[4,5,6])
        self.assertEqual(len(d["conflict_samples"]),6)
        self.assertTrue(d["y2_y3_not_exonerated_by_this_sample"])
        for y in range(2,7):
            with self.subTest(year=y), self.assertRaises(ValueError):
                require_verified_kssr2017_sains(y)
    def test_legacy_internal_coverage_is_not_external_dskp_verification(self):
        d=edition_conflict()
        text=d["meaning"]
        self.assertIn("422/342",text)
        self.assertIn("does not independently prove",text)
        self.assertEqual(d["production_changes"],0)

if __name__=="__main__":
    unittest.main()
