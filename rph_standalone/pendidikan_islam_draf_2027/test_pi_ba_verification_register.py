"""Workbook evidence ledger must not confuse PdPR hints with checked BA pages."""
from pathlib import Path
from tempfile import TemporaryDirectory
import csv
import unittest

from pi_ba_verification_register import register, save_csv, COLUMNS


class TestBookVerificationRegister(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = register()
        cls.rows = {row["lesson_id"]: row for row in cls.report["rows"]}

    def test_174_candidates_in_correct_books(self):
        r = self.report
        self.assertEqual(r["lesson_count"], 174)
        self.assertEqual(r["year_counts"], {2:76, 3:98})
        self.assertEqual(r["book_codes"], {"2":"BA102001","3":"BA103001"})
        self.assertEqual(r["secondary_hint_count"], 42)
        self.assertEqual(r["without_secondary_hints"], 132)
        self.assertEqual(r["contradiction_count"], 1)
        self.assertEqual(r["contradicted_lesson_ids"], ["T3-L004"])
        self.assertEqual(r["release"], "NO_GO")

    def test_secondhand_pages_not_verified_or_published(self):
        for r in self.rows.values():
            self.assertEqual(r["status"], "HOLD_AWAITING_ORIGINAL")
            self.assertIs(r["needs_direct_book_inspection"], True)
            self.assertIs(r["can_publish"], False)
            self.assertIs(r["can_redistribute_book_pdf"], False)
            self.assertEqual(r["original_book_printed_page"], "")
            self.assertEqual(r["original_exercise_number"], "")
            self.assertEqual(r["page_image_hash_sha256"], "")
            self.assertEqual(r["exercise_matches_sp_reviewed_by"], "")
            self.assertIs(r["a4_word_pdf_verified"], False)
        self.assertEqual(self.rows["T3-L097"]["secondary_reported_pages"], "35")
        self.assertEqual(self.rows["T3-L068"]["secondary_reported_pages"], "52")
        self.assertEqual(self.rows["T3-L004"]["secondary_conflict"], True)
        self.assertEqual(self.rows["T3-L004"]["original_book_printed_page"], "")
        self.assertEqual(self.rows["T2-L042"]["book_code_KPM"], "BA102001")


    def test_persistent_editor_csv_has_174_records_and_source_urls(self):
        path = Path(__file__).parent / "PI_BA_REVIEW_REGISTER_174_STAGING.csv"
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 174)
        index = {r["Lesson"]:r for r in rows}
        self.assertEqual(set(index), set(self.rows))
        self.assertEqual(sum(bool(r["Sumber bukti asal"]) for r in rows), 42)
        for row in rows:
            ref = self.rows[row["Lesson"]]
            self.assertEqual(row["Kod Buku Aktiviti KPM"], ref["book_code_KPM"])
            self.assertEqual(row["Tahun"], str(ref["year"]))
            self.assertEqual(row["Status"], "HOLD")
            self.assertEqual(row["Halaman bercetak diperiksa"], "")
            self.assertEqual(row["Arahan latihan diperiksa"], "")
            self.assertEqual(row["Pengesah"], "")
            self.assertEqual(bool(row["Sumber bukti asal"]),bool(ref["secondary_source_count"]))
        self.assertIn("Konflik", index["T3-L004"]["Nota"])
        self.assertTrue(index["T3-L097"]["Sumber bukti asal"].startswith("https://"))

    def test_csv_written_with_stable_columns(self):
        with TemporaryDirectory() as tmp:
            dest = Path(tmp)/"BA_174_review.csv"
            save_csv(dest, self.report)
            content = dest.read_text(encoding="utf-8-sig")
            self.assertIn("book_code_KPM", content)
            with dest.open("r", encoding="utf-8-sig", newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows),174)
            self.assertEqual(list(rows[0]),COLUMNS)
            self.assertEqual(rows[0]["can_publish"],"False")
            self.assertEqual(rows[-1]["can_publish"],"False")


if __name__ == "__main__":
    unittest.main()
