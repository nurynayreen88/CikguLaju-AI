"""Final release gate regression, including fail-closed pending state."""
import unittest
from unittest.mock import patch
from scripts import pjpk_t5_final_release_gate as gate


class TestT5FinalGate(unittest.TestCase):
    def test_real_staging_evidence_remains_blocked(self):
        pending = gate.audit()
        self.assertEqual({ident for ident, _ in pending}, {'2259', '2260', '2261'})
        for _, missing in pending:
            self.assertIn('rpt_exact_slot_verified', missing)
            self.assertIn('rph_runtime_verified', missing)
            self.assertIn('a4_review_verified', missing)

    def test_premature_promotion_is_rejected(self):
        original = gate.read
        def altered(name):
            rows = original(name)
            if name.endswith('EVIDENCE_OVERLAY_20261024.csv'):
                rows['2259']['production_ready'] = '1'
            elif name.endswith('RELEASE_CHECKLIST_20261024.csv'):
                rows['2259']['production_ready'] = '1'
            elif name.endswith('SOURCE_QUEUE_20261024.csv'):
                rows['2259']['production_ready'] = '1'
            return rows
        with patch.object(gate, 'read', side_effect=altered):
            with self.assertRaisesRegex(ValueError, 'premature production promotion'):
                gate.audit()


if __name__ == '__main__':
    unittest.main()
