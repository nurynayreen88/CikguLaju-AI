"""Keep the editorial release checklist aligned with the verified evidence overlay."""
import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'docs' / 'pjpk'


def load(name):
    with (ROOT / name).open(newline='', encoding='utf-8-sig') as fh:
        return list(csv.DictReader(fh))


class TestT5ReleaseChecklist(unittest.TestCase):
    def test_checklist_matches_authoritative_overlay(self):
        overlay = load('T5_PK_3_VERIFIED_EVIDENCE_OVERLAY_20261024.csv')
        checklist = load('T5_PK_3_REMAINING_RELEASE_CHECKLIST_20261024.csv')
        expected = {'2259', '2260', '2261'}
        self.assertEqual({r['entry_id'] for r in overlay}, expected)
        self.assertEqual({r['entry_id'] for r in checklist}, expected)
        self.assertEqual(len(checklist), len(expected))
        indexed = {r['entry_id']: r for r in overlay}
        flags = ('dskp_verified', 'textbook_verified', 'rpt_exact_slot_verified',
                 'rph_runtime_verified', 'a4_review_verified', 'production_ready')
        for row in checklist:
            source = indexed[row['entry_id']]
            self.assertEqual((row['year_label'], row['subject']),
                             (source['year_label'], source['subject']))
            for flag in flags:
                self.assertIn(row[flag], ('0', '1'))
                self.assertEqual(row[flag], source[flag], (row['entry_id'], flag))
            if row['production_ready'] == '1':
                self.assertTrue(all(row[flag] == '1' for flag in flags[:-1]))
            self.assertTrue(row['next_required_action'].strip())


if __name__ == '__main__':
    unittest.main()
