"""Check T2 editorial identity and pending gates without claiming source verification."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'docs' / 'pjpk'
FILES = ('T2_PK_7_COMPLETE_RPH_EDITORIAL_STAGING_20261024.json',
         'T2_PK_11_REMAINING_EDITORIAL_STAGING_20261024.json')


class TestT2EditorialIdentity(unittest.TestCase):
    def test_all_eighteen_have_unique_ids_and_no_unsupported_promotion(self):
        batches = [json.loads((ROOT / name).read_text(encoding='utf-8'))['records'] for name in FILES]
        self.assertEqual([len(batch) for batch in batches], [7, 11])
        records = [row for batch in batches for row in batch]
        self.assertEqual(len({row['id'] for row in records}), 18)
        flags = ('textbook_verified', 'rpt_exact_slot_verified',
                 'rph_runtime_verified', 'a4_review_verified')
        for row in records:
            self.assertEqual(row['year'], 'Tahun 2')
            self.assertEqual(row['subject'], 'Pendidikan Kesihatan')
            self.assertEqual(row['status'], 'editorial_staging_only')
            self.assertIs(row['production_ready'], False)
            for flag in flags:
                self.assertIs(row[flag], False, (row['id'], flag))
        for row in records:
            self.assertTrue(row['sk'], row['id'])
            self.assertTrue(row['sp'], row['id'])
            self.assertIs(row['sk_text_verified'], True)
            self.assertIs(row['sp_text_verified'], True)
            self.assertTrue(all(sp.startswith(row['sk'] + '.') for sp in row['sp']))


if __name__ == '__main__':
    unittest.main()
