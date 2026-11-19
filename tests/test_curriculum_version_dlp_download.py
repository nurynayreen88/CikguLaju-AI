"""Check the private Telegram DLP file endpoint and published lesson binding."""

from io import BytesIO
from pathlib import Path
import re
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from docx import Document
from flask import Flask
from pypdf import PdfReader

from dlp_year2_rph import catalog, render, resolve, rpt_lessons, science_rpt_lessons
from staging.dlp.year2.downloads import BY_SUBJECT
from web.native_rph_telegram_api import create_native_rph_blueprint


class DlpDownloadTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        runtime = SimpleNamespace(create_word_file=lambda: None, create_pdf_file=lambda: None)
        app.register_blueprint(create_native_rph_blueprint(runtime))
        self.client = app.test_client()
        self.path = "/internal/rph/v1/dlp"
        self.selection = {"year": 2, "subject": "SCIENCE_DLP", "unit": "10",
                          "lesson": "DLP-SCI-Y2-U10-06"}
        self.teacher = {"class": "2 Bestari", "date": "2026-11-16", "time": "10:00 - 11:00",
                        "students": "30", "reflection": "Teacher’s note: <check> & review."}
        token = "t" * 40
        self.headers = {"Authorization": f"Bearer {token}"}
        env = patch.dict("os.environ", {
            "CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN": token,
        })
        env.start()
        self.addCleanup(env.stop)

    def download(self, fmt, selection=None, teacher=None):
        return self.client.post(self.path + "/render", headers=self.headers, json={
            "format": fmt, "selection": selection or self.selection, "teacher": teacher or self.teacher,
        })

    def test_readiness_has_no_teaching_content_and_resolves_exact_key(self):
        for subject, units in catalog().items():
            for unit in units:
                for lesson in unit["lessons"]:
                    self.assertEqual(resolve(2, subject, unit["id"], lesson["id"]), (unit, lesson))
        route = self.path + "/availability"
        self.assertEqual(self.client.get(route, query_string=self.selection).status_code, 401)
        available = self.client.get(route, query_string=self.selection, headers=self.headers)
        self.assertEqual(available.json, {"available": True, "formats": ["word", "pdf"]})
        for field, value in (("year", 3), ("subject", "MATH_DLP"), ("unit", "09"),
                             ("lesson", "DLP-SCI-Y2-U10-99")):
            selection = self.selection | {field: value}
            self.assertEqual(self.client.get(route, query_string=selection, headers=self.headers).status_code, 404)
            self.assertEqual(self.download("pdf", selection=selection).status_code, 404)

    def test_download_attaches_real_files_and_prints_teacher_details(self):
        word = self.download("word")
        self.assertEqual(word.status_code, 200)
        self.assertIn('attachment; filename="CIKGULAJU_RPH_DLP-SCI-Y2-U10-06.docx"',
                      word.headers["Content-Disposition"])
        doc = Document(BytesIO(word.data))
        self.assertEqual(doc.paragraphs[2].text, "Explain Observations About a Built Model")
        fields = {left.text: right.text for left, right in (row.cells for row in doc.tables[0].rows)}
        self.assertIn("2 Bestari", fields["Class / date / time"])
        self.assertIn("LS 10.1.6", fields["Standards"])
        self.assertEqual(doc.tables[-1].cell(0, 1).text, self.teacher["reflection"])
        self.assertEqual(len(doc.tables[1].rows), 5)
        pdf = self.download("pdf")
        self.assertEqual(pdf.status_code, 200)
        self.assertEqual(pdf.mimetype, "application/pdf")
        self.assertTrue(pdf.data.startswith(b"%PDF-"))
        self.assertEqual(pdf.headers["Cache-Control"], "no-store, private")
        self.assertEqual(self.download("pdf", teacher=self.teacher | {"class": "X" * 41}).status_code, 400)
        self.assertEqual(self.download("pdf", teacher=self.teacher | {"reflection": "x\ny\nz\n1\n2\n3\n4"}).status_code, 400)
        self.assertEqual(self.client.post(self.path + "/render", json={}).status_code, 401)

    def test_science_lesson_numbers_standards_and_minutes_match_the_rpt(self):
        planned = Path(__file__).resolve().parents[1] / "rpt_2027" / "dlp"
        rpt = Document(planned / "CikguLaju_RPT_DLP_2027_Science_Year_2.docx")
        rows = [row for row in rpt.tables[2].rows[1:] if row.cells[1].text.startswith("Lesson ")]
        lessons = [(unit, lesson) for unit in catalog()["SCIENCE_DLP"] for lesson in unit["lessons"]]
        self.assertEqual(len(science_rpt_lessons()), len(rows))
        for row, (unit, lesson) in zip(rows, lessons, strict=True):
            with self.subTest(lesson=lesson["id"]):
                title, unit_title = row.cells[1].text.splitlines()
                number = int(title.split()[1])
                minutes = int(row.cells[4].text.splitlines()[-1].split()[0])
                self.assertEqual(unit_title, unit["title"])
                self.assertEqual(title, f"Lesson {number:02d}  {lesson['title']}")
                codes = r"\b\d+(?:\.\d+)+\b"
                self.assertEqual(re.findall(codes, row.cells[2].text),
                                 re.findall(codes, lesson["standards"]))
                references = (row.cells[4].text.rsplit("\n", 1)[0]
                              .replace("TB ", "Textbook ").replace("AB ", "Activity Book ")
                              .replace("\n", " · "))
                self.assertEqual(references, lesson["references"])
                word = Document(BytesIO(render("SCIENCE_DLP", unit, lesson, "word", self.teacher)))
                self.assertEqual(word.tables[0].cell(1, 1).text, f"Lesson {number:02d} · {minutes} min")
                activities = word.tables[1].rows[1:]
                self.assertEqual(sum(int(r.cells[0].text.split()[-2]) for r in activities), minutes)
                self.assertEqual(
                    [[cell.text for cell in r.cells[1:]] for r in activities],
                    [phase[1:] for phase in lesson["phases"]],
                )

    def test_mathematics_lessons_match_the_year_two_rpt(self):
        folder = Path(__file__).resolve().parents[1] / "rpt_2027" / "dlp"
        rpt = Document(folder / "CikguLaju_RPT_DLP_2027_Mathematics_Year_2.docx")
        rows = [row for row in rpt.tables[2].rows[1:] if row.cells[1].text.startswith("Lesson ")]
        lessons = [(unit, lesson) for unit in catalog()["MATH_DLP"] for lesson in unit["lessons"]]
        schedule = rpt_lessons("MATH_DLP")
        self.assertEqual(len(schedule), 78)
        for number, (row, (unit, lesson)) in enumerate(zip(rows, lessons, strict=True), 1):
            with self.subTest(lesson=lesson["id"]):
                self.assertEqual(row.cells[1].text, f"Lesson {number:02d}  {lesson['title']}\n{unit['title']}")
                self.assertEqual(row.cells[2].text, lesson["standards"].replace(" · ", "\n"))
                self.assertEqual(row.cells[3].text, lesson["objective"])
                references = lesson["references"].replace("Textbook ", "TB ").replace("Activity Book ", "AB ")
                self.assertEqual(row.cells[4].text, references.replace(" · ", "\n") + "\n60 min")
                self.assertEqual(schedule[lesson["id"]], {"number": number, "minutes": 60})
                doc = Document(BytesIO(render("MATH_DLP", unit, lesson, "word", self.teacher)))
                fields = {a.text: b.text for a, b in (row.cells for row in doc.tables[0].rows)}
                self.assertEqual(fields["Lesson / PdP"], f"Lesson {number:02d} · 60 min")

    def test_year_two_catalogues_download_all_lessons_and_reviews(self):
        for slug, subject, units_count, count in (
            ("science", "SCIENCE_DLP", 10, 67), ("mathematics", "MATH_DLP", 8, 96),
        ):
            catalogue = f"{self.path}/year2-{slug}/catalogue"
            self.assertEqual(self.client.get(catalogue).status_code, 401)
            reply = self.client.get(catalogue, headers=self.headers)
            self.assertEqual(reply.status_code, 200)
            units = reply.json["units"]
            self.assertEqual((reply.json["year"], reply.json["subject"]), (2, subject))
            self.assertEqual(len(units), units_count)
            self.assertEqual(sum(len(unit["lessons"]) for unit in units), count)
            for unit in units:
                for item in unit["lessons"]:
                    with self.subTest(lesson=item["id"]):
                        selection = {"year": 2, "subject": subject, "unit": unit["id"],
                                     "lesson": item["id"]}
                        _, plan = BY_SUBJECT[subject].resolve_download(unit["id"], item["id"])
                        teacher = self.teacher | {"time": ""} if subject == "MATH_DLP" else self.teacher
                        word = self.download("word", selection=selection, teacher=teacher)
                        self.assertEqual(word.status_code, 200)
                        doc = Document(BytesIO(word.data))
                        fields = {a.text: b.text for a, b in (row.cells for row in doc.tables[0].rows)}
                        teacher_field = "Class" if subject == "MATH_DLP" else "Class / date / time"
                        self.assertIn("2 Bestari", fields[teacher_field])
                        self.assertEqual(fields["Learning objective"], plan["objective"])
                        self.assertEqual(fields["RPT 2027 dates"], " · ".join(plan["rpt_dates"]))
                        self.assertEqual(fields["Lesson / PdP"], f"{item['label']} · {item['minutes']} min")
                        table = doc.tables[1]
                        if subject == "MATH_DLP":
                            self.assertEqual(len(table.rows), 4)
                            self.assertEqual([cell.text for cell in table.rows[0].cells],
                                             ["Phase / Time", "Teaching and Learning Activities", "Notes"])
                            headings = [run.text for run in table.cell(2, 1).paragraphs[0].runs
                                        if run.bold]
                            self.assertEqual(len(headings), len(plan["phases"]) - 2)
                            timed = [table.cell(1, 0).text, *headings, table.cell(3, 0).text]
                            minutes = sum(int(re.search(r"\((\d+) min\)$", phase)[1]) for phase in timed)
                            activity_text = "\n".join(row.cells[1].text for row in table.rows[1:])
                            for _, teacher_action, pupil_action in plan["phases"]:
                                self.assertIn(f"Teacher: {teacher_action}\nPupils: {pupil_action}",
                                              activity_text)
                        else:
                            self.assertEqual(len(table.rows), 5)
                            minutes = sum(int(row.cells[0].text.split()[-2]) for row in table.rows[1:])
                        self.assertEqual(minutes, item["minutes"])
                        pdf = self.download("pdf", selection=selection, teacher=teacher)
                        self.assertEqual(pdf.status_code, 200)
                        page, = PdfReader(BytesIO(pdf.data)).pages
                        self.assertAlmostEqual(float(page.mediabox.width), 595.28, delta=1)
                        self.assertAlmostEqual(float(page.mediabox.height), 841.89, delta=1)

    def test_mathematics_rpt_keeps_96_hours_before_assessment(self):
        folder = Path(__file__).resolve().parents[1] / "rpt_2027" / "dlp"
        for year, row_count in ((2, 96), (3, 82), (4, 77), (5, 69), (6, 54)):
            with self.subTest(year=year):
                rpt = Document(folder / f"CikguLaju_RPT_DLP_2027_Mathematics_Year_{year}.docx")
                rows = rpt.tables[2].rows[1:]
                self.assertEqual(len(rows), row_count)
                self.assertEqual(sum(int(row.cells[4].text.splitlines()[-1].split()[0]) for row in rows), 5760)
                windows = list(dict.fromkeys(row.cells[0].text for row in rows))
                self.assertEqual(len(windows), 35)
                self.assertEqual(windows[-1], "A  17-21 Oct\nB  18-22 Oct")
                self.assertFalse(any(re.search(r"\b(?:9-13|10-14|16-20|17-21) May\b", dates) for dates in windows))
