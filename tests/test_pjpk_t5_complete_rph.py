"""Regression checks for the structured, nonproduction RPH inventory."""
import copy
import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("audit_rph", ROOT / "scripts/pjpk_t5_complete_rph_audit.py")
audit_rph = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_rph)

class StructuredRPHTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads(audit_rph.JSON_PATH.read_text(encoding="utf-8"))
        with audit_rph.OVERLAY_PATH.open(newline="", encoding="utf-8-sig") as fh:
            cls.overlay = list(csv.DictReader(fh))
    def check(self, mutate):
        payload, overlay = copy.deepcopy(self.payload), copy.deepcopy(self.overlay)
        mutate(payload, overlay)
        with tempfile.TemporaryDirectory() as d:
            j, c = Path(d)/"rph.json", Path(d)/"overlay.csv"
            j.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            with c.open("w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=list(overlay[0]))
                writer.writeheader()
                writer.writerows(overlay)
            return audit_rph.audit(j, c)[1]
    def test_current_three_records_pass(self):
        self.assertEqual(self.check(lambda p,o: None), [])
    def test_missing_full_activity_blocks(self):
        self.assertTrue(self.check(lambda p,o: p["records"][0]["activities"].pop()))
    def test_sp_drift_blocks(self):
        self.assertTrue(self.check(lambda p,o: p["records"][0].update(sp=["6.1.1"])))
    def test_unsupported_promotion_blocks(self):
        self.assertTrue(self.check(lambda p,o: p["records"][0].update(production_ready=True)))
    def test_invented_teacher_date_blocks(self):
        self.assertTrue(self.check(lambda p,o: p["records"][0]["teacher_fields"].update(date="2026-01-01")))
    def test_missing_record_blocks(self):
        self.assertTrue(self.check(lambda p,o: p["records"].pop()))

if __name__ == "__main__":
    unittest.main()
