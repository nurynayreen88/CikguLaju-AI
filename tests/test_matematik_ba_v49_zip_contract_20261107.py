"""Regression: staging manifest and loader agree on real-ZIP release-gate schema."""
import json
import inspect
import unittest
from pathlib import Path
from rph_standalone.matematik import staging_preview_v49 as preview

ROOT=Path(__file__).resolve().parents[1]/"audits"

class ActualArchiveContract(unittest.TestCase):
    def test_outer_manifest_equals_loader_contract(self):
        gate=json.loads((ROOT/"matematik_v49_release_gate_20261107.json").read_text(encoding="utf8"))
        self.assertEqual(preview.EXPECTED_SHA256,gate["sha256"])
        self.assertEqual(gate["bytes"],48774109)
        self.assertTrue(gate["zip_metadata_gate_repaired"])
        self.assertEqual(gate["offline_actual_archive_preview_tests_passed"],12)
        self.assertEqual(gate["zip_release_gate_schema"],{
            "rph_total":585,"BA_year2_3_ref_count":234,"final_ready":False})
        src=inspect.getsource(preview._check_file)
        self.assertIn('AUDIT/V49_RELEASE_GATE.json',src)
        for key in gate["zip_release_gate_schema"]:
            self.assertIn(f'gate.get("{key}")',src)
        self.assertFalse(gate["final_ready"])
        self.assertFalse(gate["production_modified"])
        self.assertEqual(gate["academic_item_level_approved"],0)
if __name__=="__main__":
    unittest.main()
