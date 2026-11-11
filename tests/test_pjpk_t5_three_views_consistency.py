"""Ensure three T5 release-tracking views cannot drift independently."""
import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'docs' / 'pjpk'


def index(name):
    with (ROOT / name).open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    result = {r['entry_id']: r for r in rows}
    if len(result) != len(rows):
        raise ValueError(f'duplicate entry_id in {name}')
    return result


class TestT5ThreeViews(unittest.TestCase):
    def test_evidence_queue_checklist_match(self):
        overlay = index('T5_PK_3_VERIFIED_EVIDENCE_OVERLAY_20261024.csv')
        queue = index('T5_PK_PRIORITY_3_SOURCE_QUEUE_20261024.csv')
        checklist = index('T5_PK_3_REMAINING_RELEASE_CHECKLIST_20261024.csv')
        self.assertEqual(set(overlay), {'2259', '2260', '2261'})
        self.assertEqual(set(queue), set(overlay))
        self.assertEqual(set(checklist), set(overlay))
        for key, evidence in overlay.items():
            self.assertEqual(queue[key]['book_exact_match'], evidence['textbook_verified'])
            self.assertEqual(queue[key]['production_ready'], evidence['production_ready'])
            for flag in ('dskp_verified', 'textbook_verified', 'rpt_exact_slot_verified',
                         'rph_runtime_verified', 'a4_review_verified', 'production_ready'):
                self.assertEqual(checklist[key][flag], evidence[flag], (key, flag))
            self.assertEqual(evidence['production_ready'], '0')
            self.assertIn('RPT', queue[key]['next_required_check'])
            self.assertIn('RPT', checklist[key]['next_required_action'])


if __name__ == '__main__':
    unittest.main()
