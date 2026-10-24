"""Unit tests for T5 PK evidence overlay; no production DB access."""
import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("overlay", ROOT / "scripts/pjpk_t5_evidence_overlay.py")
overlay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(overlay)
COLUMNS = ["entry_id", "year_label", "subject", "dskp_sk", "dskp_sp",
           "verified_textbook_printed_pages", "dskp_verified", "textbook_verified",
           "rpt_exact_slot_verified", "rph_runtime_verified", "a4_review_verified", "production_ready"]

def sample():
    return [dict(zip(COLUMNS, [ident, "Tahun 5", "Pendidikan Kesihatan", sk,
                                ";".join(sorted(sp)), pages, "1", "1", "0", "0", "0", "0"]))
            for ident, (sk, sp, pages) in overlay.EXPECTED.items()]

def check(rows):
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "overlay.csv"
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        return overlay.audit(path)[1]

class OverlayTests(unittest.TestCase):
    def test_pending_three_pass_integrity(self):
        self.assertEqual(check(sample()), [])
    def test_missing_row_blocks(self):
        self.assertTrue(check(sample()[:2]))
    def test_duplicate_blocks(self):
        rows = sample()
        self.assertTrue(check(rows + [rows[0].copy()]))
    def test_wrong_sp_blocks(self):
        rows = sample()
        rows[0]["dskp_sp"] = "6.1.1"
        self.assertTrue(check(rows))
    def test_wrong_book_page_blocks(self):
        rows = sample()
        rows[0]["verified_textbook_printed_pages"] = "127"
        self.assertTrue(check(rows))
    def test_premature_ready_blocks(self):
        rows = sample()
        rows[0]["production_ready"] = "1"
        self.assertTrue(check(rows))
    def test_fully_checked_flags_allow_promotion(self):
        rows = sample()
        for r in rows:
            r.update(rpt_exact_slot_verified="1", rph_runtime_verified="1",
                     a4_review_verified="1", production_ready="1")
        self.assertEqual(check(rows), [])

if __name__ == "__main__":
    unittest.main()
