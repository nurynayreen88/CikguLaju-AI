"""Cross-check priority queue against verified T5 PK evidence without DB writes."""
import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'docs' / 'pjpk'


def read(name):
    with (ROOT / name).open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


class TestT5SourceQueueConsistency(unittest.TestCase):
    def test_queue_matches_verified_overlay(self):
        queue = read('T5_PK_PRIORITY_3_SOURCE_QUEUE_20261024.csv')
        overlay = read('T5_PK_3_VERIFIED_EVIDENCE_OVERLAY_20261024.csv')
        self.assertEqual(len(queue), 3)
        self.assertEqual(len(overlay), 3)
        by_id = {row['entry_id']: row for row in overlay}
        self.assertEqual(len(by_id), 3)
        self.assertEqual({row['entry_id'] for row in queue}, set(by_id))
        for row in queue:
            source = by_id[row['entry_id']]
            self.assertEqual(row['year_label'], source['year_label'])
            self.assertEqual(row['subject'], source['subject'])
            self.assertEqual(row['topic'], source['topic'])
            self.assertEqual(int(row['sp_links']), len(source['dskp_sp'].split(';')))
            self.assertEqual(int(row['dskp_text_matches']), int(row['sp_links']))
            self.assertEqual(row['book_exact_match'], source['textbook_verified'])
            self.assertEqual(row['production_ready'], source['production_ready'])
            self.assertEqual(source['rpt_exact_slot_verified'], '0')
            self.assertEqual(source['rph_runtime_verified'], '0')
            self.assertEqual(source['a4_review_verified'], '0')
            self.assertIn('RPT', row['next_required_check'])


if __name__ == '__main__':
    unittest.main()
