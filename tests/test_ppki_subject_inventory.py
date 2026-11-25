import unittest

from staging.ppki.catalog import SUBJECT, YEARS, options
from staging.ppki.subject_inventory import subject_inventory


class TestPPKISubjectInventory(unittest.TestCase):
    def test_years_subjects_and_legacy_catalog(self):
        for year in YEARS:
            with self.subTest(year=year):
                rows = subject_inventory(year)
                keys = [r["value"] for r in rows]
                self.assertEqual(len(keys), 8 if year <= 3 else 12)
                self.assertEqual(len(keys), len(set(keys)))
                self.assertTrue(all(k.endswith("_PPKI") for k in keys))
                self.assertEqual([r["label"] for r in rows],
                                 sorted((r["label"] for r in rows), key=str.casefold))
                self.assertEqual([r["value"] for r in rows if r["catalog_connected"]], [SUBJECT])
                self.assertEqual([r["value"] for r in options(year)["subjects"]], [SUBJECT])
                self.assertEqual(sum(r["curriculum_group"] == "Asas 3M" for r in rows),
                                 3 if year <= 3 else 0)
                self.assertTrue(all(r["status"] == "pending_source_audit"
                                    for r in rows if r["value"] != SUBJECT))

    def test_invalid_year(self):
        for year in (1, 7, "2", None, True):
            with self.subTest(year=year), self.assertRaises(ValueError):
                subject_inventory(year)


class TestPPKISubjectReleaseAPI(unittest.TestCase):
    def test_only_reviewed_unit_is_downloadable(self):
        from flask import Flask
        from unittest.mock import patch
        from io import BytesIO
        from docx import Document
        from pypdf import PdfReader
        from web.telegram_ppki_api import create_ppki_blueprint
        app = Flask(__name__)
        app.register_blueprint(create_ppki_blueprint())
        client = app.test_client()
        prefix = "/internal/rph/v1/ppki"
        subject = "BAHASA_INGGERIS_PPKI"
        token = "T" * 32
        headers = {"Authorization": "Bearer " + token}
        with patch.dict("os.environ", {"CIKGULAJU_AUTHORITATIVE_API_TOKEN": token,
                                       "CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1"}):
            self.assertEqual(client.get(prefix + "/subject-catalog?year=2&subject=" + subject).status_code, 401)
            subjects = client.get(prefix + "/subjects?year=2", headers=headers).get_json()["subjects"]
            self.assertEqual({x["value"] for x in subjects if x["catalog_connected"]}, {SUBJECT, subject})
            response = client.get(prefix + "/subject-catalog?year=2&subject=" + subject, headers=headers)
            self.assertEqual(response.status_code, 200)
            units = response.get_json()["units"]
            self.assertEqual([u["value"] for u in units], ["1"])
            self.assertEqual([x["value"] for x in units[0]["lessons"]], ["001", "002", "003"])
            teacher = {"class": "2 PPKI", "date": "2027-01-12", "time": "08:00 - 09:00", "students": "6", "reflection": ""}
            for lesson in ("001", "002", "003", "004"):
                for fmt in ("word", "pdf"):
                    response = client.post(prefix + "/render", headers=headers, json={
                        "selection": {"year": 2, "subject": subject, "unit": "1", "lesson": lesson},
                        "format": fmt, "teacher": teacher})
                    if lesson == "004":
                        self.assertEqual(response.status_code, 404)
                    else:
                        self.assertEqual(response.status_code, 200)
                        if fmt == "word":
                            self.assertGreater(len(Document(BytesIO(response.data)).tables), 0)
                        else:
                            self.assertEqual(len(PdfReader(BytesIO(response.data)).pages), 1)
            self.assertFalse(client.get(prefix + "/subject-catalog?year=2&subject=MATEMATIK_PPKI", headers=headers).get_json()["available"])
            self.assertEqual(client.get(prefix + "/catalog?year=2", headers=headers).get_json(), options(2))
