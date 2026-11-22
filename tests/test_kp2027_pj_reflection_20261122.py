"""Regression: PJ KP2027 auto reflection must be criterion-specific (Word and PDF)."""
from io import BytesIO
import unittest

import fitz
from docx import Document

from web.kp2027_pj_private_web import personalize_pj


def make_word(criterion):
    doc=Document()
    table=doc.add_table(rows=15, cols=2)
    table.cell(0, 0).text="Maklumat PdP"
    table.cell(0, 1).text="Kelas:    Tarikh:    Masa:    Bil. Murid:"
    table.cell(4, 0).text="Kriteria Kejayaan"
    table.cell(4, 1).text=criterion
    table.cell(14, 0).text="Refleksi (Auto / Manual)"
    table.cell(14, 1).text="Arahan lama: rekod pemerhatian."
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
    page.insert_text((38,706),"Refleksi (Auto / Manual)",fontsize=8.2)
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

    def test_manual_pdf_is_used_verbatim(self):
        text="10 murid menguasai, 5 perlu bimbingan. Latihan imbangan secara berpandu."
        out=personalize_pj(make_pdf(self.criterion),"pdf",{"reflection_mode":"manual","reflection":text})
        with fitz.open(stream=out,filetype="pdf") as d:
            self.assertIn("Latihan imbangan secara berpandu",d[0].get_text())


if __name__=="__main__":
    unittest.main()
