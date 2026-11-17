"""The 2027 RPT row must reach the same RPH through the native sequence API."""

from io import BytesIO
import json
import os
import unittest
from unittest.mock import patch

from docx import Document
from flask import Flask
from pypdf import PdfReader

from staging.sains.tahun5.eksport_2027 import SOURCE
from staging.sains.tahun5.semakan_penjana import ReviewRuntime
from web.telegram_verified_sequence_rph_bridge import create_native_sequence_rph_blueprint

ROUTE = "/internal/rph/v1/sequence"
TOKEN = "sains-sk-tahun5-review-only-token-for-flask"


class ReviewSequenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = ReviewRuntime()
        cls.source = json.loads(SOURCE.read_text(encoding="utf-8"))["pdp"]
        app = Flask(__name__)
        app.register_blueprint(create_native_sequence_rph_blueprint(cls.runtime))
        cls.client = app.test_client()
        cls.headers = {"Authorization": f"Bearer {TOKEN}"}

    def setUp(self):
        env = patch.dict(os.environ, {
            "CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN": TOKEN,
        })
        env.start()
        self.addCleanup(env.stop)

    def test_every_rpt_choice_resolves_and_renders_its_lesson(self):
        params = {"year": 5, "subject": "SCIENCE"}
        units = self.client.get(f"{ROUTE}/units", query_string=params, headers=self.headers)
        self.assertEqual(units.status_code, 200)
        self.assertEqual([item["label"] for item in units.json["items"]],
                         list(dict.fromkeys(row["unit"] for row in self.source)))
        delivered = []
        for unit in units.json["items"]:
            params["unit"] = unit["value"]
            lessons = self.client.get(f"{ROUTE}/lessons", query_string=params, headers=self.headers)
            self.assertEqual(lessons.status_code, 200)
            expected = [row for row in self.source if row["unit"] == unit["label"]]
            self.assertEqual(len(lessons.json["items"]), len(expected))
            for row, lesson in zip(expected, lessons.json["items"], strict=True):
                with self.subTest(number=row["id"]):
                    self.assertEqual(lesson, {
                        "value": f"SK27-SCI-Y5-PDP-{row['id']:03d}",
                        "label": f"PdP {row['id']:03d} • {row['title']}",
                        "textbook_ref": f"Buku Teks m/s {row['pages']}",
                    })
                    selection = {**params, "lesson": lesson["value"]}
                    check = self.client.get(f"{ROUTE}/availability", query_string=selection,
                                            headers=self.headers)
                    self.assertEqual(check.status_code, 200)
                    self.assertTrue(check.json["available"])
                    self.check_documents(selection, row)
                    delivered.append(row["id"])
        self.assertEqual(delivered, list(range(1, 117)))

    def check_documents(self, selection, row):
        sk = row["sp"].rsplit(".", 1)[0]
        plan = self.runtime.plans[selection["lesson"]]
        time = "08:00 - 08:30" if row["minutes"] == 30 else "08:00 - 09:00"
        for fmt in ("word", "pdf"):
            with self.subTest(format=fmt):
                response = self.client.post(f"{ROUTE}/render", headers=self.headers, json={
                    "selection": selection, "format": fmt,
                    "teacher": {"class": "5 Bestari", "date": "2027-01-18",
                                "time": time,
                                "students": "32", "reflection": "Murid membentangkan dapatan."},
                })
                self.assertEqual(response.status_code, 200)
                stream = BytesIO(response.data)
                if fmt == "word":
                    document = Document(stream)
                    section = document.sections[0]
                    self.assertAlmostEqual(section.page_width.mm, 210, places=1)
                    self.assertAlmostEqual(section.page_height.mm, 297, places=1)
                    text = "\n".join([p.text for p in document.paragraphs] + [
                        cell.text for table in document.tables
                        for line in table.rows for cell in line.cells
                    ])
                else:
                    pdf = PdfReader(stream)
                    self.assertEqual(len(pdf.pages), 1)
                    page = pdf.pages[0]
                    self.assertAlmostEqual(float(page.mediabox.width), 595.28, places=1)
                    self.assertAlmostEqual(float(page.mediabox.height), 841.89, places=1)
                    text = page.extract_text()
                compact = " ".join(text.split())
                for expected in (row["title"], row["unit"], f"PdP {row['id']:03d} · {row['minutes']} minit",
                                 f"SK {sk} · SP {row['sp']}", f"m/s {row['pages']}", plan["pbd"],
                                 plan["dates"], "5 Bestari", "18/01/2027", time, "Bil. murid: 32",
                                 "Murid membentangkan dapatan."):
                    self.assertIn(" ".join(expected.split()), compact)

    def test_wrong_unit_legacy_ids_and_unauthorized_requests_fail(self):
        params = {"year": 5, "subject": "SCIENCE"}
        self.assertEqual(self.client.get(f"{ROUTE}/units", query_string=params).status_code, 401)
        units = self.client.get(f"{ROUTE}/units", query_string=params, headers=self.headers).json
        opening = units["items"][0]["value"]
        rusting = units["items"][6]["value"]
        for unit, lesson in ((opening, "SK27-SCI-Y5-PDP-084"),
                             (opening, "ST5-PDP-084"), (rusting, "SCI-Y5-PDP-084"),
                             (rusting, "SK27-SCI-Y5-PDP-117")):
            with self.subTest(unit=unit, lesson=lesson):
                selection = {**params, "unit": unit, "lesson": lesson}
                result = self.client.get(f"{ROUTE}/availability", query_string=selection,
                                         headers=self.headers)
                self.assertEqual(result.status_code, 404)
                self.assertEqual(result.json, {"available": False})
                render = self.client.post(f"{ROUTE}/render", headers=self.headers, json={
                    "selection": selection, "format": "pdf",
                    "teacher": {"class": "", "date": "", "time": "", "students": ""},
                })
                self.assertEqual(render.status_code, 404)


if __name__ == "__main__":
    unittest.main()
