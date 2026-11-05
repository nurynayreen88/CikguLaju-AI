"""Standalone catalog tests; run against all 696 exact source identities."""
import unittest
from pathlib import Path
from pi_review_catalog import COUNT,HELD,counts,get_lesson,preview_rows
ROOT=Path(__file__).resolve().parent
class PIReviewCatalogTests(unittest.TestCase):
    def test_all_690_drafts_and_6_held(self):
        self.assertEqual(counts(root=ROOT),{'total':696,'draf':690,'held':6,'ready':0})
        for y,count in COUNT.items():
            for n in range(1,count+1):
                row=get_lesson(y,n,root=ROOT)
                if (y,n) in HELD:self.assertIsNone(row)
                else:
                    self.assertIsNotNone(row,(y,n))
                    self.assertIn('DRAF',row['teacher_notice'])
                    self.assertIn('objektif',row['fields'])
                    self.assertIn('aktiviti_utama',row['fields'])
    def test_exact_target_and_subject_safety(self):
        base={'TAJUK':'legacy'}
        self.assertIs(preview_rows({'subject':'English','year':'Tahun 3','lesson_no':5},base,root=ROOT),base)
        self.assertIs(preview_rows({'subject':'Pendidikan Islam','year':'Tahun 2','lesson_no':35},base,root=ROOT),base)
        self.assertIs(preview_rows({'subject':'Pendidikan Islam','year':'Tahun 5','lesson_no':124,'sp_code':'9.9.9'},base,root=ROOT),base)
        r=preview_rows({'subject':'Pendidikan Islam','year':'Tahun 5','lesson_no':124},base,root=ROOT)
        self.assertIn('DRAF',r['TAJUK']);self.assertIn('العصر',r['STANDARD PEMBELAJARAN'])
        self.assertEqual(base,{'TAJUK':'legacy'})
    def test_invalid_inputs_and_closed_catalog(self):
        self.assertIsNone(get_lesson(True,1,root=ROOT))
        self.assertIsNone(get_lesson(6,999,root=ROOT))
        self.assertIsNone(get_lesson('６','１',root=ROOT))
        self.assertIsNone(counts(root='/nonexistent/locked'))
if __name__=='__main__':unittest.main()