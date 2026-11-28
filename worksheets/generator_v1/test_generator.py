"""Smoke tests with synthetic reference only; NOT Batch 03 visual approval."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
import fitz
import generate as g

ROOT = Path(__file__).resolve().parent
FONT = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
SAMPLE = json.loads((ROOT/"sample_batch04.json").read_text(encoding="utf-8"))

def fixture(path):
    doc=fitz.open()
    for i in range(28):
        p=doc.new_page(width=595.28,height=841.89)
        p.insert_font(fontname="CLFixture",fontfile=str(FONT))
        def t(x,y,s,size=12):
            p.insert_text((x,y),s,fontname="CLFixture",fontsize=size)
        if i in (0,1):
            t(38,32,"CikguLaju",17)
            t(225,30,"MATEMATIK SK • TAHUN 4",10)
            t(509,30,"SP 2.1.1",8)
            t(545,832,f"{i+1}/2",8)
            if i==0:
                t(48,83,"PECAHAN, PERPULUHAN DAN PERATUS",10)
                t(38,126,g.EXPECTED_REF,18)
                t(38,160,"Nama                 Kelas           Tarikh",10)
            t(38,832,"CIKGULAJU / LEMBARAN LATIHAN ASLI",8)
        if i==12:
            t(61,205,"Kira dalam bentuk lazim.",13)
        if i==13:
            t(80,152,"8.7 + 4.085 + 2.63 =",14)
    doc.save(path)
    doc.close()

class Tests(unittest.TestCase):
    def test_validation(self):
        g.validate(SAMPLE)
        for change in ("missing_answer","duplicate","overflow","bad_time","bad_term","bad_operator"):
            data=copy.deepcopy(SAMPLE)
            s=data["worksheets"][0]
            if change=="missing_answer":
                s["answers"].pop("1")
            elif change=="duplicate":
                s["pages"][0][0]["items"][1]["id"]="1"
            elif change=="overflow":
                s["pages"].append(copy.deepcopy(s["pages"][1]))
            elif change=="bad_time":
                data["worksheets"][1]["pages"][0][0]["items"][0]["start"]="24:00"
            elif change=="bad_term":
                s["pages"][0][0]["items"][0]["terms"]=["ABC","2"]
            elif change=="bad_operator":
                s["pages"][0][0]["items"][0]["op"]="/"
            with self.subTest(change=change), self.assertRaises(ValueError):
                g.validate(data)

    def test_render_and_lock(self):
        self.assertTrue(FONT.exists(),"Install fonts-dejavu-core for synthetic test.")
        with tempfile.TemporaryDirectory() as d:
            d=Path(d)
            source=d/"fixture.pdf"
            lock=d/"design.lock.json"
            fixture(source)
            t=g.Template(source,[FONT.parent],lock,True)
            self.assertFalse(lock.exists())
            out=d/"out"
            g.render(t,SAMPLE,out)
            t.save_pending_lock()
            self.assertTrue(lock.exists())
            with fitz.open(out/"MURID.pdf") as p:
                self.assertEqual(len(p),4)
                self.assertIn("Tambah Wang",p[0].get_text())
                self.assertNotIn(g.EXPECTED_REF,p[0].get_text())
            with fitz.open(out/"SKEMA.pdf") as p:
                self.assertEqual(len(p),2)
            self.assertEqual(len(list((out/"preview").glob("*.png"))),6)
            manifest=json.loads((out/"manifest.json").read_text())
            self.assertEqual(manifest["status"],"DRAFT_VISUAL_QA_REQUIRED")
            self.assertEqual(len(manifest["worksheets"]),2)
            g.Template(source,[FONT.parent],lock,False)
            with self.assertRaises(ValueError):
                g.render(t,SAMPLE,out)
            with self.assertRaises(ValueError):
                g.Template(source,[FONT.parent],lock,True)
            obj=json.loads(lock.read_text())
            obj["reference_sha256"]="invalid"
            lock.write_text(json.dumps(obj))
            with self.assertRaises(ValueError):
                g.Template(source,[FONT.parent],lock,False)

if __name__=="__main__":
    unittest.main()
