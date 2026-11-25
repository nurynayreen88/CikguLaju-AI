"""Exercise native rendering of the English Year 2 bank in CI only.

The in-memory QA copies are never written back to the catalog. This does
not grant curriculum approval or change the production release gate.
"""
import copy
import json
import unittest
from io import BytesIO
from pathlib import Path

from docx import Document
from pypdf import PdfReader

from staging.ppki.render_approved_subject import render_approved_lesson


class TestPPKIEnglishNativeQA(unittest.TestCase):
    def test_all_english_records_render_in_both_formats(self):
        path = (Path(__file__).resolve().parents[1] / "staging" / "ppki"
                / "english_year2_all_units_draft.json")
        original = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(original["status"], "DALAM_SEMAKAN")
        self.assertEqual(len(original["lessons"]), 57)
        teacher = {"class": "2 PPKI", "date": "2027-01-12",
                   "time": "08:00–09:00", "students": "6"}
        for source_lesson in original["lessons"]:
            with self.subTest(pdp=source_lesson["pdp"]):
                catalog = copy.deepcopy(original)
                lesson = next(l for l in catalog["lessons"]
                              if l["pdp"] == source_lesson["pdp"])
                catalog["status"] = lesson["status"] = "READY"
                word = Document(BytesIO(render_approved_lesson(
                    catalog, lesson, "docx", teacher)))
                self.assertGreaterEqual(len(word.tables), 1)
                texts = [p.text for p in word.paragraphs]
                for table in word.tables:
                    for row in table.rows:
                        texts.extend(cell.text for cell in row.cells)
                self.assertIn(lesson["title"], "\n".join(texts))
                self.assertIn("2 PPKI", "\n".join(texts))
                pdf = PdfReader(BytesIO(render_approved_lesson(
                    catalog, lesson, "pdf", teacher)))
                self.assertEqual(len(pdf.pages), 1)
                text = pdf.pages[0].extract_text()
                self.assertIn("2 PPKI", text)
                self.assertIn("Reflection", text)
        self.assertEqual(original["status"], "DALAM_SEMAKAN")
