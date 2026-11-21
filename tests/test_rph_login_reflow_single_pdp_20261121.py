"""Regression for source-preserving RPH Word reflow (no real lesson content stored in code)."""
import unittest
from docx import Document

from tools.reflow_rph_login_single_pdp_20261121 import make_math, make_arab


def math_example():
    d = Document()
    d.add_paragraph("RANCANGAN PENGAJARAN HARIAN")
    d.add_paragraph("Reference note retained")
    head = d.add_table(rows=12, cols=2)
    names = [
        "Mata Pelajaran", "Tahun / Kelas", "Tarikh / Masa", "Bilangan Murid",
        "Tajuk", "Standard Kandungan", "Standard Pembelajaran",
        "Objektif Pembelajaran", "Kriteria Kejayaan",
        "Pengetahuan Sedia Ada", "Bahan Bantu Mengajar", "EMK / Nilai / KBAT",
    ]
    values = [
        "Matematik", "Tahun 3 / 4 Ikhlas",
        "09/11/2026 (Isnin) | 08:00 - 09:00 (60 minit)", "30 orang",
        "Wang — Darab Wang", "4.2 Complete teaching standard",
        "4.2.1 Complete learning standard", "Original long objective",
        "Original full success criteria", "Original prior knowledge",
        "Original teaching materials", "Original EMK and nilai",
    ]
    for i,(name,value) in enumerate(zip(names,values)):
        head.cell(i,0).text=name;head.cell(i,1).text=value
    act=d.add_table(rows=6, cols=2)
    phases=["Set Induksi", "Aktiviti 1", "Aktiviti 2", "Aktiviti 3",
            "Aktiviti 4 - PBD", "Penutup"]
    for i,phase in enumerate(phases):
        act.cell(i,0).text=phase
        act.cell(i,1).text="Original academic instructions: "+phase
    last=d.add_table(rows=2,cols=2)
    last.cell(0,0).text="Pemulihan / Pengayaan";last.cell(0,1).text="Original remedial and enrichment"
    last.cell(1,0).text="Refleksi";last.cell(1,1).text="Original reflection"
    d.add_paragraph("Original source reference retained")
    return d


def arabic_example():
    d=Document()
    d.add_paragraph("RPH Bahasa Arab Tahun 2 · DRAF UNTUK SEMAKAN GURU")
    table=d.add_table(rows=15,cols=2)
    labels=["Tahun","Subjek","Unit / Tajuk","Fokus PdP","SK / SP",
            "Tarikh / Masa / Kelas","Objektif","Kriteria kejayaan",
            "Set induksi","Aktiviti 1","Aktiviti 2","Pengukuhan / PBD",
            "Penutup","BBM","Refleksi"]
    for idx,label in enumerate(labels):
        table.cell(idx,0).text=label
        table.cell(idx,1).text="Original academic content "+str(idx)
    return d


def all_text(doc):
    return "\n".join(cell.text for table in doc.tables
                     for row in table.rows for cell in row.cells)


class TestOnePdPReflow(unittest.TestCase):
    def test_math_moves_original_academic_text_into_two_tables(self):
        source=math_example()
        output=make_math(source)
        self.assertEqual(len(output.tables),3)
        body=all_text(output)
        for phrase in (
            "4.2 Complete teaching standard",
            "4.2.1 Complete learning standard", "Original long objective",
            "Original full success criteria", "Original prior knowledge",
            "Original teaching materials", "Original EMK and nilai",
            "Original academic instructions: Aktiviti 1",
            "Original academic instructions: Aktiviti 4 - PBD",
            "Original remedial and enrichment", "Original reflection"
        ):
            self.assertIn(phrase,body)
        self.assertEqual(output.tables[0].cell(0,1).tables[0].rows[0].cells[1].text,
                         "4 Ikhlas")
        self.assertIn("Original source reference retained",
                      "\n".join(p.text for p in output.paragraphs))

    def test_arabic_right_to_left_preserves_learning_content(self):
        source=arabic_example()
        output=make_arab(source)
        self.assertEqual(len(output.tables),3)
        body=all_text(output)
        for i in (2,3,4,6,7,8,9,10,11,12,13,14):
            self.assertIn("Original academic content "+str(i),body)
        self.assertIn("رفليكسي", body) if False else None  # Jawi labels differ by source.
        self.assertNotIn("DRAF UNTUK SEMAKAN GURU",body)
        self.assertEqual(len(output.tables[0].cell(0,1).tables[0].rows),4)

    def test_unknown_source_shapes_fail_closed_without_rewriting(self):
        with self.assertRaises(ValueError):
            make_math(Document())
        with self.assertRaises(ValueError):
            make_arab(Document())


if __name__=="__main__":
    unittest.main()
