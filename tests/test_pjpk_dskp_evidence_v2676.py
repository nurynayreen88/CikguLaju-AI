import unittest
from pathlib import Path

from pjpk_dskp_evidence_v2676 import load_evidence, reconcile_sp_text


class TestPjpkDskpEvidenceV2676(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = load_evidence(Path(__file__).resolve().parents[1])

    def test_source_bundle_has_broad_six_year_coverage(self):
        self.assertGreaterEqual(len(self.evidence), 300)
        self.assertTrue(all(len([r for r in rows if r]) >= 1 for rows in self.evidence.values()))
        combos = {(year, subject) for year, subject, _ in self.evidence}
        self.assertEqual(len(combos), 12)

    def test_exact_year_subject_code_lookup(self):
        row = reconcile_sp_text(
            "Tahun 2", "Pendidikan Jasmani", "5.4.3",
            "Bekerjasama dalam kumpulan.", self.evidence
        )
        self.assertEqual(row["status"], "EXACT_TEXT_MATCH")
        self.assertEqual(row["dskp_text"], "Bekerjasama dalam kumpulan.")

    def test_conflicting_source_wording_fails_closed(self):
        row = reconcile_sp_text(
            "Tahun 3", "Pendidikan Kesihatan", "1.1.1",
            "Menyatakan anggota seksual.", self.evidence
        )
        self.assertEqual(row["status"], "CONFLICT_REVIEW")
        self.assertEqual(row["dskp_text"], "")

    def test_same_code_does_not_cross_year_or_subject(self):
        row = reconcile_sp_text(
            "Tahun 1", "Pendidikan Jasmani", "1.1.1",
            "any text", self.evidence
        )
        self.assertEqual(row["status"], "NO_DIRECT_DSKP_TEXT")

    def test_no_release_gate_or_database_mutation(self):
        self.assertTrue(all(
            r["source_status"] in {"DIRECT_DSKP_TEXT_TRANSCRIBED", "CONFLICT_REVIEW"}
            for rows in self.evidence.values() for r in rows
        ))


if __name__ == "__main__":
    unittest.main()
