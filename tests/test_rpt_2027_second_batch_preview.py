"""Source-identity and PDF guards for 8 further RPT 2027 STAGING previews."""
import re
import tempfile
import unittest

from pypdf import PdfReader

from rpt_2027.common.format_2026_layout_preview import validate_rows
from scripts.build_rpt_2027_second_batch_preview import (
    build_all, pjpk_records, sejarah_records, SUBJECT_ROW_COUNTS
)


class RPT2027SecondBatchQA(unittest.TestCase):
    def test_sejarah_source_and_status(self):
        for year in (4, 5, 6):
            with self.subTest(year=year):
                rows = sejarah_records(year)
                self.assertEqual(len(rows), 36)
                self.assertTrue(validate_rows("sejarah", year, rows))
                self.assertTrue(all(r["sk"] and r["sp"] and r["a_start"] and r["b_start"]
                                    for r in rows))
                self.assertEqual([r["id"] for r in rows],
                                 [f"{i:03d}" for i in range(1, 37)])
                self.assertTrue(all("bukan halaman aktiviti disahkan" in r["note"]
                                    for r in rows))

    def test_pjpk_source_identity_preserved(self):
        for year in range(2, 7):
            with self.subTest(year=year):
                rows = pjpk_records(year)
                expected = SUBJECT_ROW_COUNTS["PJ"][year] + SUBJECT_ROW_COUNTS["PK"][year]
                self.assertEqual(len(rows), expected)
                self.assertTrue(validate_rows("pjpk", year, rows))
                self.assertEqual(sum(r["display_id"].startswith("PJ PdP") for r in rows),
                                 SUBJECT_ROW_COUNTS["PJ"][year])
                self.assertEqual(sum(r["display_id"].startswith("PK PdP") for r in rows),
                                 SUBJECT_ROW_COUNTS["PK"][year])
                self.assertIn("PJ PdP 001", [r["display_id"] for r in rows])
                self.assertIn("PK PdP 001", [r["display_id"] for r in rows])
                self.assertTrue(all(r["week"].endswith("(cadangan)") for r in rows))
                self.assertTrue(all(r["sk"] and r["sp"] for r in rows))

    def test_reject_duplicate_display_identity(self):
        rows = pjpk_records(2)
        rows[1]["display_id"] = rows[0]["display_id"]
        with self.assertRaises(ValueError):
            validate_rows("pjpk", 2, rows)

    def test_eight_pdf_previews_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            built = build_all(tmp)
            self.assertEqual(len(built), 8)
            self.assertEqual({(s, y) for s, y, _, _ in built},
                             {("sejarah", y) for y in range(4, 7)} |
                             {("pjpk", y) for y in range(2, 7)})
            for subject, year, count, pdf_path in built:
                with self.subTest(subject=subject, year=year):
                    reader = PdfReader(str(pdf_path))
                    self.assertGreaterEqual(len(reader.pages), 2)
                    self.assertGreater(pdf_path.stat().st_size, 8000)
                    self.assertTrue(all(float(page.mediabox.width) >
                                        float(page.mediabox.height)
                                        for page in reader.pages))
                    body = "\n".join(page.extract_text() for page in reader.pages[1:])
                    self.assertIn("MINGGU / TARIKH", body)
                    self.assertIn("CATATAN / BAHAN", body)
                    if subject == "sejarah":
                        self.assertEqual(count, 36)
                        numbers = re.findall(r"(?m)^\\s*PdP\\s+(\\d{3})\\s*$", body)
                        self.assertEqual(numbers, [f"{n:03d}" for n in range(1, 37)])
                    else:
                        for sub in ("PJ", "PK"):
                            ids = re.findall(r"(?m)^\\s*" + sub +
                                             r" PdP\\s+(\\d{3})\\s*$", body)
                            self.assertEqual(ids, [
                                f"{n:03d}" for n in range(1, SUBJECT_ROW_COUNTS[sub][year]+1)
                            ])
                    self.assertIn("DRAF", reader.pages[0].extract_text())


if __name__ == "__main__":
    unittest.main()
