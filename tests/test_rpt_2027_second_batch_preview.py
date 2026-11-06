"""Source-identity and PDF guards for 8 further RPT 2027 STAGING previews."""
import re
import tempfile
import unittest

from pypdf import PdfReader

from rpt_2027.common.format_2026_layout_preview import validate_rows, week_merge_ranges
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
                self.assertTrue(all(r["week"] == "Agihan cadangan" for r in rows))
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
                self.assertTrue(all("BT m/s Rujuk DSKP" not in r["note"] for r in rows))

    def test_merge_week_cell_only_when_week_and_dates_match(self):
        rows = pjpk_records(3)
        spans = week_merge_ranges(rows)
        self.assertEqual(sum(end - start + 1 for start, end in spans), len(rows))
        self.assertTrue(any(end > start for start, end in spans))
        for start, end in spans:
            members = rows[start - 1:end]
            if end > start:
                self.assertEqual(len({r["week"] for r in members}), 1)
                for field in ("a_start", "a_end", "b_start", "b_end"):
                    self.assertEqual(len({r[field] for r in members}), 1)
        # RBT records have no confirmed week: never coalesce all 32 PdP.
        from scripts.build_rpt_2027_standard_preview import rbt_records
        self.assertTrue(all(a == b for a, b in week_merge_ranges(rbt_records(4))))
        # A repeated week number with different dates may not be merged.
        example = [dict(rows[0]), dict(rows[1])]
        example[1]["week"] = example[0]["week"]
        example[1]["a_start"] = "2027-12-01"
        self.assertEqual(week_merge_ranges(example), [(1, 1), (2, 2)])

    def test_single_week_label_for_multi_lesson_group(self):
        from rpt_2027.common.format_2026_layout_preview import build_preview
        records = pjpk_records(3)
        start, end = next((a, b) for a, b in week_merge_ranges(records) if b > a)
        with tempfile.TemporaryDirectory() as temp:
            target = __import__("pathlib").Path(temp) / "week_merge.pdf"
            build_preview("pjpk", 3, records, target)
            text = "\n".join(page.extract_text() for page in PdfReader(str(target)).pages[1:])
            label = records[start - 1]["week"]
            # Week label occurs once for the merged block, not per PJ/PK lesson.
            self.assertEqual(text.count(label), sum(
                records[s - 1]["week"] == label for s, _ in week_merge_ranges(records)
            ))
            self.assertIn(records[start - 1]["display_id"], text)
            self.assertIn(records[end - 1]["display_id"], text)

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
                        numbers = re.findall(r"(?m)^\s*PdP\s+(\d{3})\s*$", body)
                        self.assertEqual(numbers, [f"{n:03d}" for n in range(1, 37)])
                    else:
                        for sub in ("PJ", "PK"):
                            ids = re.findall(r"(?m)^\s*" + sub +
                                             r" PdP\s+(\d{3})\s*$", body)
                            self.assertEqual(ids, [
                                f"{n:03d}" for n in range(1, SUBJECT_ROW_COUNTS[sub][year]+1)
                            ])
                    self.assertIn("DRAF", reader.pages[0].extract_text())


if __name__ == "__main__":
    unittest.main()
