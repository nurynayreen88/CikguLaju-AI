"""Source-preserving layout test for real Web-side RPH download bytes."""
import io
import unittest
from zipfile import ZipFile
from docx import Document
from web.rph_delivery_presentation_20261121 import (
    ORDINARY, presentation_for_web, _word_tokens,
)


def native_three_table_example():
    """Build the documented native Word table contract with REAL source text."""
    d = Document()
    d.add_paragraph("RANCANGAN PENGAJARAN HARIAN")
    header = d.add_table(rows=10, cols=2)
    for i, (label, value) in enumerate((
        ("Mata Pelajaran", "Bahasa Melayu"),
        ("Tahun/Tingkatan", "Tahun 3"),
        ("Tarikh", ""),
        ("Hari", ""),
        ("Masa", ""),
        ("Kelas", ""),
        ("Bilangan Murid", ""),
        ("Tajuk", "Kata Nama"),
        ("Standard Kandungan", "1.1 Membaca dan memahami"),
        ("Standard Pembelajaran", "1.1.1 Mengenal pasti maklumat"),
    )):
        header.cell(i, 0).text = label
        header.cell(i, 1).text = value
    activity = d.add_table(rows=4, cols=3)
    for i, (name, value) in enumerate((
        ("Fasa", "Aktiviti Pengajaran & Pembelajaran"),
        ("Set Induksi", "Guru memaparkan gambar."),
        ("Aktiviti Utama", "Aktiviti 1\nMurid mengenal pasti kata nama.\nAktiviti 2\nMurid membina ayat."),
        ("Penutup", "Murid menyatakan dua contoh kata nama."),
    )):
        activity.cell(i, 0).text = name
        activity.cell(i, 1).text = value
        activity.cell(i, 2).text = ""
    end = d.add_table(rows=2, cols=2)
    end.cell(0, 0).text = "Pemulihan / Pengayaan"
    end.cell(0, 1).text = "Bimbingan berfokus"
    end.cell(1, 0).text = "Refleksi"
    end.cell(1, 1).text = ""
    out = io.BytesIO()
    d.save(out)
    return out.getvalue()


class TestFinalStyle(unittest.TestCase):
    def test_word_uses_four_aligned_tables_and_preserves_exact_source_tokens(self):
        original = native_three_table_example()
        before = _word_tokens(original)
        for subject in ORDINARY:
            amended = presentation_for_web(
                {"subject": subject, "source": "telegram-native"}, "word",
                io.BytesIO(original),
            ).getvalue()
            self.assertEqual(_word_tokens(amended), before, subject)
            self.assertEqual(ZipFile(io.BytesIO(amended)).testzip(), None)
            self.assertEqual(len(Document(io.BytesIO(amended)).tables), 4, subject)
            self.assertIn("Murid membina ayat.", Document(io.BytesIO(amended)).tables[2].cell(2,1).text)

    def test_specialty_subjects_and_unknown_layout_are_unchanged(self):
        original = native_three_table_example()
        for subject in ("PI", "ARAB", "SCIENCE", "MATH_DLP", "SCIENCE_DLP",
                        "PPKI", "MATH_SJKC", "MATH_SJKT"):
            self.assertEqual(
                presentation_for_web({"subject": subject}, "word", io.BytesIO(original)).getvalue(),
                original,
            )
        other = io.BytesIO(b"not-a-word-file")
        self.assertIs(presentation_for_web({"subject": "BM"}, "word", other), other)

    def test_does_not_consume_source_stream(self):
        original = native_three_table_example()
        inp = io.BytesIO(original)
        result = presentation_for_web({"subject": "BM"}, "word", inp)
        self.assertEqual(inp.getvalue(), original)
        self.assertIn("Kata Nama", Document(result).tables[0].cell(0,0).text
                      + " " + str([t.cell(0,1).text for t in Document(result).tables]))


if __name__ == "__main__":
    unittest.main()
