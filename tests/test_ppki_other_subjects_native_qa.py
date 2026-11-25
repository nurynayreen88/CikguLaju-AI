"""Exercise three additional PPKI subject banks in temporary QA copies."""
import copy
import json
import unittest
from io import BytesIO
from pathlib import Path

from docx import Document
from pypdf import PdfReader
from staging.ppki.render_approved_subject import render_approved_lesson


class TestPPKIOtherSubjectsNativeQA(unittest.TestCase):
    def test_native_generation(self):
        root = Path(__file__).resolve().parents[1] / "staging" / "ppki"
        teacher = {"class": "2 PPKI", "date": "2027-01-12",
                   "time": "08:00–09:00", "students": "6"}
        count = skipped = 0
        for name in ("pendidikan_jasmani", "pendidikan_moral", "pendidikan_seni_kreatif"):
            original = json.loads((root / f"{name}_tahun2_draft.json").read_text(encoding="utf-8"))
            self.assertEqual(original["status"], "DALAM_SEMAKAN")
            for record in original["lessons"]:
                if record.get("status") in ("KONFLIK_PENOMBORAN_DSKP", "ADAPTASI_PERLU_SAHAN"):
                    skipped += 1
                    continue
                with self.subTest(subject=name, pdp=record["pdp"]):
                    catalog = copy.deepcopy(original)
                    lesson = next(l for l in catalog["lessons"] if l["pdp"] == record["pdp"])
                    catalog["status"] = lesson["status"] = "READY"
                    word = Document(BytesIO(render_approved_lesson(catalog, lesson, "docx", teacher)))
                    texts = [p.text for p in word.paragraphs]
                    for table in word.tables:
                        for row in table.rows:
                            texts.extend(cell.text for cell in row.cells)
                    text = "\n".join(texts)
                    self.assertIn(lesson["title"], text)
                    self.assertIn("2 PPKI", text)
                    pdf = PdfReader(BytesIO(render_approved_lesson(catalog, lesson, "pdf", teacher)))
                    self.assertEqual(len(pdf.pages), 1)
                    self.assertIn("Refleksi", pdf.pages[0].extract_text())
                    if name == "pendidikan_seni_kreatif":
                        mapping = catalog["component_standards"][lesson["component"]]["learning_standards"]
                        self.assertIn(mapping[lesson["sp"][0]], text)
                    count += 1
        self.assertEqual((count, skipped), (58, 2))

    def test_islam_format_guard(self):
        root = Path(__file__).resolve().parents[1] / "staging" / "ppki"
        catalog = json.loads((root / "pendidikan_islam_tahun2_draft.json").read_text(encoding="utf-8"))
        lesson = catalog["lessons"][0]
        catalog["status"] = lesson["status"] = "READY"
        with self.assertRaisesRegex(ValueError, "format has not passed approval"):
            render_approved_lesson(catalog, lesson, "pdf", {})
