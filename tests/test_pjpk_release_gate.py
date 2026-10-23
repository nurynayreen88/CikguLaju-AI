"""Regression checks for the fail-closed PJPK source gate; no production DB required."""
import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "pjpk_release_gate.py"
spec = importlib.util.spec_from_file_location("pjpk_release_gate", SCRIPT)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

BASE = dict(entry_id="100", year_label="Tahun 1", subject="Pendidikan Jasmani",
            entry_kind="PDP_CANDIDATE", sp_links="2", dskp_text_matches="2",
            dskp_text_mismatches="0", dskp_text_missing="0",
            book_exact_match="1", conflict="0", production_ready="1")

def check(rows):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "source.csv"
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(BASE))
            writer.writeheader()
            writer.writerows(rows)
        return gate.audit(path)

class PJPKReleaseGateTests(unittest.TestCase):
    def test_verified_candidate_passes_source_checks(self):
        self.assertEqual(check([BASE.copy()])[2], [])
    def test_reference_cannot_be_ready(self):
        row = dict(BASE, entry_kind="TEXTBOOK_REFERENCE")
        self.assertTrue(check([row])[2])
    def test_missing_dskp_text_blocks(self):
        row = dict(BASE, dskp_text_missing="1", dskp_text_matches="1")
        self.assertTrue(check([row])[2])
    def test_conflict_blocks(self):
        self.assertTrue(check([dict(BASE, conflict="1")])[2])
    def test_book_mapping_blocks(self):
        self.assertTrue(check([dict(BASE, book_exact_match="0")])[2])
    def test_duplicate_ids_block(self):
        self.assertTrue(check([BASE.copy(), BASE.copy()])[2])
    def test_invalid_year_blocks(self):
        self.assertTrue(check([dict(BASE, year_label="Tahun 7")])[2])
    def test_pending_inventory_is_not_promoted(self):
        row = dict(BASE, production_ready="0", dskp_text_matches="0",
                   dskp_text_missing="2", book_exact_match="0")
        rows, _, errors = check([row])
        self.assertEqual(errors, [])
        self.assertFalse(any(r["production_ready"] == "1" for r in rows))

if __name__ == "__main__":
    unittest.main()
