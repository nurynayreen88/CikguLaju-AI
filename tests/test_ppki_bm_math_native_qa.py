"""Native Word/PDF QA for BM and Mathematics; no catalog status mutation."""
import copy
import json
import unittest
from io import BytesIO
from pathlib import Path

from docx import Document
from pypdf import PdfReader

from staging.ppki.render_approved_subject import render_approved_lesson


class TestPPKIBMAndMathNativeQA(unittest.TestCase):
    def test_native_output_for_nonconflicting_drafts(self):
        root = Path(__file__).resolve().parents[1] / "staging" / "ppki"
        teacher = {"class": "2 PPKI", "date": "2027-01-12",
                   "time": "08:00–09:00", "students": "6"}
        checked = skipped = 0
        for name in ("bahasa_melayu_tahun2_tema1_draft.json",
                     "bahasa_melayu_tahun2_tema2_6_draft.json",
                     "matematik_tahun2_all_units_draft.json"):
            original = json.loads((root / name).read_text(encoding="utf-8"))
            self.assertEqual(original["status"], "DALAM_SEMAKAN")
            for record in original["lessons"]:
                if record.get("status") in (
                    "KONFLIK_PENOMBORAN_DSKP",
                    "PADANAN_ALTERNATIF_DSKP_PERLU_SAHAN",
                ):
                    skipped += 1
                    continue
                with self.subTest(bank=name, pdp=record["pdp"]):
                    catalog = copy.deepcopy(original)
                    lesson = next(l for l in catalog["lessons"] if l["pdp"] == record["pdp"])
                    catalog["status"] = lesson["status"] = "READY"
                    # Only a temporary QA copy; never published.
                    word = Document(BytesIO(render_approved_lesson(catalog, lesson, "docx", teacher)))
                    texts = [p.text for p in word.paragraphs]
                    for table in word.tables:
                        for row in table.rows:
                            texts.extend(cell.text for cell in row.cells)
                    text = "\n".join(texts)
                    self.assertIn(lesson["title"], text)
                    self.assertIn("2 PPKI", text)
                    self.assertIn("Refleksi", text)
                    pdf = PdfReader(BytesIO(render_approved_lesson(catalog, lesson, "pdf", teacher)))
                    self.assertEqual(len(pdf.pages), 1)
                    self.assertIn("2 PPKI", pdf.pages[0].extract_text())
                    self.assertIn("Refleksi", pdf.pages[0].extract_text())
                    checked += 1
        self.assertEqual((checked, skipped), (143, 6))
