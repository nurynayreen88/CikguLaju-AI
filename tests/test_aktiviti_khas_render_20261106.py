"""QA for source-first 50 RPH Aktiviti Khas (draft, never deployed)."""
import io
import os
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from flask import Flask
from pypdf import PdfReader

from rph_standalone.aktiviti_khas.engine import (
    SELEPAS, TRANSISI, SourceUnavailable, _catalog, fields_for, list_options,
    render, select,
)
from web.telegram_special_activity_api import create_special_rph_blueprint


META = {"class": "6 Anggerik", "date": "2026-11-06",
        "time": "09:30-10:30", "students": "30"}
TOKEN = "Z" * 40


class TestSpecialActivityRender(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source, cls.digest = _catalog()
        cls.rows = cls.source["activities"]

    def test_complete_inventory_and_tiers(self):
        self.assertEqual(len(self.rows), 50)
        self.assertEqual(len({r["id"] for r in self.rows}), 50)
        self.assertEqual(len(list_options(TRANSISI, 1)[0]), 20)
        for year in (1, 2, 3, 4, 5, 6):
            self.assertEqual(len(list_options(SELEPAS, year)[0]), 10)
        self.assertEqual(len(list_options(TRANSISI, 1,
            phase="Fasa Penyesuaian")[0]), 10)
        self.assertEqual(len(list_options(TRANSISI, 1,
            phase="Fasa Kesediaan")[0]), 10)
        for year in (2, 3, 4, 5, 6):
            with self.assertRaises(ValueError):
                list_options(TRANSISI, year)

    def test_all_50_pdf_files_one_page_a4(self):
        for row in self.rows:
            with self.subTest(activity=row["id"]):
                year = row["years"][0]
                selected = select(row["category"], year, row["id"], self.digest)
                pdf = render(selected, year, META, "pdf")
                reader = PdfReader(io.BytesIO(pdf))
                self.assertEqual(len(reader.pages), 1)
                self.assertTrue(abs(float(reader.pages[0].mediabox.width)-595.28) < 1)
                self.assertTrue(abs(float(reader.pages[0].mediabox.height)-841.89) < 1)
                txt = reader.pages[0].extract_text()
                self.assertIn(row["title"], txt)
                self.assertIn("Aktiviti 1", txt)
                self.assertIn("Aktiviti 2", txt)
                self.assertIn("Aktiviti 3", txt)
                self.assertIn("06/11/2026", txt)

    def test_word_structured_separate_activity_rows(self):
        for ident, year, kind in (("K01", 1, TRANSISI),
                                  ("S03A", 2, SELEPAS),
                                  ("S03B", 4, SELEPAS),
                                  ("S03C", 6, SELEPAS)):
            with self.subTest(ident=ident):
                row = select(kind, year, ident, self.digest)
                content = render(row, year, META, "word")
                with ZipFile(io.BytesIO(content)) as z:
                    self.assertIsNone(z.testzip())
                    xml = z.read("word/document.xml").decode("utf-8")
                    self.assertIn(row["title"], xml)
                    for n in (1, 2, 3):
                        self.assertIn("Aktiviti %d" % n, xml)
                    self.assertIn("06/11/2026", xml)
                    self.assertIn("DRAF", xml)

    def test_wrong_tier_or_digest_is_rejected(self):
        with self.assertRaises(SourceUnavailable):
            select(SELEPAS, 2, "S03C", self.digest)
        with self.assertRaises(SourceUnavailable):
            select(SELEPAS, 6, "S03C", "0" * 64)
        with self.assertRaises(ValueError):
            list_options(TRANSISI, 2)
        row = select(TRANSISI, 1, "K01", self.digest)
        with self.assertRaises(ValueError):
            fields_for(row, 1, META, subject="Bahasa Melayu")

    def test_no_db_or_curriculum_fabrication(self):
        for row in self.rows:
            for key in ("sk", "sp", "textbook_page", "lesson_number"):
                self.assertNotIn(key, row)
        self.assertEqual(self.source["release_status"], "DRAFT_REVIEW")


class TestProtectedApi(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(create_special_rph_blueprint())
        self.client = self.app.test_client()
        self.headers = {"Authorization": "Bearer " + TOKEN}
        self.env = patch.dict(os.environ, {
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN": TOKEN,
            "CIKGULAJU_SPECIAL_RPH_ENABLED": "1",
            "CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1"
        })
        self.env.start()

    def tearDown(self):
        self.env.stop()

    def test_no_public_access(self):
        r = self.client.get("/internal/rph/v1/aktiviti-khas/options?kind=%s&year=1" % TRANSISI)
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.headers["Cache-Control"], "private, no-store")

    def test_options_and_protected_word_render(self):
        r = self.client.get(
            "/internal/rph/v1/aktiviti-khas/options?kind=%s&year=6" % SELEPAS,
            headers=self.headers)
        self.assertEqual(r.status_code, 200)
        options = r.get_json()
        self.assertEqual(len(options["items"]), 10)
        self.assertEqual(options["status"], "DRAFT_REVIEW")
        req = {"selection": {"kind": SELEPAS, "year": 6,
                             "activity_id": "S03C", "subject": "Matematik"},
               "teacher": META, "format": "word",
               "source_digest": options["source_digest"]}
        doc = self.client.post("/internal/rph/v1/aktiviti-khas/render",
                               json=req, headers=self.headers)
        self.assertEqual(doc.status_code, 200)
        self.assertTrue(doc.data.startswith(b"PK"))
        self.assertIn("DRAF", doc.headers["Content-Disposition"])
        req["source_digest"] = "f" * 64
        bad = self.client.post("/internal/rph/v1/aktiviti-khas/render",
                               json=req, headers=self.headers)
        self.assertNotEqual(bad.status_code, 200)

    def test_must_not_accept_client_supplied_rph(self):
        digest = _catalog()[1]
        body = {"selection": {"kind": TRANSISI, "year": 1,
                              "activity_id": "K01", "subject": None},
                "teacher": META, "format": "pdf", "source_digest": digest,
                "rph_text": "Arbitrary AI-generated text"}
        r = self.client.post("/internal/rph/v1/aktiviti-khas/render",
                             json=body, headers=self.headers)
        self.assertEqual(r.status_code, 400)


if __name__ == "__main__":
    unittest.main()
