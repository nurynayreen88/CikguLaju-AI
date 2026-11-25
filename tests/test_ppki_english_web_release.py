"""Web PPKI English source contract and existing access gate, no network."""
import json
import unittest
from io import BytesIO
from unittest.mock import patch

from flask import Flask
from web import native_telegram_ppki_client as ppki
from web import unified_rph_web as rph


def source():
    return {"source": "ppki-subject-v1", "year": 2,
            "subject": ppki.ENGLISH_SUBJECT, "available": True,
            "units": [{"value": "1", "label": "Welcome Back", "lessons": [
                {"value": f"{n:03d}", "label": title, "textbook_ref": page,
                 "formats": ["word", "pdf"]}
                for n, title, page in [(1, "School song", "1"),
                                       (2, "School places", "2–3"),
                                       (3, "Reading directions", "4")]
            ]}]}


class TestPPKIEnglishWebRelease(unittest.TestCase):
    def test_catalog_scope_and_legacy_fallback(self):
        legacy = {"subjects": [{"value": ppki.SUBJECT, "label": "Pengurusan Kehidupan"}]}
        with patch.object(ppki, "catalog", return_value=legacy), patch.object(
                ppki, "_request", return_value=json.dumps(source()).encode()):
            self.assertEqual([x["value"] for x in ppki.get_options("subjects", 2)],
                             [ppki.ENGLISH_SUBJECT, ppki.SUBJECT])
            self.assertEqual(ppki.get_options("subjects", 3), legacy["subjects"])
            self.assertEqual(ppki.get_options("units", 2, ppki.ENGLISH_SUBJECT),
                             [{"value": "1", "label": "Welcome Back"}])
            for n in ("001", "002", "003"):
                self.assertEqual(ppki.validate_selection(2, ppki.ENGLISH_SUBJECT, "1", n)["value"], n)
            for year, unit, pdp in [(2, "1", "004"), (3, "1", "001"), (2, "2", "001")]:
                with self.assertRaises(ValueError):
                    ppki.validate_selection(year, ppki.ENGLISH_SUBJECT, unit, pdp)
        with patch.object(ppki, "catalog", return_value=legacy), patch.object(
                ppki, "_request", side_effect=ppki.NativeRPHUnavailable("unavailable")):
            self.assertEqual(ppki.get_options("subjects", 2), legacy["subjects"])

    def test_existing_download_gate(self):
        app = Flask(__name__)
        app.register_blueprint(rph.create_blueprint())
        client = app.test_client()
        query = {"year": "2", "subject": ppki.ENGLISH_SUBJECT,
                 "unit": "1", "lesson": "001", "teacher_students": "6"}
        account = {"telegram_user_id": 42, "free_remaining": 0}
        with patch.object(rph, "_account", return_value=(account, None)), patch.object(
                ppki, "_request", return_value=json.dumps(source()).encode()), patch.object(
                ppki, "request_rph", return_value=BytesIO(b"%PDF-test")) as render:
            with patch.object(rph, "_has_paid_access", return_value=False):
                available = client.get("/api/web/rph/availability", query_string=query)
                self.assertEqual(available.status_code, 200)
                self.assertFalse(available.get_json()["download_allowed"])
                self.assertEqual(client.get("/api/web/rph/pdf", query_string=query).status_code, 403)
                render.assert_not_called()
            with patch.object(rph, "_has_paid_access", return_value=True), patch(
                    "web.rph_reflection_universal.personalize_verified_document",
                    side_effect=lambda doc, *_: doc):
                available = client.get("/api/web/rph/availability", query_string=query)
                self.assertEqual(available.status_code, 200)
                self.assertTrue(available.get_json()["download_allowed"])
                self.assertEqual(client.get("/api/web/rph/pdf",
                    query_string={**query, "lesson": "004"}).status_code, 503)
                render.assert_not_called()
                response = client.get("/api/web/rph/pdf", query_string=query)
                self.assertEqual(response.status_code, 200)
                self.assertIn("BAHASA_INGGERIS_PPKI", response.headers["Content-Disposition"])
                self.assertEqual(response.headers["X-RPH-Access-Mode"], "paid")
                render.assert_called_once()
