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
            self.assertEqual({x["value"] for x in subjects if x["catalog_connected"]}, {SUBJECT, subject, "BAHASA_MELAYU_PPKI"})
            response = client.get(prefix + "/subject-catalog?year=2&subject=" + subject, headers=headers)
            self.assertEqual(response.status_code, 200)
            units = response.get_json()["units"]
            self.assertEqual([u["value"] for u in units], [str(n) for n in range(1, 13)])
            self.assertEqual([len(u["lessons"]) for u in units], [3, 4, 4, 5, 6, 5, 5, 6, 4, 5, 5, 5])
            self.assertEqual([x["value"] for x in units[0]["lessons"]], ["001", "002", "003"])
            teacher = {"class": "2 PPKI", "date": "2027-01-12", "time": "08:00 - 09:00", "students": "6", "reflection": ""}
            for unit, lesson in [(u["value"], x["value"]) for u in units for x in u["lessons"]] + [("1", "004"), ("12", "058")]:
                for fmt in ("word", "pdf"):
                    response = client.post(prefix + "/render", headers=headers, json={
                        "selection": {"year": 2, "subject": subject, "unit": unit, "lesson": lesson},
                        "format": fmt, "teacher": teacher})
                    if (unit, lesson) in (("1", "004"), ("12", "058")):
                        self.assertEqual(response.status_code, 404)
                    else:
                        self.assertEqual(response.status_code, 200)
                        if fmt == "word":
                            self.assertGreater(len(Document(BytesIO(response.data)).tables), 0)
                        else:
                            self.assertEqual(len(PdfReader(BytesIO(response.data)).pages), 1)
            self.assertFalse(client.get(prefix + "/subject-catalog?year=2&subject=MATEMATIK_PPKI", headers=headers).get_json()["available"])
            self.assertEqual(client.get(prefix + "/catalog?year=2", headers=headers).get_json(), options(2))


    def test_malay_31_source_locked_documents(self):
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
        subject = "BAHASA_MELAYU_PPKI"
        token = "T" * 32
        headers = {"Authorization": "Bearer " + token}
        teacher = {"class": "2 PPKI", "date": "2027-01-12", "time": "08:00 - 09:00", "students": "6", "reflection": ""}
        with patch.dict("os.environ", {"CIKGULAJU_AUTHORITATIVE_API_TOKEN": token,
                                       "CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1"}):
            result = client.get(prefix + "/subject-catalog?year=2&subject=" + subject, headers=headers)
            self.assertEqual(result.status_code, 200)
            units = result.get_json()["units"]
            self.assertEqual([u["value"] for u in units], [str(n) for n in range(1, 7)])
            self.assertEqual([len(u["lessons"]) for u in units], [5, 6, 4, 5, 5, 6])
            self.assertEqual([x["value"] for u in units for x in u["lessons"]], [f"{n:03d}" for n in range(1, 32)])
            for unit in units:
                for item in unit["lessons"]:
                    for fmt in ("word", "pdf"):
                        with self.subTest(unit=unit["value"], lesson=item["value"], fmt=fmt):
                            response = client.post(prefix + "/render", headers=headers, json={
                                "selection": {"year": 2, "subject": subject, "unit": unit["value"], "lesson": item["value"]},
                                "format": fmt, "teacher": teacher})
                            self.assertEqual(response.status_code, 200)
                            if fmt == "word":
                                doc = Document(BytesIO(response.data))
                                text = "\n".join(p.text for p in doc.paragraphs) + "\n".join(cell.text for t in doc.tables for row in t.rows for cell in row.cells)
                                self.assertIn("2 PPKI", text)
                                self.assertIn("Refleksi", text)
                            else:
                                pdf = PdfReader(BytesIO(response.data))
                                self.assertEqual(len(pdf.pages), 1)
                                self.assertIn("Refleksi", pdf.pages[0].extract_text())
            for unit, lesson in [("1", "006"), ("7", "032"), ("6", "032")]:
                response = client.post(prefix + "/render", headers=headers, json={
                    "selection": {"year": 2, "subject": subject, "unit": unit, "lesson": lesson},
                    "format": "pdf", "teacher": teacher})
                self.assertEqual(response.status_code, 404)
