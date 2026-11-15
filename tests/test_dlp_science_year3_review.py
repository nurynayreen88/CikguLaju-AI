"""Verify the Year 3 DLP review plans against their annual schedules."""

from io import BytesIO
from pathlib import Path
import re
import unittest

from docx import Document
from pypdf import PdfReader

from dlp_year2_rph import render

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "staging" / "dlp" / "year3"
RPT = ROOT / "rpt_2027" / "dlp" / "CikguLaju_RPT_DLP_2027_Science_Year_3.docx"
PLAN_HEADING = re.compile(r"^## (DLP-(?:SCI|MAT)-Y3-(?:U\d{2}-\d{2}|R\d{2})) · (.+)$", re.M)
FIELDS = {
    "Standards": "standards",
    "References": "references",
    "Learning objective": "objective",
    "Materials": "materials",
    "Reflection": "reflection",
}


def review_plans(pattern="science_*.md"):
    for source in sorted(SOURCE.glob(pattern)):
        text = source.read_text(encoding="utf-8")
        unit_title = text.splitlines()[0].split(" · ")[-1]
        sections = PLAN_HEADING.split(text)
        for index in range(1, len(sections), 3):
            lesson_id, title, body = sections[index:index + 3]
            lesson = {"id": lesson_id, "title": title}
            for label, field in FIELDS.items():
                lesson[field] = re.search(rf"^\*\*{label}\*\* · (.+)$", body, re.M)[1].strip()
            lesson["phases"] = re.findall(
                r"^\| ([^|]+ · \d+ min) \| ([^|]+) \| ([^|]+) \|$", body, re.M
            )
            yield {"title": unit_title}, lesson


def schedule():
    lessons = {}
    reviews = 0
    for table in Document(RPT).tables:
        for row in table.rows:
            cells = [" ".join(cell.text.split()) for cell in row.cells]
            if len(cells) != 5:
                continue
            _, title, standards, _, reference = cells
            if match := re.fullmatch(r"Lesson (\d+) (.+) (Unit (\d+) .+)", title):
                number, topic, unit, unit_no = match.groups()
                lesson_id = f"DLP-SCI-Y3-U{int(unit_no):02d}-{number}"
                cs, ls = re.fullmatch(r"CS (.+) LS (.+)", standards).groups()
                standards = f"CS {cs} · LS {ls}"
            elif match := re.fullmatch(r"Review (.+) Consolidation", title):
                reviews += 1
                lesson_id, topic, unit = f"DLP-SCI-Y3-R{reviews:02d}", f"Review: {match[1]}", "Consolidation"
                standards = None
            else:
                continue
            minutes = int(re.search(r"(\d+) min$", reference)[1])
            lessons[lesson_id] = (unit, topic, standards, minutes)
    return lessons


class ScienceYear3DlpReviewTests(unittest.TestCase):
    def test_plans_cover_rpt_and_all_dskp_standards(self):
        expected = schedule()
        covered = set()
        ids = set()
        total = 0
        for unit, lesson in review_plans():
            with self.subTest(lesson=lesson["id"]):
                self.assertNotIn(lesson["id"], ids)
                ids.add(lesson["id"])
                unit_title, title, standards, minutes = expected[lesson["id"]]
                self.assertEqual((unit["title"], lesson["title"]), (unit_title, title))
                if standards is not None:
                    self.assertEqual(lesson["standards"], standards)
                    self.assertIn("Activity Book pp.", lesson["references"])
                    covered.update(re.findall(r"\d+\.\d+\.\d+", standards))
                self.assertIn("Textbook pp.", lesson["references"])
                phases = lesson["phases"]
                self.assertEqual([phase.split(" · ")[0] for phase, _, _ in phases], [
                    "Set induction", "Main activity", "Practice and assessment", "Closure",
                ])
                self.assertEqual(sum(int(phase.rsplit(" ", 2)[1]) for phase, _, _ in phases), minutes)
                total += minutes
        self.assertEqual(ids, set(expected))
        self.assertEqual(len(ids), 56)
        self.assertEqual(len(covered), 60)
        self.assertEqual(total, 2880)

    def test_every_review_plan_renders_one_page_a4_pdf_and_word(self):
        teacher = {"class": "3 Bestari", "date": "2027-01-04", "time": "07:30 - 08:30", "students": "30"}
        for unit, lesson in review_plans():
            with self.subTest(lesson=lesson["id"]):
                pdf = PdfReader(BytesIO(render("SCIENCE_DLP", unit, lesson, "pdf", teacher, year=3)))
                self.assertEqual(len(pdf.pages), 1)
                page = pdf.pages[0]
                self.assertAlmostEqual(float(page.mediabox.width), 595.28, places=1)
                self.assertAlmostEqual(float(page.mediabox.height), 841.89, places=1)
                self.assertIn("Year 3 SK", page.extract_text())
                self.assertIn("Reflection", page.extract_text())
                word = Document(BytesIO(render("SCIENCE_DLP", unit, lesson, "word", teacher, year=3)))
                self.assertAlmostEqual(word.sections[0].page_width.mm, 210, places=1)
                self.assertAlmostEqual(word.sections[0].page_height.mm, 297, places=1)
                self.assertIn("Year 3 SK", word.paragraphs[1].text)
                self.assertEqual(word.tables[1].cell(3, 0).text, lesson["phases"][2][0])


class MathematicsYear3DlpReviewTests(unittest.TestCase):
    def test_unit_two_matches_rpt_and_renders_word_and_pdf(self):
        rpt = RPT.with_name(RPT.name.replace("Science", "Mathematics"))
        expected = {}
        for table in Document(rpt).tables:
            for row in table.rows:
                cells = [" ".join(cell.text.split()) for cell in row.cells]
                if len(cells) != 5:
                    continue
                _, title, standards, _, references = cells
                if match := re.fullmatch(r"Lesson (\d+) (.+) Unit 2 Addition, Subtraction, Multiplication and Division", title):
                    number, topic = match.groups()
                    lesson_id = f"DLP-MAT-Y3-U02-{number}"
                    cs, ls = re.fullmatch(r"CS (.+) LS (.+)", standards).groups()
                    standards = f"CS {cs} · LS {ls}"
                elif title == "Review Basic Operations Consolidation":
                    lesson_id, topic, standards = "DLP-MAT-Y3-R02", "Review: Basic Operations", None
                else:
                    continue
                time = int(re.search(r"(\d+) min$", references)[1])
                expected[lesson_id] = topic, standards, time
        available = set()
        covered = set()
        total = 0
        teacher = {"class": "", "date": "", "time": "", "students": ""}
        for unit, plan in review_plans("mathematics_unit_02.md"):
            with self.subTest(lesson=plan["id"]):
                self.assertNotIn(plan["id"], available)
                available.add(plan["id"])
                topic, standards, minutes = expected[plan["id"]]
                self.assertEqual(plan["title"], topic)
                if standards is not None:
                    self.assertEqual(plan["standards"], standards)
                    covered.update(re.findall(r"2\.\d+\.\d+", plan["standards"]))
                self.assertIn("Textbook Part 1", plan["references"])
                self.assertIn("Activity Book", plan["references"])
                self.assertEqual(len(plan["phases"]), 4)
                self.assertEqual(sum(int(phase.rsplit(" ", 2)[1]) for phase, _, _ in plan["phases"]), minutes)
                total += minutes
                pdf = PdfReader(BytesIO(render("MATH_DLP", unit, plan, "pdf", teacher, year=3)))
                self.assertEqual(len(pdf.pages), 1)
                self.assertIn("Mathematics (DLP)", pdf.pages[0].extract_text())
                word = Document(BytesIO(render("MATH_DLP", unit, plan, "word", teacher, year=3)))
                self.assertEqual(word.paragraphs[2].text, topic)
        self.assertEqual(available, set(expected))
        self.assertEqual(len(available), 15)
        self.assertEqual(len(covered), 12)
        self.assertEqual(total, 1230)
