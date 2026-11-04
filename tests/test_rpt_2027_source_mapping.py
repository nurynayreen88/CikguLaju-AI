"""Unit tests for read-only RPT 2027 source mapping validation."""
import csv
import tempfile
import unittest
from pathlib import Path
from scripts.validate_rpt_2027_source_mapping import REQUIRED, validate

SOURCE = Path(__file__).resolve().parents[1] / "data/rpt_2027/year2_source_mapping_seed_20261028.csv"

class MappingTests(unittest.TestCase):
    def test_existing_seed(self):
        rows, errors = validate(SOURCE)
        self.assertEqual(len(rows), 9)
        self.assertEqual(errors, [])

    def write_rows(self, rows):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "mapping.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=REQUIRED)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def seed_rows(self):
        with SOURCE.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_duplicate_id_rejected(self):
        rows = self.seed_rows()
        rows.append(dict(rows[0]))
        _, errors = validate(self.write_rows(rows))
        self.assertIn("Duplicate record_id", errors)

    def test_ready_rejected(self):
        rows = self.seed_rows()
        rows[0]["review_status"] = "READY"
        _, errors = validate(self.write_rows(rows))
        self.assertTrue(any("premature READY" in e for e in errors))

    def test_invalid_sp_rejected(self):
        rows = self.seed_rows()
        rows[0]["sp_codes"] = "1.2"
        _, errors = validate(self.write_rows(rows))
        self.assertTrue(any("malformed SP" in e for e in errors))

    def test_unverified_calendar_enforced(self):
        rows = self.seed_rows()
        rows[0]["calendar_2027_status"] = "VERIFIED"
        _, errors = validate(self.write_rows(rows))
        self.assertTrue(any("calendar must remain UNVERIFIED" in e for e in errors))

    def test_malformed_extra_column_rejected(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "bad.csv"
        path.write_text(",".join(REQUIRED) + "\n" + ",".join(["x"] * (len(REQUIRED) + 1)) + "\n", encoding="utf-8")
        _, errors = validate(path)
        self.assertTrue(any("Malformed CSV" in e for e in errors))

if __name__ == "__main__":
    unittest.main()
