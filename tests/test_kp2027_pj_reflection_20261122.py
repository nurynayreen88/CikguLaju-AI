"""Regression: PJ KP2027 auto reflection must be criterion-specific (Word and PDF)."""
from io import BytesIO
import unittest

import fitz
from docx import Document

from web.kp2027_pj_private_web import personalize_pj


def make_word(criterion):
    doc=Document()
    from docx.shared import Pt
    doc.add_paragraph('PENDIDIKAN JASMANI TAHUN 1').runs[0].bold=False
    table=doc.add_table(rows=15, cols=2)
    table.cell(0, 0).text="Maklumat PdP"
    table.cell(0, 1).text="Kelas:    Tarikh:    Masa:    Bil. Murid:"
    table.cell(4, 0).text="Kriteria Kejayaan"
    table.cell(4, 1).text=criterion
    table.cell(13, 1).text="Latihan tambahan secara berpandu."
    table.cell(13, 1).paragraphs[0].runs[0].font.size=Pt(9)
    table.cell(14, 0).text="Refleksi (Auto / Manual)"
    table.cell(14, 1).text="Arahan lama: rekod pemerhatian."
    table.rows[14].height=Pt(100)
    output=BytesIO()
    doc.save(output)
    return output.getvalue()


def make_pdf(criterion):
    doc=fitz.open()
    page=doc.new_page(width=595.3039,height=841.8898)
    page.insert_text((38,42),"PENDIDIKAN JASMANI TAHUN 1", fontsize=12)
    for i,lab in enumerate(("Kelas:","Tarikh:","Masa:","Bil. Murid:")):
        page.insert_text((393.7,101+i*13.3),lab,fontsize=8.2)
    page.insert_text((38,309),"Kriteria Kejayaan",fontsize=8.2)
    page.insert_text((155.6,304),criterion,fontsize=8.1)
    page.insert_text((38,335),"EMK / Nilai",fontsize=8.2)
    page.draw_line((35,670),(560,670),width=.6)
    page.draw_line((35,732),(560,732),width=.6)
    page.insert_text((155.6,680),"Catatan awal yang mesti dibuang.",fontsize=8.1)
    page.insert_text((38,700),"Refleksi (Auto /",fontsize=8.2)
    page.insert_text((38,711),"Manual)",fontsize=8.2)
    page.insert_text((155.6,707),"Arahan lama: rekod pencapaian.",fontsize=8.1)
    page.insert_text((38,740),"Rujukan DK rasmi",fontsize=8.1)
    result=doc.tobytes()
    doc.close()
    return result


class PJReflectionTest(unittest.TestCase):
    criterion="Murid melakukan dua percubaan terkawal dan menerangkan satu konsep."
    def test_auto_word_extracts_actual_criterion_and_keeps_two_counts_blank(self):
        original=make_word(self.criterion)
        out=personalize_pj(original,"word",{"reflection_mode":"auto","teacher_students":"35"})
        doc=Document(BytesIO(out))
        text=doc.tables[0].cell(14,1).text
        self.assertIn("melakukan dua percubaan terkawal",text)
        self.assertIn("____ orang",text)
        self.assertEqual(text.count("____"),2)
        self.assertIn("tindakan",text.lower() if "tindakan" in text.lower() else text.lower().replace("akan mengikuti","tindakan"))
        self.assertNotIn("Arahan lama",text)
        self.assertEqual(doc.tables[0].cell(4,1).text,self.criterion)
        self.assertTrue(doc.paragraphs[0].runs[0].bold)
        self.assertEqual(doc.tables[0].cell(14,0).text,"Refleksi")
        self.assertAlmostEqual(doc.tables[0].cell(14,1).paragraphs[0].runs[0].font.size.pt,9)
        self.assertIsNone(doc.tables[0].rows[14].height)

    def test_manual_word_is_used_verbatim(self):
        note="12 murid telah menguasai; 3 murid diberi bimbingan pergerakan."
        out=personalize_pj(make_word(self.criterion),"word",{"reflection_mode":"manual","reflection":note})
        self.assertEqual(Document(BytesIO(out)).tables[0].cell(14,1).text,note)

    def test_auto_pdf_keeps_criterion_and_counts(self):
        raw=make_pdf(self.criterion)
        out=personalize_pj(raw,"pdf",{"reflection_mode":"auto","teacher_students":"35"})
        with fitz.open(stream=out,filetype="pdf") as d:
            self.assertEqual(len(d),1)
            text=d[0].get_text()
            self.assertIn("melakukan dua percubaan",text)
            self.assertIn("____",text)
            self.assertNotIn("Arahan lama",text)
            self.assertNotIn("Catatan awal",text)
            self.assertNotIn("Auto /",text)
            self.assertNotIn("Manual)",text)
            spans=[s for b in d[0].get_text("dict")["blocks"] for l in b.get("lines",[]) for s in l["spans"]]
            title=next(s for s in spans if s["text"].startswith("PENDIDIKAN JASMANI"))
            self.assertTrue(title["flags"]&16 or "Bold" in title["font"])
            label=next(s for s in spans if s["text"]=="Refleksi")
            self.assertTrue(label["flags"]&16 or "Bold" in label["font"])
            for s in spans:
                if "orang murid" in s["text"]:
                    self.assertGreaterEqual(s["bbox"][1],670)
                    self.assertLessEqual(s["bbox"][3],732)

    def test_manual_pdf_is_used_verbatim(self):
        text="10 murid menguasai, 5 perlu bimbingan. Latihan imbangan secara berpandu."
        out=personalize_pj(make_pdf(self.criterion),"pdf",{"reflection_mode":"manual","reflection":text})
        with fitz.open(stream=out,filetype="pdf") as d:
            self.assertIn("Latihan imbangan secara berpandu",d[0].get_text())


if __name__=="__main__":
    unittest.main()
