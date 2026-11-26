"""Paired Mathematics Web release assets, native cover and selector contract."""
from pathlib import Path
from io import BytesIO
from unittest.mock import patch
from datetime import date
import json,unittest
from docx import Document
from web import dlp_paired_science_rpt as paired
from web import native_telegram_sequence_rph_client as client

ROOT=Path("rpt_2027")
class PairedMathematicsWebTests(unittest.TestCase):
    def test_verified_rpt_and_calendar(self):
        for y in (3,4,5,6):
            with self.subTest(year=y):
                data=paired.assets(str(ROOT),y,'mathematics_dlp')
                rows=json.loads(data["index"])
                self.assertEqual(len(rows),101)
                self.assertEqual(len({r["week"] for r in rows}),35)
                with patch("web.english_rpt_2027_http._has_paid_access",return_value=False):
                    with self.assertRaises(PermissionError):paired.word_document(ROOT,y,{},None,'mathematics_dlp')
                with patch("web.english_rpt_2027_http._has_paid_access",return_value=True),patch("web.rpt_school_cover.school_identity",return_value=None):
                    blob,_=paired.word_document(ROOT,y,{},None,'mathematics_dlp')
                    d=Document(BytesIO(blob))
                    self.assertEqual(sum(len(t.rows)-1 for t in d.tables[:-1]),101)
                for row in rows:
                    for i,g in enumerate(row["dates"]):
                        s=paired.suggestion(ROOT,y,date.fromisoformat(g["start"]),i==0,'mathematics_dlp')
                        self.assertIn(f"Session {row['session']:02d}",s["dlp_labels"])
                with patch.dict("os.environ",{'CIKGULAJU_DLP_PAIRED_MATH_YEARS':"3,4,5,6"}):
                    route,selection=client._selection(y,"MATH_DLP","sessions","SESSION-101")
                    self.assertEqual(route,client.DLP_ROUTE)
                    self.assertEqual(selection["lesson"],"SESSION-101")
                    with self.assertRaises(ValueError):client._selection(y,"MATH_DLP","sessions","SESSION-102")
                with patch.dict("os.environ",{'CIKGULAJU_DLP_PAIRED_MATH_YEARS':""}):
                    with self.assertRaises(ValueError):client._selection(y,"MATH_DLP","sessions","SESSION-001")

if __name__=="__main__":unittest.main()
