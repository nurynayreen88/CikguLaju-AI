import unittest
from rpt_pj_2027_release_policy import calendar_release_status


class TestReleasePolicy(unittest.TestCase):
    def test_verified_release_with_legacy_labels(self):
        records = {i: {"Status PdP Dikira": "BELUM AUDIT"} for i in range(5840)}
        audit = [["KEPUTUSAN AUDIT AKHIR", "FINAL VERIFIED - KPM/BKPP"]]
        release = [["Penerbitan", "FINAL VERIFIED - KPM/BKPP"]]
        result = calendar_release_status(records, audit, release)
        self.assertTrue(result["approved"])
        self.assertEqual(result["legacy_label_count"], 5840)

    def test_missing_release_evidence(self):
        records = {i: {"Status PdP Dikira": "CALON PDP"} for i in range(5840)}
        self.assertFalse(calendar_release_status(records, [], [])["approved"])


if __name__ == "__main__":
    unittest.main()
