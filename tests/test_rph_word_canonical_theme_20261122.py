"""Native Word gallery-theme QA: no changes to source SK/SP or activities."""
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import json
import unittest
from xml.etree import ElementTree as ET

from docx import Document
from web.rph_table_layout import build_rph_table_docx

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT / "web/rph_login_canonical_layout_20261121.json")
                      .read_text(encoding="utf-8"))
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

MAIN = (
    "Aktiviti 1:\nGuru menerangkan contoh dan murid mengenal pasti maklumat.\n"
    "\nAktiviti 2:\nMurid menulis jawapan dalam ayat lengkap.\n"
    "\nAktiviti 3:\nGuru menjalankan pentaksiran individu."
)
STANDARDS = (
    "2.1 Membaca dan memahami teks rujukan asal.",
    "2.1.1 Murid menyatakan maklumat dan bukti daripada teks.",
)
TEACHER = ("4 Bestari", "", "08:00 - 09:00", "30")

def sample(subject):
    labels = ["Mata Pelajaran", "Tahun", "Tarikh", "Hari", "Masa",
              "Kelas", "Bilangan Murid", "Tajuk", "Standard Kandungan",
              "Standard Pembelajaran", "Objektif Pembelajaran",
              "Kriteria Kejayaan", "Pengetahuan Sedia Ada", "BBM",
              "EMK / Nilai", "Pentaksiran"]
    values = [subject, "Tahun 4", TEACHER[1], "", TEACHER[2],
              TEACHER[0], TEACHER[3], "Tajuk asal", STANDARDS[0],
              STANDARDS[1], "Objektif PdP asal", "Kriteria asal",
              "Pengetahuan asal", "Buku teks asal", "Nilai asal",
              "Penilaian asal"]
    return {
        "subject": subject,
        "telegram_layout": {
            "style": "telegram-native-rph-v1",
            "title": "RANCANGAN PENGAJARAN HARIAN",
            "header": [{"label": a, "value": b} for a, b in zip(labels, values)],
            "activity_header": ["Fasa", "Aktiviti Pengajaran & Pembelajaran", "Catatan"],
            "phases": [
                {"label": "Set Induksi", "activity": "Set induksi asal.", "notes": ""},
                {"label": "Aktiviti Utama", "activity": MAIN, "notes": "Catatan asal"},
                {"label": "Penutup", "activity": "Rumusan asal.", "notes": ""},
            ],
            "footer": [
                {"label": "Pemulihan / Pengayaan", "value": "Pemulihan asal"},
                {"label": "Refleksi", "value": "Refleksi asal"},
            ],
        },
    }

def word_parts(data):
    raw = build_rph_table_docx(data, {}).getvalue()
    with ZipFile(BytesIO(raw)) as zipfile:
        assert zipfile.testzip() is None
        xml = ET.fromstring(zipfile.read("word/document.xml"))
    return Document(BytesIO(raw)), xml


class TestCanonicalNativeRphWord(unittest.TestCase):
    def test_all_sixteen_subjects_preserve_source_and_apply_theme(self):
        for entry in CONTRACT["subjects"]:
            code = entry["subject_code"]
            normalized = {"DLP_MATH": "MATH_DLP",
                          "DLP_SCIENCE": "SCIENCE_DLP",
                          "MUSIC": "MUZIK",
                          "PPKI": "PENGURUSAN_KEHIDUPAN_PPKI"}.get(code, code)
            with self.subTest(subject=code):
                doc, xml = word_parts(sample(normalized))
                self.assertEqual(len(doc.tables), 3)
                first, phases, followup = doc.tables
                self.assertEqual(first.cell(8, 1).text, STANDARDS[0])
                self.assertEqual(first.cell(9, 1).text, STANDARDS[1])
                self.assertEqual(phases.cell(2, 1).text, MAIN)
                self.assertEqual(phases.cell(1, 1).text, "Set induksi asal.")
                self.assertEqual(phases.cell(3, 1).text, "Rumusan asal.")
                self.assertEqual(followup.cell(0, 1).text, "Pemulihan asal")
                self.assertEqual(followup.cell(1, 1).text, "Refleksi asal")
                colors = {s.get(W + "fill") for s in xml.iter(W + "shd")}
                self.assertIn(entry["tone"].lstrip("#").upper(), colors)
                self.assertIn(entry["strong"].lstrip("#").upper(), colors)
                bidi = list(xml.iter(W + "bidiVisual"))
                self.assertEqual(bool(bidi), code in ("PI", "ARAB"))

    def test_activity_headings_bold_but_not_instructions(self):
        _, xml = word_parts(sample("BM"))
        by_text = {}
        for run in xml.iter(W + "r"):
            text = "".join(t.text or "" for t in run.findall(W + "t"))
            if text:
                by_text.setdefault(text, []).append(run)
        for heading in ("Aktiviti 1:", "Aktiviti 2:", "Aktiviti 3:"):
            self.assertIn(heading, by_text)
            self.assertTrue(any(run.find(W + "rPr/" + W + "b") is not None
                                for run in by_text[heading]))
        for original in (
            "Guru menerangkan contoh dan murid mengenal pasti maklumat.",
            "Murid menulis jawapan dalam ayat lengkap.",
            "Guru menjalankan pentaksiran individu.",
        ):
            self.assertIn(original, by_text)
            self.assertTrue(all(run.find(W + "rPr/" + W + "b") is None
                                for run in by_text[original]))

    def test_unknown_subject_falls_back_without_losing_content(self):
        doc, xml = word_parts(sample("UNKNOWN_SUBJECT"))
        self.assertEqual(doc.tables[1].cell(2, 1).text, MAIN)
        self.assertIn("EDF3FA", {s.get(W + "fill") for s in xml.iter(W + "shd")})


if __name__ == "__main__":
    unittest.main()
