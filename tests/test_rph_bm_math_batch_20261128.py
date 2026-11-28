import unittest
from io import BytesIO
from unittest.mock import patch
from docx import Document
import fitz
from web import kp2027_bm_rpt_aligned as bm, kp2027_bm_5p as b5, kp2027_math_5p as m5

class BatchRPH(unittest.TestCase):
    def test_all_companions(self):
        self.assertEqual(len(b5.companions()),353)
        _,_,drafts,_=m5.inventory()
        self.assertEqual(len(drafts),249)
        for g,n in drafts:
            m5.prepare(g,n,{})
        for g,n in b5.companions():
            b5.prepare(g,n,{})

    def test_bm_header_both_formats(self):
        for g,n in [('A',1),('B',175)]:
            w=Document(BytesIO(bm.render(g,n,'word')))
            cells=w.tables[0].rows[0].cells
            self.assertIn('Kelas:',cells[0].text)
            self.assertIn('BAHASA MELAYU SK',cells[1].text)
            with fitz.open(stream=bm.render(g,n,'pdf'),filetype='pdf') as d:
                teacher=d[0].search_for('Kelas:')
                subject=d[0].search_for('BAHASA MELAYU SK')
                self.assertTrue(teacher and subject)
                self.assertLess(teacher[0].x0,subject[0].x0)

    def test_math_source_mismatch_fails_closed(self):
        source,original,drafts,reviews=m5.inventory()
        broken={**original,'A':{**original['A'],'1':{**original['A']['1'],'word':'0'*64}}}
        with patch.object(m5,'inventory',return_value=(source,broken,drafts,reviews)):
            with self.assertRaises(m5.PilotUnavailable):
                m5.prepare('A',1,{})
