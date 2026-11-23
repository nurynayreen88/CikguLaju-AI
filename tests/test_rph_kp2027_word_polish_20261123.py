"""Word-only KP2027 visual polish must never rewrite KSSR teaching content."""
from io import BytesIO
from pathlib import Path
import json
import unittest
from zipfile import ZipFile

from docx import Document
from docx.oxml import OxmlElement
from lxml import etree

from web.rph_kp2027_word_polish import polish_kssr_word, W, DOC

ROOT = Path(__file__).resolve().parents[1]
SUBJECTS = json.loads((ROOT/"web/rph_login_canonical_layout_20261121.json").read_text())["subjects"]

def sample(title="RANCANGAN PENGAJARAN HARIAN", rtl=False):
    doc = Document()
    doc.add_paragraph(title)
    grid = doc.add_table(rows=6, cols=2)
    rows = [
        ("Mata Pelajaran", "Mata pelajaran sedia ada"),
        ("Standard Kandungan", "2.1 Standard asal tidak diubah."),
        ("Standard Pembelajaran", "2.1.1 Penerangan SP asal."),
        ("Objektif Pembelajaran", "Murid mengenal pasti bahan."),
        ("Kriteria Kejayaan", "Murid menyatakan dua bukti."),
        ("Kelas", ""),
    ]
    for i, (label, value) in enumerate(rows):
        grid.cell(i, 0).text = label
        grid.cell(i, 1).text = value
    phases = doc.add_table(rows=4, cols=3)
    for i, (label, value) in enumerate((
        ("Fasa", "Aktiviti Pengajaran",),
        ("Set Induksi", "Guru menunjukkan gambar asal."),
        ("Aktiviti Utama", "Aktiviti 1:\nMurid mengenal pasti gambar."),
        ("Penutup", "Guru meminta rumusan."),
    )):
        phases.cell(i, 0).text = label
        phases.cell(i, 1).text = value
        phases.cell(i, 2).text = "Catatan asal" if i == 2 else ""
    tail = doc.add_table(rows=2, cols=2)
    tail.cell(0, 0).text, tail.cell(0, 1).text = "Pemulihan / Pengayaan", "Latihan asal."
    tail.cell(1, 0).text, tail.cell(1, 1).text = "Refleksi", "Catatan asal."
    if rtl:
        for tbl in doc.tables:
            tbl._tbl.tblPr.append(OxmlElement("w:bidiVisual"))
    out = BytesIO()
    doc.save(out)
    return out

def parts(data):
    with ZipFile(BytesIO(data)) as z:
        assert z.testzip() is None
        return {name: z.read(name) for name in z.namelist()}

def words(data):
    root = etree.fromstring(parts(data)[DOC])
    return tuple(t.text for t in root.iter(W+"t")), root

class TestKSSRWordPolish(unittest.TestCase):
    def test_sixteen_subjects_keep_source_bytes_and_style_themed_tables(self):
        for item in SUBJECTS:
            code = item["subject_code"]
            normalized = {
                "DLP_MATH": "MATH_DLP", "DLP_SCIENCE": "SCIENCE_DLP",
                "MUSIC": "MUZIK", "PPKI": "PENGURUSAN_KEHIDUPAN_PPKI",
            }.get(code, code)
            with self.subTest(subject=normalized):
                original = sample(rtl=item["direction"]=="rtl")
                before = parts(original.getvalue())
                styled = polish_kssr_word(original, normalized)
                after = parts(styled.getvalue())
                self.assertEqual(set(before), set(after))
                for name in before:
                    if name != DOC:
                        self.assertEqual(before[name], after[name], name)
                src_text, src_xml = words(original.getvalue())
                final_text, final_xml = words(styled.getvalue())
                self.assertEqual(src_text, final_text)
                self.assertEqual(len(list(src_xml.iter(W+"tbl"))),
                                 len(list(final_xml.iter(W+"tbl"))))
                doc = Document(BytesIO(styled.getvalue()))
                self.assertEqual(len(doc.tables), 3)
                self.assertEqual(doc.tables[0].cell(1, 1).text,
                                 "2.1 Standard asal tidak diubah.")
                self.assertEqual(doc.tables[1].cell(2, 1).text,
                                 "Aktiviti 1:\nMurid mengenal pasti gambar.")
                shadings = {n.get(W+"fill") for n in final_xml.iter(W+"shd")}
                self.assertIn(item["tone"].upper().strip("#"), shadings)
                self.assertIn(item["strong"].upper().strip("#"), shadings)
                tables = list(final_xml.iter(W+"tbl"))
                for tbl in tables:
                    self.assertEqual(tbl.find(W+"tblPr/"+W+"tblW").get(W+"type"), "pct")
                    self.assertEqual(tbl.find(W+"tblPr/"+W+"tblW").get(W+"w"), "5000")
                    self.assertIsNotNone(tbl.find(W+"tblPr/"+W+"tblBorders"))
                self.assertEqual(
                    len(list(src_xml.iter(W+"bidiVisual"))),
                    len(list(final_xml.iter(W+"bidiVisual"))))
                self.assertEqual(polish_kssr_word(styled, normalized).getvalue(),
                                 styled.getvalue())

    def test_empty_teacher_boxes_stay_truly_blank_and_no_status_label_is_added(self):
        original = sample()
        styled = polish_kssr_word(original, "BM")
        word = Document(BytesIO(styled.getvalue()))
        self.assertEqual(word.tables[0].cell(5, 1).text, "")
        self.assertEqual(word.tables[2].cell(1, 0).text, "Refleksi")
        self.assertNotIn("Auto / Manual", "\n".join(p.text for p in word.paragraphs))

    def test_unknown_source_and_invalid_word_fail_closed(self):
        original = sample()
        self.assertIs(polish_kssr_word(original, "UNKNOWN"), original)
        invalid = BytesIO(b"not a Word file")
        self.assertIs(polish_kssr_word(invalid, "BM"), invalid)
        off = sample("Nota guru sahaja")
        self.assertIs(polish_kssr_word(off, "BM"), off)

    def test_non_rph_two_col_data_not_restyled(self):
        doc = Document()
        doc.add_paragraph("Senarai umum")
        t = doc.add_table(rows=2, cols=2)
        t.cell(0, 0).text = "Nombor"
        t.cell(1, 0).text = "Kelas"
        buff = BytesIO()
        doc.save(buff)
        self.assertIs(polish_kssr_word(buff, "MATH"), buff)

if __name__ == "__main__":
    unittest.main()
