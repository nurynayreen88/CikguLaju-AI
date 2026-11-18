"""Verify the Year 4 Science review pack against the published 2027 RPT."""

import re
from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory
import unittest

from docx import Document
from pypdf import PdfReader

from staging.dlp.year4.render_science import export, load_plans
from staging.dlp.year4.annual_plan import make_annual_plan, standards_for


INTERNAL_LABEL = re.compile(
    r"\b(?:draf(?:t)?|produksi|production|staging|semakan guru|teacher review)\b",
    re.IGNORECASE,
)


class ScienceDLPYear4Review(unittest.TestCase):
    def test_export_preserves_schedule_and_a4_single_page(self):
        plans = load_plans()
        self.assertEqual(len(plans), 69)
        self.assertEqual(len({plan["unit"] for plan in plans}), 10)
        self.assertEqual(sum(plan["minutes"] for plan in plans), 3840)
        self.assertEqual(plans[-1]["rpt_dates"], ["A  17-21 Oct", "B  18-22 Oct"])
        with TemporaryDirectory(prefix="science_dlp_year4_") as directory:
            output = Path(directory)
            export(plans, output)
            word_pdf = output / "word_pdf"
            word_pdf.mkdir()
            run([
                "soffice", f"-env:UserInstallation={(output / 'lo').as_uri()}", "--headless",
                "--convert-to", "pdf", "--outdir", str(word_pdf),
                *map(str, sorted(output.glob("*.docx"))),
            ], check=True, capture_output=True, timeout=180)
            for plan in plans:
                with self.subTest(lesson=plan["id"]):
                    stem = plan["id"]
                    word = Document(output / f"{stem}.docx")
                    self.assertEqual(word.paragraphs[2].text, plan["title"])
                    self.assertNotRegex(word.core_properties.title or "", INTERNAL_LABEL)
                    fields = {row.cells[0].text: row.cells[1].text for row in word.tables[0].rows}
                    self.assertEqual(fields["Learning objective"], plan["objective"])
                    self.assertEqual(fields["Success criteria"], plan["success_criteria"])
                    self.assertEqual(fields["RPT 2027 dates"], " · ".join(plan["rpt_dates"]))
                    for folder in (output, word_pdf):
                        file = PdfReader(folder / f"{stem}.pdf")
                        self.assertEqual(len(file.pages), 1)
                        page, = file.pages
                        self.assertAlmostEqual(float(page.mediabox.width), 595.28, delta=1)
                        self.assertAlmostEqual(float(page.mediabox.height), 841.89, delta=1)
                        content = " ".join(page.extract_text().split())
                        self.assertIn(plan["title"], content)
                        self.assertIn(" ".join(plan["objective"].split()), content)
                        self.assertIn(" ".join(fields["Book references"].split()), content)
                        self.assertNotRegex(content, INTERNAL_LABEL)

    def test_annual_and_daily_plans_use_the_same_evidence(self):
        plans = load_plans()
        with TemporaryDirectory() as directory:
            out = Path(directory) / "rpt.docx"
            make_annual_plan(out)
            annual = Document(out)
            rows = [row for table in annual.tables[2:-1] for row in table.rows[1:]]
            for plan, row in zip(plans, rows, strict=True):
                dates, session, standards, objective, evidence, book = (
                    cell.text for cell in row.cells
                )
                self.assertEqual(dates.replace("–", "-").splitlines(), plan["rpt_dates"])
                self.assertEqual(session.splitlines(), [plan["label"], plan["title"]])
                self.assertEqual(standards.splitlines(), list(standards_for(plan)))
                self.assertEqual(objective, plan["objective"])
                self.assertEqual(evidence, plan["success_criteria"])
                self.assertEqual(book.splitlines(), [
                    plan["references"][0].removeprefix("TB "), f"{plan['minutes']} min",
                ])
            self.assertEqual(len(annual.tables[-1].rows) - 1, 7)
        by_id = {p["id"][-3:]: p for p in plans}
        self.assertEqual(by_id["L09"]["rpt_dates"], by_id["L08"]["rpt_dates"])
        self.assertIn("spiracles", by_id["L19"]["success_criteria"])
        self.assertIn("starch", by_id["L25"]["success_criteria"])

    def test_shadow_lessons_cover_both_size_and_shape_factors(self):
        plans = {plan["id"]: plan for plan in load_plans()}
        size = plans["DLP-SCI-Y4-L30"]
        self.assertEqual(size["references"], ["TB p. 92"])
        self.assertIn("two torch positions", size["phases"][1]["teacher"])
        self.assertIn("two screen positions", size["phases"][1]["teacher"])
        self.assertIn("shadow widths in cm", size["phases"][1]["pupils"])
        shape = plans["DLP-SCI-Y4-L31"]
        self.assertEqual(shape["references"], ["TB p. 93"])
        self.assertIn("rotating the card", shape["phases"][1]["teacher"])
        self.assertIn("torch off to one side", shape["phases"][1]["teacher"])
        self.assertIn("straight path", shape["phases"][2]["teacher"])
