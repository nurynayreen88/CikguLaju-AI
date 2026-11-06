"""Sejarah 2027 Web/Telegram source API remains private and source-bound."""
import os
import unittest
from unittest.mock import patch

from flask import Flask
from web.sejarah_2027_native_api import create_sejarah_2027_native_blueprint
from web.sejarah_2027_user_runtime import adapt_rows


class FakeRuntime:
    SEJARAH_2027_USER_BRIDGE_ACTIVE = True

    def __init__(self):
        self.word_calls = 0
        self.pdf_calls = 0

    def _rph_rows(self, state, text):
        return adapt_rows(state, {})

    def create_word_file(self, state, text, unique):
        self.word_calls += 1
        raise RuntimeError("No live files from tests")

    def create_pdf_file(self, state, text, unique):
        self.pdf_calls += 1
        raise RuntimeError("No live files from tests")


class SejarahNativeApiTest(unittest.TestCase):
    def setUp(self):
        self.runtime = FakeRuntime()
        app = Flask(__name__)
        app.register_blueprint(create_sejarah_2027_native_blueprint(self.runtime))
        self.client = app.test_client()
        self.env = patch.dict(os.environ, {
            "CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN": "X" * 48,
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        self.headers = {"Authorization": "Bearer " + "X"*48}

    def test_authentication(self):
        self.assertEqual(self.client.get("/internal/rph/v1/sejarah/units?year=4").status_code, 401)
        self.assertEqual(self.client.get("/internal/rph/v1/sejarah/units?year=4",
            headers={"Authorization": "Bearer wrong"}).status_code, 401)
        self.assertEqual(self.runtime.word_calls, 0)

    def test_catalog_year_unit_pdp_parity(self):
        for year in (4, 5, 6):
            result = self.client.get(f"/internal/rph/v1/sejarah/units?year={year}",headers=self.headers)
            self.assertEqual(result.status_code, 200)
            units = result.json["items"]
            self.assertGreater(len(units), 0)
            seen = []
            for unit in units:
                result = self.client.get(f"/internal/rph/v1/sejarah/lessons?year={year}&unit={unit['value']}",
                                         headers=self.headers)
                self.assertEqual(result.status_code, 200)
                for item in result.json["items"]:
                    self.assertIn("textbook_ref", item)
                    seen.append(item["value"])
                    availability = self.client.get(
                        f"/internal/rph/v1/sejarah/availability?year={year}&unit={unit['value']}&lesson={item['value']}",
                        headers=self.headers)
                    self.assertEqual(availability.status_code, 200)
                    self.assertTrue(availability.json["available"])
            self.assertEqual(sorted(seen), [f"{n:03d}" for n in range(1,37)])

    def test_stale_and_invalid_selections_do_not_render(self):
        for url in (
            "/internal/rph/v1/sejarah/availability?year=5&unit=u01&lesson=007",
            "/internal/rph/v1/sejarah/availability?year=5&unit=u02&lesson=007&extra=1",
            "/internal/rph/v1/sejarah/availability?year=3&unit=u01&lesson=001",
            "/internal/rph/v1/sejarah/availability?year=6&unit=u00&lesson=001",
        ):
            self.assertNotEqual(self.client.get(url,headers=self.headers).status_code, 200)
        self.assertEqual(self.runtime.word_calls, 0)

    def test_correct_selection_reaches_only_existing_renderer(self):
        payload = {"selection":{"year":5,"unit":"u02","lesson":"007"},
                   "teacher":{"class":"5 Bestari","date":"2027-03-22",
                              "time":"08:00-09:00","students":"30"},
                   "format":"pdf"}
        result = self.client.post("/internal/rph/v1/sejarah/render",json=payload,headers=self.headers)
        self.assertEqual(result.status_code, 503)  # deliberately no fake PDF
        self.assertEqual(self.runtime.pdf_calls, 1)
        self.assertEqual(self.runtime.word_calls, 0)
        self.assertEqual(result.headers["Cache-Control"],"no-store, private")
        payload["selection"]["unit"] = "u01"
        result = self.client.post("/internal/rph/v1/sejarah/render",json=payload,headers=self.headers)
        self.assertEqual(result.status_code, 404)
        self.assertEqual(self.runtime.pdf_calls, 1)

    def test_source_bridge_disabled_refuses_catalog_and_renderer(self):
        self.runtime.SEJARAH_2027_USER_BRIDGE_ACTIVE = False
        result=self.client.get("/internal/rph/v1/sejarah/units?year=4",headers=self.headers)
        self.assertEqual(result.status_code, 503)
        self.assertEqual(self.runtime.pdf_calls,0)


if __name__ == "__main__":
    unittest.main()
