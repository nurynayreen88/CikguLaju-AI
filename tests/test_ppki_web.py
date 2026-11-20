"""PPKI-only Web catalog, authenticated downloads and shared trial access."""
from hashlib import sha256
from io import BytesIO
import json
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from tools.run_web_v1_preview import app
from web import native_telegram_ppki_client as ppki


class PpkiWebTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.source_requests = []
        self.paid = True
        self.credits = 1
        self.selection = {"year": 2, "subject": ppki.SUBJECT, "unit": ppki.UNIT, "lesson": "014"}
        self.catalog = {
            "source": ppki.SOURCE, "year": 2,
            "subjects": [{"value": ppki.SUBJECT, "label": "Pengurusan Kehidupan"}],
            "components": [{"value": ppki.COMPONENT, "label": "Pengurusan Diri"}],
            "units": [{"value": ppki.UNIT, "label": "Unit 2 · Diri Bersih Badan Sihat"}],
            "lessons": [{"value": f"{n:03d}", "label": f"PdP {n:03d}", "formats": ["word", "pdf"],
                         "textbook_ref": "Buku Teks hlm. 21"} for n in range(1, 15)],
        }
        self.pdf = b"%PDF-1.4\n" + b"%" * 9000
        self.docx = BytesIO()
        with ZipFile(self.docx, "w") as doc:
            doc.writestr("word/document.xml", "<w:document/>")
        auth_config = {"CIKGULAJU_WEB_SESSION_SECRET": "x" * 40}
        for substitute in (
            patch("web_v1_telegram_auth_routes._config", return_value=auth_config),
            patch("web_v1_sessions.verify_session_ticket", return_value=42),
            patch("web_v1_telegram_auth_routes._lookup", side_effect=self._account_lookup),
            patch("web.unified_rph_web._account", side_effect=lambda: (self._account_lookup(), None)),
            patch("web.rpt_2027_all_http._account", side_effect=lambda: (self._account_lookup(), None)),
            patch("web.unified_rph_web._has_paid_access", side_effect=lambda _: self.paid),
            patch("web.rpt_2027_all_http._has_paid_access", side_effect=lambda _: self.paid),
            patch.object(ppki, "_request", side_effect=self._request),
        ):
            substitute.start()
            self.addCleanup(substitute.stop)

    def _account_lookup(self, *_):
        return {"telegram_user_id": 42, "free_remaining": self.credits}

    def _request(self, path, mime, limit, payload=None):
        self.source_requests.append((path, payload))
        if path == "catalog":
            return json.dumps(self.catalog).encode()
        if path in ("rpt.pdf", "rpt-current.pdf"):
            return self.pdf
        return self.docx.getvalue() if payload["format"] == "word" else self.pdf

    def test_separate_menu_path(self):
        opts = "/api/options"
        queries = [
            ({"kind": "subjects", "curriculum": "ppki"}, ppki.SUBJECT),
            ({"kind": "components", "subject": ppki.SUBJECT}, ppki.COMPONENT),
            ({"kind": "units", "subject": ppki.SUBJECT, "component": ppki.COMPONENT}, ppki.UNIT),
            ({"kind": "pdp", "subject": ppki.SUBJECT, "unit": ppki.UNIT}, "001"),
        ]
        for query, token in queries:
            response = self.client.get(opts, query_string={"year": 2, **query})
            self.assertEqual(response.status_code, 200, response.get_json())
            self.assertEqual(response.get_json()[0]["value"], token)
        self.assertEqual(len(response.get_json()), 14)
        self.assertEqual(self.client.get(opts, query_string={"year": 3, **queries[0][0]}).status_code, 400)
        self.assertEqual(self.client.get(opts, query_string={"year": 2, "kind": "pdp", "subject": ppki.SUBJECT,
                                                             "unit": "u01"}).status_code, 400)

    def test_rph_word_pdf_and_trial_gate(self):
        prefix = "/api/web/rph/"
        available = self.client.get(prefix + "availability", query_string=self.selection)
        self.assertEqual(available.status_code, 200)
        self.assertEqual(available.json["formats"], ["word", "pdf"])
        for fmt in ("word", "pdf"):
            response = self.client.post(prefix + fmt, query_string=self.selection,
                                        json={"reflection": "Pemulihan esok."})
            self.assertEqual(response.status_code, 200, response.get_json(silent=True))
            render_request = self.source_requests[-1][1]
            self.assertEqual(render_request["selection"], self.selection)
            self.assertEqual(render_request["teacher"]["reflection"], "Pemulihan esok.")
            self.assertEqual(response.headers["X-RPH-Generator"], "telegram-native")
        self.paid, self.credits = False, 0
        before = len(self.source_requests)
        self.assertEqual(self.client.get(prefix + "word", query_string=self.selection).status_code, 403)
        self.assertEqual(len(self.source_requests), before)

    def test_rpt_list_paid_access_and_digest(self):
        path = f"/api/rpt/2027/all/{ppki.RPT_CODE}/2.pdf"
        self.paid = False
        self.assertEqual(self.client.get(path).status_code, 403)
        for paid in (False, True):
            self.paid = paid
            response = self.client.get("/api/rpt/2027/catalog")
            entry, = [s for s in response.json["subjects"] if s["code"] == ppki.RPT_CODE]
            self.assertEqual(entry["years"][0]["download_enabled"], paid)
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, self.pdf)
        self.assertEqual(response.headers["X-RPT-Source-SHA256"], sha256(self.pdf).hexdigest())
        self.assertEqual(response.headers["X-RPT-Personalization-Allowed"], "0")

    def test_unit_three_is_scoped_independently_and_rpt_expands(self):
        self.catalog["additional_units"] = [{
            "value": ppki.UNIT3, "label": "Unit 3 · Bersih Cermin Peribadi",
            "lessons": [{"value": f"{n:03d}", "label": f"PdP {n:03d}", "formats": ["word", "pdf"],
                         "textbook_ref": "Buku Teks hlm. 24–25"} for n in range(15, 19)],
        }]
        units = self.client.get("/api/options", query_string={"year": 2, "kind": "units",
                                "subject": ppki.SUBJECT, "component": ppki.COMPONENT})
        self.assertEqual([item["value"] for item in units.json], [ppki.UNIT, ppki.UNIT3])
        for unit, numbers in ((ppki.UNIT, range(1, 15)), (ppki.UNIT3, range(15, 19))):
            choices = self.client.get("/api/options", query_string={"year": 2, "kind": "pdp",
                                      "subject": ppki.SUBJECT, "unit": unit})
            self.assertEqual([int(item["value"]) for item in choices.json], list(numbers))
        selection = {**self.selection, "unit": ppki.UNIT3, "lesson": "018"}
        self.assertEqual(self.client.get("/api/web/rph/pdf", query_string=selection).status_code, 200)
        wrong_unit = dict(selection, unit=ppki.UNIT)
        self.assertEqual(self.client.get("/api/web/rph/pdf", query_string=wrong_unit).status_code, 503)
        pdf = self.client.get(f"/api/rpt/2027/all/{ppki.RPT_CODE}/2.pdf")
        self.assertEqual(pdf.status_code, 200)
        self.assertIn("UNIT_2_3_2027.pdf", pdf.headers["Content-Disposition"])
        self.assertEqual(self.source_requests[-1][0], "rpt-current.pdf")

    def test_unit_four_and_combined_rpt(self):
        self.catalog["additional_units"] = [
            {"value": unit, "label": label,
             "lessons": [{"value": f"{n:03d}", "label": f"PdP {n:03d}", "formats": ["word", "pdf"],
                          "textbook_ref": "Buku Teks"} for n in ppki.UNIT_LESSONS[unit]]}
            for unit, label in ((ppki.UNIT3, "Unit 3"), (ppki.UNIT4, "Unit 4 · Rumah Rubina"))
        ]
        opts = self.client.get("/api/options", query_string={"kind": "pdp", "year": 2,
                               "subject": ppki.SUBJECT, "unit": ppki.UNIT4})
        self.assertEqual([row["value"] for row in opts.json], ["019", "020", "021", "022", "023"])
        selection = {**self.selection, "unit": ppki.UNIT4, "lesson": "023"}
        for fmt in ("word", "pdf"):
            self.assertEqual(self.client.get(f"/api/web/rph/{fmt}", query_string=selection).status_code, 200)
        response = self.client.get("/api/rpt/2027/catalog")
        entry, = [s for s in response.json["subjects"] if s["code"] == ppki.RPT_CODE]
        self.assertIn("23 PdP Unit 2–4", entry["years"][0]["note"])
        rpt = self.client.get(f"/api/rpt/2027/all/{ppki.RPT_CODE}/2.pdf")
        self.assertEqual(rpt.status_code, 200)
        self.assertIn("UNIT_2_3_4_2027.pdf", rpt.headers["Content-Disposition"])
        self.catalog["additional_units"].reverse()
        with self.assertRaises(ppki.NativeRPHUnavailable):
            ppki.catalog()

    def test_unit_five_and_combined_rpt(self):
        self.catalog["additional_units"] = [
            {"value": unit, "label": label,
             "lessons": [{"value": f"{n:03d}", "label": f"PdP {n:03d}", "formats": ["word", "pdf"],
                          "textbook_ref": "Buku Teks"} for n in ppki.UNIT_LESSONS[unit]]}
            for unit, label in ((ppki.UNIT3, "Unit 3"), (ppki.UNIT4, "Unit 4 · Rumah Rubina"),
                                (ppki.UNIT5, "Unit 5 · Budi Pekerti Mulia"))
        ]
        opts = self.client.get("/api/options", query_string={"kind": "pdp", "year": 2,
                               "subject": ppki.SUBJECT, "unit": ppki.UNIT5})
        self.assertEqual([row["value"] for row in opts.json], ["024", "025", "026", "027", "028", "029"])
        selection = {**self.selection, "unit": ppki.UNIT5, "lesson": "029"}
        for fmt in ("word", "pdf"):
            self.assertEqual(self.client.get(f"/api/web/rph/{fmt}", query_string=selection).status_code, 200)
        response = self.client.get("/api/rpt/2027/catalog")
        entry, = [s for s in response.json["subjects"] if s["code"] == ppki.RPT_CODE]
        self.assertIn("29 PdP Unit 2–5", entry["years"][0]["note"])
        rpt = self.client.get(f"/api/rpt/2027/all/{ppki.RPT_CODE}/2.pdf")
        self.assertEqual(rpt.status_code, 200)
        self.assertIn("UNIT_2_3_4_5_2027.pdf", rpt.headers["Content-Disposition"])
        unit_five = self.catalog["additional_units"][-1]
        complete = unit_five["lessons"]
        unit_five["lessons"] = complete[:4]
        self.assertEqual(len(ppki.catalog()["lessons_by_unit"][ppki.UNIT5]), 4)
        unit_five["lessons"] = complete[:5]
        with self.assertRaises(ppki.NativeRPHUnavailable):
            ppki.catalog()
        unit_five["lessons"] = complete
        self.catalog["additional_units"].reverse()
        with self.assertRaises(ppki.NativeRPHUnavailable):
            ppki.catalog()

    def test_unit_one_display_order_and_complete_rpt(self):
        self.catalog["additional_units"] = [
            {"value": unit, "label": label,
             "lessons": [{"value": f"{n:03d}", "label": f"PdP {n:03d}", "formats": ["word", "pdf"],
                          "textbook_ref": "Buku Teks"} for n in ppki.UNIT_LESSONS[unit]]}
            for unit, label in ((ppki.UNIT3, "Unit 3"), (ppki.UNIT4, "Unit 4"), (ppki.UNIT5, "Unit 5"),
                                (ppki.UNIT1, "Unit 1 · Mari Belajar"))
        ]
        units = self.client.get("/api/options", query_string={
            "kind": "units", "year": 2, "subject": ppki.SUBJECT, "component": ppki.COMPONENT,
        })
        self.assertEqual([row["value"] for row in units.json],
                         [ppki.UNIT1, ppki.UNIT, ppki.UNIT3, ppki.UNIT4, ppki.UNIT5])
        choices = self.client.get("/api/options", query_string={
            "kind": "pdp", "year": 2, "subject": ppki.SUBJECT, "unit": ppki.UNIT1,
        })
        self.assertEqual([row["value"] for row in choices.json], [f"{n:03d}" for n in range(30, 40)])
        selection = {**self.selection, "unit": ppki.UNIT1, "lesson": "039"}
        self.assertEqual(self.client.get("/api/web/rph/word", query_string=selection).status_code, 200)
        response = self.client.get("/api/rpt/2027/catalog")
        entry, = [row for row in response.json["subjects"] if row["code"] == ppki.RPT_CODE]
        self.assertIn("39 PdP Unit 1–5", entry["years"][0]["note"])
        rpt = self.client.get(f"/api/rpt/2027/all/{ppki.RPT_CODE}/2.pdf")
        self.assertEqual(rpt.status_code, 200)
        self.assertIn("UNIT_1_2_3_4_5_2027.pdf", rpt.headers["Content-Disposition"])

    def test_missing_catalog_hides_rpt_and_blocks_fake_pdp(self):
        self.catalog["lessons"].pop()
        selection = self.client.get("/api/web/rph/availability", query_string=self.selection)
        self.assertEqual(selection.status_code, 503)
        response = self.client.get("/api/rpt/2027/catalog")
        self.assertNotIn(ppki.RPT_CODE, [s["code"] for s in response.json["subjects"]])
