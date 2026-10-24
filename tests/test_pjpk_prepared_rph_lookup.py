"""Current editorial records must never leak through the production lookup."""
import unittest
from scripts.pjpk_prepared_rph_lookup import prepared_rph

class PreparedRPHLookupTests(unittest.TestCase):
    def setUp(self):
        self.ready = dict(id=2259, year_label="Tahun 5", subject="Pendidikan Kesihatan",
                          topic="Pencegahan Penyakit Berjangkit", content_verified=1,
                          sequence_verified=1, schedule_verified=1)
    def test_all_three_staging_records_blocked_even_with_ready_row(self):
        for ident, topic in ((2259, "Pencegahan Penyakit Berjangkit"),
                             (2260, "Pengaruh Rakan Sebaya"),
                             (2261, "Nutrien dan Label Makanan")):
            with self.subTest(ident=ident):
                row = dict(self.ready, id=ident, topic=topic)
                self.assertIsNone(prepared_rph(ident, row))
    def test_missing_verified_standards_blocks(self):
        self.assertIsNone(prepared_rph(2259, self.ready))
    def test_unverified_standard_blocks(self):
        row = dict(self.ready, _std=[
            dict(standard_type="SK", standard_code="6.1", verified=0),
            dict(standard_type="SP", standard_code="6.1.1", verified=1),
            dict(standard_type="SP", standard_code="6.1.2", verified=1)])
        self.assertIsNone(prepared_rph(2259, row))
    def test_mismatched_standard_blocks(self):
        row = dict(self.ready, _std=[
            dict(standard_type="SK", standard_code="6.1", verified=1),
            dict(standard_type="SP", standard_code="6.1.1", verified=1),
            dict(standard_type="SP", standard_code="6.1.9", verified=1)])
        self.assertIsNone(prepared_rph(2259, row))
    def test_no_ready_row_blocks(self):
        self.assertIsNone(prepared_rph(2259))
    def test_wrong_id_blocks(self):
        self.assertIsNone(prepared_rph(2260, self.ready))
    def test_unverified_schedule_blocks(self):
        self.assertIsNone(prepared_rph(2259, dict(self.ready, schedule_verified=0)))
    def test_unexpected_id_blocks(self):
        self.assertIsNone(prepared_rph(9999, dict(self.ready, id=9999)))
    def test_boolean_id_blocks(self):
        self.assertIsNone(prepared_rph(True, dict(self.ready, id=True)))

if __name__ == "__main__":
    unittest.main()
