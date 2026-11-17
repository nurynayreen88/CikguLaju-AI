"""Verify each 2027 Mathematics DLP Year 6 review export against its RPT."""

from collections import Counter
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from docx import Document
from pypdf import PdfReader

from staging.dlp.year6.render_mathematics import DATA, RPT, RPT_NAME, export, load_plans, official_rows


class MathematicsDLPYear6ReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        folder = TemporaryDirectory()
        cls.addClassCleanup(folder.cleanup)
        cls.output = Path(folder.name)
        rpt, cls.plans = load_plans()
        export(cls.output, rpt, cls.plans)

    def test_review_rpt_preserves_all_rows_and_changes_only_verified_book_pages(self):
        original = official_rows(Document(RPT))
        reviewed = official_rows(Document(self.output / f"{RPT_NAME}_Teacher_Review.docx"))
        self.assertEqual(len(original), 54)
        changed_refs = {}
        for source_row, updated_row, plan in zip(original, reviewed, self.plans, strict=True):
            source = [cell.text for cell in source_row.cells]
            updated = [cell.text for cell in updated_row.cells]
            self.assertEqual(source[:4], updated[:4])
            original_book, original_duration = source[4].splitlines()
            actual_book, actual_duration = updated[4].splitlines()
            self.assertEqual(original_duration, actual_duration)
            self.assertEqual(actual_book.replace("TB ", "Textbook ", 1), plan["reference"])
            if original_book != actual_book:
                changed_refs[plan["id"]] = actual_book
        references = json.loads(DATA.read_text(encoding="utf-8"))["reference_corrections"]
        self.assertEqual(len(changed_refs), 5)
        self.assertEqual(changed_refs, references)

    def test_all_word_pdf_documents_match_specific_plan_and_fit_a4(self):
        self.assertEqual(Counter(plan["id"][0] for plan in self.plans), {"L": 46, "R": 8})
        self.assertEqual(sum(plan["minutes"] for plan in self.plans), 5760)
        for plan in self.plans:
            with self.subTest(plan_id=plan["id"]):
                stem = f"CikguLaju_RPH_Mathematics_DLP_Y6_{plan['id']}"
                word = Document(self.output / f"{stem}.docx")
                section = word.sections[0]
                self.assertAlmostEqual(section.page_width.mm, 210, places=1)
                self.assertAlmostEqual(section.page_height.mm, 297, places=1)
                self.assertEqual(word.paragraphs[2].text, plan["title"])
                details = {row.cells[0].text: row.cells[1].text for row in word.tables[0].rows}
                for label, key in (("Lesson / PdP", "label"), ("RPT date ranges", "dates"),
                                   ("Standards", "standards"), ("Book reference", "reference"),
                                   ("Learning objective", "objective")):
                    self.assertEqual(details[label], plan[key])
                self.assertEqual(word.tables[2].rows[0].cells[1].text, plan["evidence"])
                self.assertEqual(sum(int(phase.split()[-2]) for phase, *_ in plan["phases"]),
                                 plan["minutes"])
                self.assertEqual(
                    [tuple(cell.text for cell in row.cells) for row in word.tables[1].rows[1:]],
                    plan["phases"],
                )

                pdf = PdfReader(self.output / f"{stem}.pdf")
                self.assertEqual(len(pdf.pages), 1)
                page = pdf.pages[0]
                self.assertAlmostEqual(float(page.mediabox.width), 595.28, places=1)
                self.assertAlmostEqual(float(page.mediabox.height), 841.89, places=1)
                page_text = " ".join(page.extract_text().split())
                for field in ("title", "label", "dates", "standards", "reference", "objective", "evidence"):
                    self.assertIn(" ".join(plan[field].split()), page_text)


if __name__ == "__main__":
    unittest.main()
