"""Official year5 SP-code coverage vs legacy: fail closed, never grant READY."""
import unittest
from tools.audit_sains_y5_kssr2017_content_kps_20261107 import checked
from tools.render_sains_y5_83_rph_draf_20261107 import kps_for
from web.sains_y5_83_activity_bank_draf_20261107 import BANK


class TestYear5KSSR2017Coverage(unittest.TestCase):
    def test_all_83_official_content_sp_and_12_kps_explicitly_mapped(self):
        report=checked()
        self.assertEqual(report["official_unique_sp_total"],95)
        self.assertEqual(report["official_content_sp_total"],83)
        self.assertEqual(report["official_science_process_sp_total"],12)
        self.assertEqual(report["stage_content_sp_exact_numeric_membership"],83)
        self.assertEqual(report["stage_extra_or_missing_content_sp"],0)
        self.assertEqual(report["kps_codes_referenced_in_staged_rph"],12)
        self.assertEqual(len(report["kps_to_proposed_pdp"]),12)
        self.assertTrue(all(report["kps_to_proposed_pdp"].values()))
        self.assertEqual(report["release_status"],"STAGING_HOLD")
        self.assertFalse(report["ready_for_runtime"])
        self.assertFalse(report["db_modified"])
        self.assertIsNone(report["academic_quality_percent"])
        self.assertEqual(report["pedagogical_and_pbd_teacher_approval_count"],0)

    def test_extra_kps_have_actual_lesson_evidence(self):
        self.assertIn("1.1.11 Membuat hipotesis",kps_for("5.2.4"))
        self.assertIn("hipotesis",BANK["5.2.4"]["pupil1"].lower())
        self.assertIn("1.1.9 Mendefinisi secara operasi",kps_for("7.1.3"))
        self.assertIn("lapisan perang",BANK["7.1.3"]["pupil2"].lower())
        self.assertIn("1.1.5 Meramal",kps_for("7.1.3"))
        self.assertIn("meramal",BANK["7.1.3"]["pupil1"].lower())
        self.assertIn("1.1.7 Menggunakan perhubungan ruang dan masa",kps_for("9.1.2"))
        self.assertIn("putaran",BANK["9.1.2"]["teacher1"].lower())

    def test_no_legacy_year5_sk_promoted(self):
        self.assertFalse(any(sp.startswith(("6.2.","10.2.")) for sp in BANK))
        report=checked()
        self.assertEqual(report["full_sp_statement_semantic_validation"],"PENDING")
        self.assertEqual(report["kps_implementation_teacher_validation"],"PENDING")


if __name__=="__main__":
    unittest.main()
