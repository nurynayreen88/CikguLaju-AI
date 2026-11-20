"""Check the Year 6 Science review exporters with real Word and PDF files."""

from collections import Counter
import json
from pathlib import Path
import re
from subprocess import run
from tempfile import TemporaryDirectory
import unittest

from docx import Document
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
SK = ROOT / "staging/sains/tahun6/eksport_2027.py"
DLP = ROOT / "staging/dlp/year6/render_science.py"


def check_pdf(test, path, pages, *, landscape=False):
    expected_size = (842, 595) if landscape else (595, 842)
    document = PdfReader(path)
    test.assertEqual(len(document.pages), pages, path.name)
    for page in document.pages:
        test.assertAlmostEqual(float(page.mediabox.width), expected_size[0], delta=1)
        test.assertAlmostEqual(float(page.mediabox.height), expected_size[1], delta=1)
        test.assertTrue(page.extract_text().strip(), path.name)


class ScienceYear6ReviewExports(unittest.TestCase):
    def check_exports(self, folder, titles, rpt_name, rpt_pages):
        word_files = sorted(folder.glob("*.docx"))
        self.assertEqual({path.stem for path in word_files}, {*titles, rpt_name})
        self.assertEqual({path.stem for path in folder.glob("*.pdf")}, set(titles))
        converted = folder / "word_pdf"
        converted.mkdir()
        run([
            "soffice", f"-env:UserInstallation={(folder / 'lo_profile').as_uri()}",
            "--headless", "--convert-to", "pdf", "--outdir", str(converted),
            *map(str, word_files),
        ], check=True, timeout=180, capture_output=True, text=True)
        check_pdf(self, converted / f"{rpt_name}.pdf", rpt_pages, landscape=True)
        for stem, title in titles.items():
            with self.subTest(document=stem):
                self.assertEqual(Document(folder / f"{stem}.docx").paragraphs[2].text, title)
                for path in (folder / f"{stem}.pdf", converted / f"{stem}.pdf"):
                    check_pdf(self, path, 1)

    def test_review_source_is_available(self):
        self.assertTrue(SK.is_file() or DLP.is_file())

    @unittest.skipUnless(SK.is_file(), "Sains SK draft is on its own branch")
    def test_all_sains_sk_exports(self):
        from staging.sains.tahun6.eksport_2027 import RPT_STEM, build_source, export_rph, export_rpt

        weeks, plans = build_source()
        self.assertEqual(len(weeks), 44)
        self.assertEqual([n for row in weeks for n in row["pdp"]], [*range(85, 90), *range(1, 85)])
        self.assertEqual(Counter(plan["minutes"] for plan in plans.values()), {30: 50, 60: 39})
        self.assertEqual(len({sp for plan in plans.values() for sp in plan["standards"]}), 96)
        self.assertEqual(plans[6]["sp_texts"], ["Memerihalkan sistem saraf pusat dan fungsinya."])
        self.assertEqual(plans[7]["sp_texts"], ["Menyatakan fungsi sistem saraf periferi."])
        self.assertEqual(plans[35]["sp_texts"], ["Memerihalkan kesan daya geseran."])
        self.assertIn("Mengeksperimen", plans[36]["sp_texts"][0])
        self.assertIn("lilitannya", plans[13]["phases"][1][2])
        self.assertIn("kiraan awal", plans[14]["phases"][2][2])
        self.assertIn("kiraan susulan", plans[16]["phases"][1][2])

        with TemporaryDirectory(prefix="sains_sk_tahun6_review_") as directory:
            folder = Path(directory)
            export_rpt(folder / f"{RPT_STEM}.docx", weeks, plans)
            for plan in plans.values():
                export_rph(folder, plan)
                stem = f"CikguLaju_RPH_Sains_SK_T6_PdP_{plan['id']:03d}"
                word = Document(folder / f"{stem}.docx")
                fields = {row.cells[0].text: row.cells[1].text for row in word.tables[0].rows}
                self.assertEqual(fields["Standard Kandungan"], f"{plan['sk']} {plan['sk_text']}")
                table = word.tables[1]
                self.assertEqual([cell.text for cell in table.rows[0].cells],
                                 ["Fasa", "Aktiviti Pengajaran & Pembelajaran", "Catatan"])
                activities = "\n".join(row.cells[1].text for row in table.rows[1:])
                for _, teacher, pupils in plan["phases"]:
                    self.assertIn(f"Guru: {teacher}\nMurid: {pupils}", activities)
                pdf = " ".join(PdfReader(folder / f"{stem}.pdf").pages[0].extract_text().split())
                self.assertIn("Fasa Aktiviti Pengajaran & Pembelajaran Catatan", pdf)
                for code, description in zip(plan["standards"], plan["sp_texts"], strict=True):
                    self.assertIn(f"{code} {description}", fields["Standard Pembelajaran"])
                    self.assertIn(f"{code} {description}", pdf)
            titles = {f"CikguLaju_RPH_Sains_SK_T6_PdP_{number:03d}": plan["title"]
                      for number, plan in plans.items()}
            self.check_exports(folder, titles, RPT_STEM, 13)

    @unittest.skipUnless(DLP.is_file(), "Science DLP draft is on its own branch")
    def test_all_science_dlp_exports(self):
        from staging.dlp.year6.render_science import DATA, RPT, RPT_NAME, export, load_plans, schedule_rows

        rpt, plans = load_plans()
        source = schedule_rows(Document(RPT))
        review = schedule_rows(rpt)
        self.assertEqual(len(plans), 61)
        self.assertEqual(Counter(plan["minutes"] for plan in plans), {30: 16, 60: 27, 90: 14, 120: 4})
        self.assertEqual(len({code for row in plans for code in re.findall(r"\d+\.\d+\.\d+", row["standards"])}), 96)
        corrections = json.loads(DATA.read_text(encoding="utf-8"))["schedule_corrections"]
        for plan, old, new in zip(plans, source, review, strict=True):
            with self.subTest(lesson=plan["id"]):
                self.assertEqual(old.cells[0].text, new.cells[0].text)
                self.assertEqual(old.cells[2].text, new.cells[2].text)
                self.assertEqual(old.cells[4].text.splitlines()[-1], new.cells[4].text.splitlines()[-1])
                if "title" in corrections.get(plan["id"], {}):
                    self.assertIn(plan["title"], new.cells[1].text)

        by_id = {plan["id"]: plan for plan in plans}
        self.assertIn("balloon circumference", by_id["L14"]["phases"][1][2])
        self.assertIn("Count both samples", by_id["L15"]["phases"][2][2])
        self.assertIn("captioned sketch", by_id["L16"]["phases"][2][2])
        self.assertIn("2.1 Human reproduction", by_id["R02"]["content_standards"])
        self.assertIn("2.2 Nervous system", by_id["R02"]["content_standards"])
        self.assertIn("2.2.3 State what the peripheral nervous system does.",
                      by_id["R02"]["learning_standards"])

        with TemporaryDirectory(prefix="science_dlp_year6_review_") as directory:
            folder = Path(directory)
            export(folder, rpt, plans)
            titles = {f"CikguLaju_RPH_Science_DLP_Y6_{plan['id']}": plan["title"] for plan in plans}
            for plan in plans:
                stem = f"CikguLaju_RPH_Science_DLP_Y6_{plan['id']}"
                word = Document(folder / f"{stem}.docx")
                fields = {row.cells[0].text: row.cells[1].text for row in word.tables[0].rows}
                self.assertEqual(fields["Content Standards"], plan["content_standards"])
                self.assertEqual(fields["Learning Standards"], plan["learning_standards"])
                pdf_text = " ".join(PdfReader(folder / f"{stem}.pdf").pages[0].extract_text().split())
                for entry in plan["learning_standards"].split(" · "):
                    self.assertIn(entry, pdf_text)
            self.check_exports(folder, titles, f"{RPT_NAME}_Teacher_Review", 7)
