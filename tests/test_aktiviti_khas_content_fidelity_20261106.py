"""Guard that full, subject-specific lesson instructions survive Word/PDF export."""
import io
import re
import unicodedata
import unittest

from docx import Document
from pypdf import PdfReader

from rph_standalone.aktiviti_khas.engine import _catalog, render


META = {"class": "4 Amanah", "date": "2026-11-06",
        "time": "09:00-10:00", "students": "30"}


def compact(text):
    text = unicodedata.normalize("NFKC", text or "")
    return "".join(c.casefold() for c in text if c.isalnum())


class CompleteContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = _catalog()[0]["activities"]

    def test_word_has_all_complete_numbered_instructions(self):
        for row in self.records:
            with self.subTest(activity=row["id"]):
                year = row["years"][0]
                subject = row.get("subject_options", [None])[0]
                raw = render(row, year, META, "word", subject=subject)
                doc = Document(io.BytesIO(raw))
                self.assertGreaterEqual(len(doc.tables), 4)
                activity_table = doc.tables[2]
                self.assertEqual(len(activity_table.rows), 7)
                labels = ["Set Induksi", "Aktiviti 1", "Aktiviti 2",
                          "Aktiviti 3", "Pengukuhan / Penilaian", "Penutup"]
                source = [row["set_induksi"], *row["aktiviti_utama"],
                          row["pengukuhan_penilaian"], row["penutup"]]
                for i, (label, original) in enumerate(zip(labels, source), start=1):
                    actual_label = activity_table.rows[i].cells[0].text
                    actual_text = activity_table.rows[i].cells[1].text
                    self.assertIn(label, actual_label)
                    self.assertEqual(actual_text, original)
                self.assertEqual(compact(doc.tables[1].rows[0].cells[1].text),
                                 compact(row["title"]))

    def test_pdf_keeps_all_three_full_detailed_steps(self):
        for row in self.records:
            with self.subTest(activity=row["id"]):
                year = row["years"][0]
                subject = row.get("subject_options", [None])[0]
                raw = render(row, year, META, "pdf", subject=subject)
                reader = PdfReader(io.BytesIO(raw))
                self.assertEqual(len(reader.pages), 1)
                extracted = compact(reader.pages[0].extract_text())
                for part in row["aktiviti_utama"]:
                    self.assertGreaterEqual(len(part), 185)
                    self.assertIn(compact(part), extracted)
                self.assertIn(compact(row["learning_objective"]), extracted)
                self.assertIn(compact(row["bbm"]), extracted)

    def test_subjects_have_distinct_rph_instructions_at_all_stages(self):
        rows = [r for r in self.records
                if r["category"] == "SELEPAS_TAMAT_SUKATAN"]
        for letter in "ABC":
            stage = [r for r in rows if r["id"].endswith(letter)]
            self.assertEqual(len(stage), 13)
            self.assertEqual(len({r["subject_options"][0] for r in stage}), 13)
            # A different heading alone is not enough: steps must actually differ.
            self.assertEqual(len({
                compact(" ".join(r["aktiviti_utama"])) for r in stage
            }), 13)
        for subject in {r["subject_options"][0] for r in rows}:
            versions = [r for r in rows if r["subject_options"][0] == subject]
            self.assertEqual(len(versions), 3)
            self.assertEqual(len({r["learning_objective"] for r in versions}), 3)
            self.assertEqual(len({
                compact(" ".join(r["aktiviti_utama"])) for r in versions
            }), 3)


if __name__ == "__main__":
    unittest.main()
