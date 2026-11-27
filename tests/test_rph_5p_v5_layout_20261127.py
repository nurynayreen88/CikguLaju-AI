"""Approved V5 sample and source-preservation / layout regression."""
import io
import json
import unittest
from hashlib import sha256
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn
from web.rph_5p_v5_layout import render_word,MATH_V5,PHASE_KEYS,MS_LABELS

SOURCE={
    "subject":"matematik_sk","year":3,"lesson_id":"QA-approved-sample",
    "curriculum":"KSSR",
    "topic":"Nombor dan Operasi / Pecahan, Perpuluhan dan Peratus\nPecahan setara",
    "sk":"3.1 Pecahan.",
    "sp":"3.1.2 Menyatakan pecahan setara bagi pecahan wajar yang penyebutnya hingga 10.",
    "objective":"Pada akhir PdP, murid dapat menyatakan pecahan setara bagi pecahan wajar dengan penyebut hingga 10.",
    "criteria":"Murid menjawab sekurang-kurangnya 4 daripada 5 soalan pecahan setara dengan betul.",
    "closure":"Murid menyatakan satu pasangan pecahan setara dan merumuskan konsep yang dipelajari.",
    "aids_pak21_emk":"Jalur kertas, kad pecahan, lembaran latihan / Think-Pair-Share / Nilai murni: kerjasama.",
    "remedial_enrichment":"Pemulihan: Padankan pecahan berpandukan jalur pecahan.\nPengayaan: Cari dua pecahan setara bagi 1/3 dengan penyebut hingga 10.",
    "reflection":"",
    "reference":"Rujukan: DSKP KSSR (Semakan 2017) Matematik Tahun 3, hlm. 42."
}
RAW=json.dumps(SOURCE,ensure_ascii=False,sort_keys=True).encode()
COMPANION={**{k:SOURCE[k] for k in ("subject","year","lesson_id","curriculum")},
    "source_sha256":sha256(RAW).hexdigest(),
    "phases":dict(zip(PHASE_KEYS,(
        "Guru menunjukkan dua gambar pizza sama saiz: 1/2 dan 2/4. Murid meneka sama ada bahagian berlorek sama banyak.",
        "Murid melipat jalur kertas sama panjang kepada 2, 4 dan 8 bahagian, kemudian membandingkan 1/2, 2/4 dan 4/8.",
        "Murid menerangkan dapatan. Guru membimbing murid mengenal pasti pecahan setara dengan mendarab pengangka dan penyebut dengan nombor yang sama.",
        "Secara berpasangan, murid memadankan kad pecahan seperti 1/3 dengan 2/6 dan 2/5 dengan 4/10 serta menjelaskan padanan.",
        "Murid menjawab lima soalan individu untuk menyatakan pecahan setara. Guru menyemak pencapaian berdasarkan kriteria kejayaan."
    )))}

def sample(source=SOURCE,companion=COMPANION,**kwargs):
    return render_word(source,companion,source_bytes=RAW,palette=MATH_V5,
        subject_heading="MATEMATIK SK\nTAHUN 3",**kwargs)

class V5(unittest.TestCase):
    def test_exact_layout_and_source(self):
        doc=Document(io.BytesIO(sample()))
        self.assertEqual(len(doc.tables),1)
        t=doc.tables[0]
        self.assertEqual(len(t.rows),21)
        self.assertEqual(t.cell(0,0).text,MS_LABELS[0])
        self.assertEqual(t.cell(1,0).text,"Kelas:\nTarikh:\nMasa:\nBil. Murid:")
        self.assertEqual(t.cell(1,1).text,"MATEMATIK SK\nTAHUN 3")
        for i,k in enumerate(("topic","sk","sp","objective","criteria"),2):
            self.assertEqual(t.cell(i,1).text,SOURCE[k])
        for i,k in enumerate(PHASE_KEYS):
            title=t.cell(7+2*i,1)
            self.assertEqual(title.text,MS_LABELS[11+i])
            self.assertEqual(title._tc.tcPr.find(qn("w:shd")).get(qn("w:fill")),MATH_V5.label)
            self.assertEqual(t.cell(8+2*i,1).text,COMPANION["phases"][k])
            self.assertIs(t.cell(7+2*i,0)._tc,t.cell(7,0)._tc)
            self.assertIs(t.cell(8+2*i,0)._tc,t.cell(7,0)._tc)
        self.assertEqual(t.cell(20,0).text,"Refleksi")
        self.assertFalse(t.cell(20,1).text.strip())
    def test_fail_closed(self):
        for companion in ({**COMPANION,"year":4},{**COMPANION,"source_sha256":"0"*64},
                          {**COMPANION,"phases":{}},
                          {**COMPANION,"phases":dict.fromkeys(PHASE_KEYS,"repeat")}):
            with self.assertRaises(ValueError):sample(companion=companion)
        with self.assertRaises(ValueError):sample(source={**SOURCE,"sk":"changed"})
    def test_teacher_fields(self):
        doc=Document(io.BytesIO(sample(profile={"class":"3 Amanah","date":"1/2/2027","time":"8.00–9.00","students":"30"})))
        self.assertIn("3 Amanah",doc.tables[0].cell(1,0).text)
        self.assertEqual(doc.tables[0].cell(4,1).text,SOURCE["sp"])

if __name__=="__main__":
    import sys
    if len(sys.argv)==2 and sys.argv[1]=="--sample":
        Path("qa_rph5p").mkdir(exist_ok=True)
        Path("qa_rph5p/RPH_5P_MATEMATIK_T3.docx").write_bytes(sample())
    else: unittest.main()
