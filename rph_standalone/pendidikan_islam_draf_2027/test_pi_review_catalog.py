"""Standalone catalog tests; run against all 696 exact source identities."""
import unittest
from pathlib import Path
from pi_review_catalog import COUNT,HELD,counts,get_lesson,preview_rows
ROOT=Path(__file__).resolve().parent
class PIReviewCatalogTests(unittest.TestCase):
    def test_all_690_drafts_and_6_held(self):
        self.assertEqual(counts(root=ROOT),{'total':696,'draf':690,'held':6,'critical_source_hold':3,'preview_eligible':687,'ready':0})
        for y,count in COUNT.items():
            for n in range(1,count+1):
                row=get_lesson(y,n,root=ROOT)
                if (y,n) in HELD or (y,n) in {(4,83),(6,137),(6,141)}:self.assertIsNone(row)
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
    def test_critical_sources_blocked_and_material_notes_not_leaked(self):
        base={'TAJUK':'legacy'}
        for year, lesson in ((4,83),(6,137),(6,141)):
            self.assertIs(
                preview_rows({'subject':'Pendidikan Islam','year':f'Tahun {year}',
                              'lesson_no':lesson},base,root=ROOT),base)
        note_count=0
        for y,total in COUNT.items():
            for n in range(1,total+1):
                if (y,n) in HELD or (y,n) in {(4,83),(6,137),(6,141)}:
                    continue
                raw=get_lesson(y,n,root=ROOT)['fields']['bahan']
                result=preview_rows({'subject':'Pendidikan Islam','year':f'Tahun {y}',
                                     'lesson_no':n},base,root=ROOT)
                expected=next(x.strip() for x in raw.splitlines() if x.strip())
                self.assertEqual(result['BAHAN BANTU MENGAJAR'],expected)
                if len([x for x in raw.splitlines() if x.strip()])>1:
                    note_count+=len([x for x in raw.splitlines() if x.strip()])-1
                    self.assertNotIn('\\n',result['BAHAN BANTU MENGAJAR'])
                self.assertEqual(result['CATATAN SEMAKAN'],get_lesson(y,n,root=ROOT)['teacher_notice'])
        self.assertEqual(note_count,520)

    def test_invalid_inputs_and_closed_catalog(self):
        self.assertIsNone(get_lesson(True,1,root=ROOT))
        self.assertIsNone(get_lesson(6,999,root=ROOT))
        self.assertIsNone(get_lesson('６','１',root=ROOT))
        self.assertIsNone(counts(root='/nonexistent/locked'))
if __name__=='__main__':unittest.main()