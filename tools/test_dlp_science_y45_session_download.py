"""Verify real Y4/Y5 download adapters and original source preservation."""
import os,unittest
from unittest.mock import patch
from io import BytesIO
from docx import Document
import fitz
from staging.dlp.year4 import render_science as y4
from staging.dlp.year5 import render_science as y5
from staging.dlp.year5.downloads import SCIENCE
from staging.dlp.science_y45_session_delivery import extend,for_teacher

class ScienceSession(unittest.TestCase):
    def test_actual_downloads(self):
        seen=0
        for year,plans,adapter in [(4,y4.load_plans(),y4),(5,y5.load_plans()[1],SCIENCE)]:
            for p in plans:
                if p["minutes"]!=30:continue
                seen+=1
                uid=f"{int(p['unit'].split()[1]):02d}"
                ident=p["id"] if year==4 else "DLP-SCI-Y5-"+p["id"]
                with patch.dict(os.environ,{"CIKGULAJU_DLP_SCIENCE_Y45_SESSION":"1"}):
                    _,source=adapter.resolve_download(uid,ident)
                    expanded=extend(source,year)
                    self.assertEqual(expanded["minutes"],60)
                    self.assertEqual(expanded["phases"][:2]+expanded["phases"][3:],source["phases"])
                    for field in ("content_standards","learning_standards","objective"):
                        self.assertEqual(expanded[field],source[field])
                    self.assertEqual(for_teacher(source,year,{"time":"08:00 - 08:30"}),source)
                    row=next(l for u in adapter.download_catalogue() for l in u["lessons"] if l["id"]==ident)
                    self.assertEqual(row["minutes"],60)
                    teacher={"class":"Bestari","time":"08:00 - 09:00","date":"2027-01-12","students":"30"}
                    word=adapter.render_download(source,"word",teacher)
                    pdf=adapter.render_download(source,"pdf",teacher)
                    doc=Document(BytesIO(word))
                    txt=" ".join(c.text for t in doc.tables for r in t.rows for c in r.cells)
                    self.assertIn("Targeted reinforcement",txt)
                    with fitz.open(stream=pdf,filetype="pdf") as d:self.assertEqual(len(d),1)
                with patch.dict(os.environ,{"CIKGULAJU_DLP_SCIENCE_Y45_SESSION":"0"}):
                    self.assertEqual(extend(p,year),p)
        self.assertEqual(seen,22)
if __name__=="__main__":unittest.main()
