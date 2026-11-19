"""Check the Science DLP Year 3 lesson plans against the published RPT."""

import hashlib
from io import BytesIO
import json
from pathlib import Path
import unittest

from docx import Document
from pypdf import PdfReader

from dlp_year2_rph import render, resolve, subject_units


ROOT = Path(__file__).resolve().parents[1]
SCIENCE = "SCIENCE_DLP"


class DlpScienceYear3Tests(unittest.TestCase):
    def test_every_rpt_row_has_one_exact_review_document(self):
        source = ROOT / "staging" / "dlp" / "year3" / "science_2027.json"
        data = json.loads(source.read_text(encoding="utf-8"))
        descriptions = json.loads(source.with_name("science_standard_descriptions.json").read_text(encoding="utf-8"))
        rpt = ROOT / "rpt_2027" / "dlp" / "CikguLaju_RPT_DLP_2027_Science_Year_3.docx"
        self.assertEqual(data["rpt_file"], rpt.name)
        self.assertEqual(data["rpt_sha256"], hashlib.sha256(rpt.read_bytes()).hexdigest())
        self.assertEqual((data["year"], data["planning_year"], data["subject"]), (3, 2027, SCIENCE))
        plans = data["plans"]
        rows = Document(rpt).tables[2].rows[1:]
        self.assertEqual(len(plans), 56)
        self.assertEqual(sum(plan["minutes"] for plan in plans), 48 * 60)
        self.assertEqual(len({plan["id"] for plan in plans}), 56)
        groups = subject_units(3, SCIENCE)
        unit_for_lesson = {lesson["id"]: unit["id"] for unit in groups for lesson in unit["lessons"]}
        self.assertEqual(len(unit_for_lesson), 56)
        self.assertEqual(subject_units(3, "MATH_DLP"), ())
        self.assertIsNone(resolve(2, SCIENCE, "01", "DLP-SCI-Y3-01"))
        teacher = {"class": "3 Bestari", "date": "2027-01-05", "time": "09:00–09:30", "students": "29"}
        reviews = 0
        taught = set()
        for row, plan in zip(rows, plans, strict=True):
            with self.subTest(plan=plan["id"]):
                dates, caption, standards, pbd, books = (c.text for c in row.cells)
                lesson_text, unit_text = caption.splitlines()
                lesson_label, lesson_title = lesson_text.split("  ", 1)
                if lesson_label == "Review":
                    reviews += 1
                    lesson_label = f"Review {reviews:02d}"
                    ls_codes = descriptions["review_ls"][plan["id"]]
                    self.assertTrue(set(ls_codes) <= taught)
                    cs_codes = list(dict.fromkeys(code.rsplit(".", 1)[0] for code in ls_codes))
                else:
                    cs, ls = standards.splitlines()
                    cs_codes = cs.removeprefix("CS ").split(", ")
                    ls_codes = ls.removeprefix("LS ").split(", ")
                    taught.update(ls_codes)
                self.assertEqual({code.rsplit(".", 1)[0] for code in ls_codes}, set(cs_codes))
                self.assertEqual((lesson_label, lesson_title, unit_text),
                                 (plan["label"], plan["title"], plan["unit"]))
                self.assertEqual(dates.splitlines(), plan["rpt_dates"])
                self.assertEqual(standards.splitlines(), plan["standards"])
                self.assertEqual(pbd, plan["objective"])
                self.assertEqual(books.splitlines(), [*plan["references"], f"{plan['minutes']} min"])
                self.assertEqual(sum(phase["minutes"] for phase in plan["phases"]), plan["minutes"])
                self.assertEqual(len(plan["phases"]), 4)
                self.assertTrue(all(phase["teacher"] and phase["pupils"] for phase in plan["phases"]))
                unit_id = unit_for_lesson[plan["id"]]
                unit, lesson = resolve(3, SCIENCE, unit_id, plan["id"])
                self.assertIsNone(resolve(3, SCIENCE, "invalid", plan["id"]))
                word = Document(BytesIO(render(SCIENCE, unit, lesson, "word", teacher)))
                details = {a.text: b.text for a, b in (r.cells for r in word.tables[0].rows)}
                content_text = "\n".join(f"{code} {descriptions['cs'][code]}" for code in cs_codes)
                learning_text = "\n".join(f"{code} {descriptions['ls'][code]}" for code in ls_codes)
                self.assertEqual(details["Content Standards"], content_text)
                self.assertEqual(details["Learning Standards"], learning_text)
                self.assertEqual(details["Learning objective"], pbd)
                self.assertEqual(details["Lesson / PdP"], lesson_label)
                self.assertEqual(details["RPT 2027 dates"], " · ".join(plan["rpt_dates"]))
                phases = [r.cells[0].text for r in word.tables[1].rows[1:]]
                self.assertEqual(phases, [phase["phase"] for phase in plan["phases"]])
                pdf = PdfReader(BytesIO(render(SCIENCE, unit, lesson, "pdf", teacher)))
                self.assertEqual(len(pdf.pages), 1)
                text = " ".join(pdf.pages[0].extract_text().split())
                for value in (content_text, learning_text):
                    self.assertIn(" ".join(value.split()), text)
        self.assertEqual(reviews, 4)
        self.assertEqual(taught, set(descriptions["ls"]))
