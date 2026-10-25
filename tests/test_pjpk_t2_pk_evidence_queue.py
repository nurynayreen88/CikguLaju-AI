import tempfile
import unittest
from pathlib import Path
from scripts.pjpk_t2_pk_evidence_queue import build, write


class TestT2PKEvidenceQueue(unittest.TestCase):
    def test_eighteen_entries_all_fail_closed(self):
        rows = build()
        self.assertEqual(len(rows), 18)
        self.assertEqual(len({r["entry_id"] for r in rows}), 18)
        for row in rows:
            self.assertEqual(row["production_ready"], "false")
            self.assertIn("textbook exact", row["required_next_evidence"])
            self.assertIn("RPT exact", row["required_next_evidence"])
            self.assertEqual(row["sp_text_verified"], "true")
        self.assertTrue(all(not row["candidate_sp_codes_not_verified"] for row in rows))
        self.assertEqual(sum(bool(row["recorded_sp_codes"]) for row in rows), 18)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "queue.csv"
            self.assertEqual(write(path), 18)
            self.assertEqual(len(path.read_text(encoding="utf-8").splitlines()), 19)


if __name__ == "__main__":
    unittest.main()
