"""Compare the Science and Mathematics review exports with their 2027 RPTs."""

from collections import Counter
import json
from pathlib import Path
import re
from shutil import which
from subprocess import run
from tempfile import TemporaryDirectory
import unittest

from docx import Document
from pypdf import PdfReader

from staging.dlp.year5 import render_mathematics, render_science


INTERNAL_LABEL = re.compile(
    r"\b(?:draf(?:t)?|produksi|production|staging|semakan guru|teacher review)\b",
    re.IGNORECASE,
)


def normalized(text):
    return " ".join(text.split())


class DLPYear5ReviewExports(unittest.TestCase):
    def test_mathematics(self):
        self.check_set(render_mathematics, "Mathematics", render_mathematics.official_rows,
                       61, 8, 96, 23, 8)

    def test_science(self):
        self.check_set(render_science, "Science", render_science.schedule_rows,
                       60, 10, 64, 8, 7)

    def check_set(self, module, subject, rows, lessons, reviews, hours, edits, rpt_pages):
        source = rows(Document(module.RPT))
        rpt, plans = module.load_plans()
        self.assertEqual(Counter(plan["id"][0] for plan in plans), {"L": lessons, "R": reviews})
        data = json.loads(module.DATA.read_text(encoding="utf-8"))
        corrections = data.get("schedule_corrections", data.get("reference_corrections"))
        descriptions = (
            json.loads(module.STANDARD_DESCRIPTIONS.read_text(encoding="utf-8"))
            if subject == "Science" else None
        )
        changed = set()
        minutes = 0
        for original, updated, plan in zip(source, rows(rpt), plans, strict=True):
            before = [cell.text for cell in original.cells]
            after = [cell.text for cell in updated.cells]
            self.assertEqual(before[0], after[0])
            self.assertEqual(normalized(before[0].replace("\n", " · ")), normalized(plan["dates"]))
            self.assertEqual(before[2], after[2])
            self.assertEqual(before[4].splitlines()[-1], after[4].splitlines()[-1])
            self.assertEqual(after[3], plan["objective"])
            self.assertEqual(after[4].splitlines()[0].replace("TB ", "Textbook ", 1), plan["reference"])
            if descriptions is not None:
                expected_codes = (
                    re.findall(r"\d+\.\d+\.\d+", before[2]) if plan["id"].startswith("L")
                    else data["review_standards"][plan["id"]]
                )
                content_codes = tuple(dict.fromkeys(code.rsplit(".", 1)[0] for code in expected_codes))
                expected_content = " · ".join(f"{code} {descriptions['cs'][code]}" for code in content_codes)
                expected_learning = " · ".join(f"{code} {descriptions['ls'][code]}" for code in expected_codes)
                self.assertEqual(plan["content_standards"], expected_content)
                self.assertEqual(plan["learning_standards"], expected_learning)
            if before != after:
                changed.add(plan["id"])
            duration = int(after[4].splitlines()[-1].removesuffix(" min"))
            self.assertEqual(sum(int(phase.split()[-2]) for phase, *_ in plan["phases"]), duration)
            minutes += duration
        self.assertEqual(changed, set(corrections))
        self.assertEqual(len(changed), edits)
        self.assertEqual(minutes, hours * 60)

        with TemporaryDirectory(prefix="dlp_year5_review_") as directory:
            folder = Path(directory)
            module.export(folder, rpt, plans)
            word_pdfs = folder / "word_pdfs"
            if which("soffice"):
                word_pdfs.mkdir()
                run([
                    "soffice", f"-env:UserInstallation={(folder / 'lo_profile').as_uri()}",
                    "--headless", "--convert-to", "pdf", "--outdir", str(word_pdfs),
                    *map(str, sorted(folder.glob("*.docx"))),
                ], check=True, timeout=180, capture_output=True, text=True)
                rpt_pdf = word_pdfs / f"{module.RPT_NAME}_Teacher_Review.pdf"
                self.check_pdf(rpt_pdf, rpt_pages, (842, 595))

            for plan in plans:
                with self.subTest(subject=subject, lesson=plan["id"]):
                    stem = f"CikguLaju_RPH_{subject}_DLP_Y5_{plan['id']}"
                    word = Document(folder / f"{stem}.docx")
                    self.assertEqual(word.tables[2].rows[0].cells[1].text, plan["evidence"])
                    table = word.tables[1]
                    fields = {row.cells[0].text: row.cells[1].text for row in word.tables[0].rows}
                    self.assertNotIn("RPT date ranges", fields)
                    if subject == "Mathematics":
                        self.assertEqual(fields["Topic"], plan["title"])
                    else:
                        self.assertEqual(fields["Content Standards"], plan["content_standards"])
                        self.assertEqual(fields["Learning Standards"], plan["learning_standards"])
                        self.assertEqual(word.paragraphs[2].text, plan["title"])
                    text = "\n".join(row.cells[1].text for row in table.rows[1:])
                    for _, teacher, pupils in plan["phases"]:
                        self.assertIn(f"Teacher: {teacher}\nPupils: {pupils}", text)
                    standard_fields = (
                        ("content_standards", "learning_standards") if subject == "Science" else ("standards",)
                    )
                    for pdf_folder in (folder, word_pdfs) if word_pdfs.exists() else (folder,):
                        self.assertNotRegex(stem.replace("_", " "), INTERNAL_LABEL)
                        content = self.check_pdf(pdf_folder / f"{stem}.pdf", 1, (595, 842))
                        self.assertNotIn("RPT date ranges", content)
                        self.assertIn(normalized(plan["label"].rsplit(" · ", 1)[0]), content)
                        for field in ("title", *standard_fields, "reference", "objective", "evidence"):
                            self.assertIn(normalized(plan[field]), content)

    def check_pdf(self, path, count, size):
        doc = PdfReader(path)
        self.assertEqual(len(doc.pages), count, path.name)
        text = []
        for page in doc.pages:
            self.assertAlmostEqual(float(page.mediabox.width), size[0], delta=1)
            self.assertAlmostEqual(float(page.mediabox.height), size[1], delta=1)
            content = normalized(page.extract_text())
            self.assertTrue(content, path.name)
            self.assertNotRegex(content, INTERNAL_LABEL)
            text.append(content)
        return " ".join(text)
