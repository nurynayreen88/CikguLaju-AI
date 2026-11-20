"""Verify each 2027 Mathematics DLP Year 6 review export against its RPT."""

from collections import Counter
from io import BytesIO
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from docx import Document
from flask import Flask
from pypdf import PdfReader

from dlp_year2_rph import mathematics_standard_rows
from staging.dlp.year6.render_mathematics import DATA, RPT, RPT_NAME, export, load_plans, official_rows
from web.native_rph_telegram_api import create_native_rph_blueprint


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
                details = {row.cells[0].text: row.cells[1].text for row in word.tables[0].rows}
                self.assertEqual(details["Topic"], plan["title"])
                self.assertEqual(details["Lesson / PdP"], plan["label"].rsplit(" · ", 1)[0])
                self.assertNotIn("RPT date ranges", details)
                standards = mathematics_standard_rows(6, plan["standards"])
                for label, description in standards:
                    self.assertEqual(details[label], description)
                for label, key in (("Book reference", "reference"),
                                   ("Learning objective", "objective")):
                    self.assertEqual(details[label], plan[key])
                self.assertEqual(word.tables[2].rows[0].cells[1].text, plan["evidence"])
                self.assertEqual(sum(int(phase.split()[-2]) for phase, *_ in plan["phases"]),
                                 plan["minutes"])
                table = word.tables[1]
                self.assertEqual(len(table.rows), 4)
                activities = "\n".join(row.cells[1].text for row in table.rows[1:])
                for _, teacher, pupils in plan["phases"]:
                    self.assertIn(f"Teacher: {teacher}\nPupils: {pupils}", activities)

                pdf = PdfReader(self.output / f"{stem}.pdf")
                self.assertEqual(len(pdf.pages), 1)
                page = pdf.pages[0]
                self.assertAlmostEqual(float(page.mediabox.width), 595.28, places=1)
                self.assertAlmostEqual(float(page.mediabox.height), 841.89, places=1)
                page_text = " ".join(page.extract_text().split())
                self.assertIn(plan["label"].rsplit(" · ", 1)[0], page_text)
                self.assertNotIn("RPT date ranges", page_text)
                for _, description in standards:
                    self.assertIn(" ".join(description.split()), page_text)
                for field in ("title", "reference", "objective", "evidence"):
                    self.assertIn(" ".join(plan[field].split()), page_text)


class MathematicsDLPYear6DownloadTests(unittest.TestCase):
    PATH = "/internal/rph/v1/dlp"

    def setUp(self):
        app = Flask(__name__)
        runtime = SimpleNamespace(create_word_file=lambda: None, create_pdf_file=lambda: None)
        app.register_blueprint(create_native_rph_blueprint(runtime))
        self.client = app.test_client()
        token = "t" * 40
        self.headers = {"Authorization": f"Bearer {token}"}
        configuration = patch.dict(os.environ, {
            "CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN": token,
        })
        configuration.start()
        self.addCleanup(configuration.stop)
        self.teacher = {"class": "6 Bestari", "date": "2027-10-18", "time": "08:00 - 09:30",
                        "students": "30", "reflection": "Pupils explained their methods."}

    def _render(self, selection, fmt):
        return self.client.post(self.PATH + "/render", headers=self.headers, json={
            "selection": selection, "format": fmt, "teacher": self.teacher,
        })

    def test_protected_catalogue_downloads_every_exact_rpt_plan(self):
        catalogue_path = self.PATH + "/year6-mathematics/catalogue"
        self.assertEqual(self.client.get(catalogue_path).status_code, 401)
        catalogue = self.client.get(catalogue_path, headers=self.headers).json
        self.assertEqual(catalogue["year"], 6)
        self.assertEqual(catalogue["subject"], "MATH_DLP")
        self.assertEqual(len(catalogue["units"]), 8)
        _, plans = load_plans()
        expected = {f"DLP-MATH-Y6-{p['id']}": p for p in plans}
        ids = []
        for unit in catalogue["units"]:
            for row in unit["lessons"]:
                key = row["id"]
                ids.append(key)
                with self.subTest(lesson=key):
                    plan = expected[key]
                    standards = mathematics_standard_rows(6, plan["standards"])
                    self.assertEqual(unit["title"], plan["unit"])
                    self.assertEqual(row, {"id": key, "title": plan["title"], "label": plan["label"],
                                           "book_reference": plan["reference"], "minutes": plan["minutes"]})
                    selection = {"year": 6, "subject": "MATH_DLP", "unit": unit["id"], "lesson": key}
                    response = self.client.get(self.PATH + "/availability", headers=self.headers,
                                               query_string=selection)
                    self.assertEqual(response.json, {"available": True, "formats": ["word", "pdf"]})
                    for fmt, suffix in (("word", "docx"), ("pdf", "pdf")):
                        response = self._render(selection, fmt)
                        self.assertEqual(response.status_code, 200)
                        self.assertEqual(response.headers["Cache-Control"], "no-store, private")
                        self.assertIn(f"CIKGULAJU_RPH_{key}.{suffix}", response.headers["Content-Disposition"])
                        if fmt == "word":
                            doc = Document(BytesIO(response.data))
                            details = {a.text: b.text for a, b in (row.cells for row in doc.tables[0].rows)}
                            self.assertEqual(details["Topic"], plan["title"])
                            for label, description in standards:
                                self.assertEqual(details[label], description)
                            self.assertEqual(doc.tables[2].rows[0].cells[1].text, plan["evidence"])
                            self.assertEqual(doc.tables[2].rows[1].cells[1].text, self.teacher["reflection"])
                            text = " ".join(details.values())
                        else:
                            pdf = PdfReader(BytesIO(response.data))
                            self.assertEqual(len(pdf.pages), 1)
                            text = " ".join(pdf.pages[0].extract_text().split())
                            for _, description in standards:
                                self.assertIn(" ".join(description.split()), text)
                            for field in ("title", "reference", "evidence"):
                                self.assertIn(" ".join(plan[field].split()), text)
                        self.assertIn(plan["label"].rsplit(" · ", 1)[0], text)
                        self.assertNotIn(plan["label"].rsplit(" · ", 1)[0] + " · 90 min", text)
                        for value in ("6 Bestari", "18/10/2027", "08:00 - 09:30", "30"):
                            self.assertIn(value, text)
        self.assertEqual(ids, list(expected))

    def test_wrong_unit_lesson_subject_and_year_do_not_render(self):
        selection = {"year": 6, "subject": "MATH_DLP", "unit": "01", "lesson": "DLP-MATH-Y6-L01"}
        for field, value in (("unit", "02"), ("lesson", "DLP-MATH-Y6-L99"),
                             ("subject", "SCIENCE_DLP"), ("year", 5)):
            with self.subTest(field=field):
                self.assertEqual(self._render(selection | {field: value}, "pdf").status_code, 404)

    def test_unverified_source_produces_no_catalogue_or_document(self):
        selection = {"year": 6, "subject": "MATH_DLP", "unit": "01", "lesson": "DLP-MATH-Y6-L01"}
        with patch("staging.dlp.year6.render_mathematics._download_units",
                   side_effect=ValueError("Source RPT changed")):
            catalogue = self.client.get(self.PATH + "/year6-mathematics/catalogue", headers=self.headers)
            self.assertEqual(catalogue.status_code, 503)
            self.assertEqual(self._render(selection, "word").status_code, 503)


if __name__ == "__main__":
    unittest.main()
