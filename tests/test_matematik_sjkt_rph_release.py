"""Checks for the reviewed-vs-live Matematik SJKT RPH boundary."""

from datetime import date
from io import BytesIO
import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from docx import Document
from flask import Flask
import pymupdf

from web.matematik_sjkt_t2_release import RELEASE_FLAG
from web.matematik_sjkt_t2_telegram import _slots
from web.native_rph_telegram_api import create_native_rph_blueprint


class MatematikSjktRphRelease(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.register_blueprint(create_native_rph_blueprint(SimpleNamespace(
            create_word_file=lambda *_: self.fail("Unexpected SK renderer"),
            create_pdf_file=lambda *_: self.fail("Unexpected SK renderer"),
        )))
        self.client = app.test_client()
        self.base = "/internal/rph/v1/matematik-sjkt-t2"
        token = "test-sjkt-" + "x" * 40
        self.auth = {"Authorization": "Bearer " + token}
        env = patch.dict(os.environ, {
            RELEASE_FLAG: "1",
            "CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN": token,
        })
        env.start()
        self.addCleanup(env.stop)

    def test_catalogue_requires_release_and_lists_exactly_96_pdp(self):
        url = self.base + "/options"
        self.assertEqual(self.client.get(url + "?year=2").status_code, 401)
        with patch.dict(os.environ, {RELEASE_FLAG: "0"}):
            self.assertEqual(self.client.get(url + "?year=2", headers=self.auth).status_code, 404)
            review = self.client.get(self.base + "/review", headers=self.auth)
            self.assertEqual(review.status_code, 200)
        units = self.client.get(url + "?year=2", headers=self.auth).get_json()
        self.assertEqual([row["value"] for row in units], list(map(str, range(1, 9))))
        numbers = [
            lesson["lesson_no"]
            for unit in units
            for lesson in self.client.get(
                url, query_string={"year": 2, "unit": unit["value"]}, headers=self.auth
            ).get_json()
        ]
        self.assertEqual(numbers, list(range(1, 97)))
        self.assertEqual(self.client.get(url + "?year=2&unit=1&pdp=71", headers=self.auth).status_code, 404)

    def test_timetable_uses_school_calendar_and_profile_count(self):
        entry = {"class_name": "2 தமிழ்", "subject": "Matematik (SJKT)",
                 "start": "08:00", "end": "09:00"}
        runtime = SimpleNamespace(
            _teacher_profile=lambda _: {"state_name": "Kuala Lumpur"},
            _today_rows_v25272=lambda _: ("Isnin", [(0, entry)]),
            _profile_class_record=lambda *_: {"year_label": "Tahun 2", "students": 27},
        )
        self.assertEqual(_slots(runtime, 1, date(2027, 1, 11))[0]["students"], "27")
        self.assertEqual(_slots(runtime, 1, date(2027, 2, 1)), {})

    def test_render_uses_teacher_fields_and_public_footer(self):
        request = {"year": 2, "unit": 5, "pdp": 71, "teacher": {
            "class": "2 தமிழ்", "date": "2027-01-11", "time": "08:00 - 09:00",
            "students": "27", "reflection": "Selesai latihan.",
        }}
        for fmt in ("word", "pdf"):
            with self.subTest(fmt=fmt):
                response = self.client.post(self.base + "/render", headers=self.auth, json=request | {"format": fmt})
                self.assertEqual(response.status_code, 200)
                if fmt == "word":
                    document = Document(BytesIO(response.data))
                    text = "\n".join(p.text for p in document.paragraphs + document.sections[0].footer.paragraphs)
                else:
                    with pymupdf.open(stream=response.data, filetype="pdf") as document:
                        self.assertEqual(len(document), 1)
                        text = document[0].get_text(sort=True)
                for value in ("PdP 071", "5.3.1", "Bilangan murid 27", "Selesai latihan."):
                    self.assertIn(value, text)
                self.assertNotIn("Draf semakan", text)
