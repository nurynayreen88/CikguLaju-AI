"""Tests for BA TOC and v27 page-range reconciliation, without private PDFs."""
import csv
from collections import Counter
from pathlib import Path
import unittest

DIR = Path(__file__).resolve().parents[1] / "audits"


def records(filename):
    with (DIR / filename).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class VisualContentsEvidence(unittest.TestCase):
    def test_contents_cover_printed_pages_without_gaps(self):
        data = records("matematik_ba_t2_t3_visual_toc_20261107.csv")
        self.assertEqual(len(data), 190)
        self.assertEqual(Counter(r["year"] for r in data), {"2": 84, "3": 106})
        for year, final_page, offset in (("2", 156, 6), ("3", 155, 3)):
            rows = [r for r in data if r["year"] == year]
            self.assertEqual(int(rows[0]["printed_page_start"]), 1)
            self.assertEqual(int(rows[-1]["printed_page_end"]), final_page)
            expected = 1
            for row in rows:
                with self.subTest(year=year, topic=row["toc_topic"]):
                    first = int(row["printed_page_start"])
                    last = int(row["printed_page_end"])
                    self.assertEqual(first, expected)
                    self.assertGreaterEqual(last, first)
                    self.assertEqual(int(row["pdf_page_start"]), first + offset)
                    self.assertEqual(int(row["pdf_page_end"]), last + offset)
                    self.assertEqual(row["v41_match_status"], "NOT_MAPPED_TO_V41")
                    expected = last + 1

    def test_72_legacy_ranges_match_visual_contents_not_v41(self):
        data = records("matematik_ba_t2_v27_72_toc_reconciliation_20261107.csv")
        self.assertEqual(len(data), 72)
        self.assertEqual(len({r["legacy_rph_id"] for r in data}), 72)
        for row in data:
            with self.subTest(legacy=row["legacy_rph_id"]):
                self.assertEqual(row["check_status"], "TOC_RANGE_MATCHED_NOT_ACTIVITY_VERIFIED")
                self.assertEqual(row["v41_release_approval"], "NOT_APPROVED")
                self.assertTrue(row["toc_topic"])
                a, *rest = map(int, row["v27_ba_printed_page"].split("-"))
                b = rest[0] if rest else a
                self.assertGreaterEqual(a, int(row["toc_printed_start"]))
                self.assertLessEqual(b, int(row["toc_printed_end"]))
                self.assertEqual(int(row["v27_pdf_page_start"]), a + 6)
                self.assertEqual(int(row["v27_pdf_page_end"]), b + 6)


if __name__ == "__main__":
    unittest.main()
