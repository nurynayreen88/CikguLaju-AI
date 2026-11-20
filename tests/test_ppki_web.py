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
        self.catalog_year3 = None
        self.catalog_year4 = None
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
        if path == "catalog?year=3":
            if self.catalog_year3 is None:
                raise ppki.NativeRPHUnavailable("Year 3 source is not deployed")
            return json.dumps(self.catalog_year3).encode()
        if path == "catalog?year=4":
            if self.catalog_year4 is None:
                raise ppki.NativeRPHUnavailable("Year 4 source is not deployed")
            return json.dumps(self.catalog_year4).encode()
        if path in ("rpt.pdf?year=4", "rpt.pdf", "rpt-current.pdf", "rpt-manipulatif.pdf", "rpt.pdf?year=3", "rpt-manipulatif.pdf?year=3"):
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
        self.assertEqual(self.client.get(opts, query_string={"year": 3, **queries[0][0]}).status_code, 503)
        self.assertEqual(self.client.get(opts, query_string={"year": 4, **queries[0][0]}).status_code, 503)
        self.assertEqual(self.client.get(opts, query_string={"year": 2, "kind": "pdp", "subject": ppki.SUBJECT,
                                                             "unit": "u01"}).status_code, 400)

    def test_year3_exact_pdp_rph_and_rpt_access(self):
        self.catalog_year3 = {
            **self.catalog, "year": 3,
            "units": [{"value": ppki.UNIT1, "label": "Unit 1 · Sekolah, Duniaku"}],
            "lessons": [{"value": f"{number:03d}", "label": f"PdP {number:03d}",
                         "formats": ["word", "pdf"], "textbook_ref": "Buku Teks hlm. 4–16"}
                        for number in range(1, 18)],
        }
        selection = {**self.selection, "year": 3, "unit": ppki.UNIT1, "lesson": "017"}
        choices = self.client.get("/api/options", query_string={
            "year": 3, "kind": "pdp", "subject": ppki.SUBJECT, "unit": ppki.UNIT1,
        })
        self.assertEqual([row["value"] for row in choices.json], [f"{number:03d}" for number in range(1, 18)])
        for fmt in ("word", "pdf"):
            response = self.client.get(f"/api/web/rph/{fmt}", query_string=selection)
            self.assertEqual(response.status_code, 200)
            self.assertIn("TAHUN_3_017", response.headers["Content-Disposition"])
            self.assertEqual(self.source_requests[-1][1]["selection"], selection)
        self.assertEqual(self.client.get("/api/web/rph/availability",
                         query_string={**selection, "year": 2}).status_code, 503)
        listing = self.client.get("/api/rpt/2027/catalog").json
        entry, = [row for row in listing["subjects"] if row["code"] == ppki.RPT_CODE]
        self.assertEqual([item["year"] for item in entry["years"]], [2, 3])
        self.assertIn("17 PdP Unit 1", entry["years"][1]["note"])
        url = f"/api/rpt/2027/all/{ppki.RPT_CODE}/3.pdf"
        rpt = self.client.get(url)
        self.assertEqual(rpt.status_code, 200)
        self.assertIn("TAHUN_3_UNIT_1", rpt.headers["Content-Disposition"])
        self.assertEqual(self.source_requests[-1][0], "rpt.pdf?year=3")
        materials = "/api/web/rph/extra-materials"
        self.assertEqual(self.client.get(materials, query_string=selection).json["items"], [])
        video = self.client.get(materials, query_string={**selection, "lesson": "003"}).json["items"][0]
        self.assertEqual((video["type"], video["action"]), ("video", "Muat Turun Video"))
        self.assertTrue(video["url"].startswith("https://drive.usercontent.google.com/download?"))
        self.paid = False
        self.assertEqual(self.client.get(url).status_code, 403)
        self.credits = 0
        blocked = self.client.get(materials, query_string={**selection, "lesson": "003"})
        self.assertEqual(blocked.status_code, 403)
        self.assertEqual(blocked.json["code"], "FREE_TRIAL_EXHAUSTED")

        self.paid = True
        self.catalog_year3["additional_units"] = [{
            "value": unit, "label": label,
            "lessons": [{"value": f"{number:03d}", "label": f"PdP {number:03d}",
                         "formats": ["word", "pdf"], "textbook_ref": "Buku Teks"}
                        for number in numbers],
        } for unit, label, numbers in (
            (ppki.UNIT, "Unit 2", range(18, 36)),
            (ppki.UNIT3, "Unit 3", range(36, 40)),
        )]
        selection = {**selection, "unit": ppki.UNIT3, "lesson": "039"}
        self.assertEqual(self.client.get("/api/web/rph/pdf", query_string=selection).status_code, 200)
        self.assertEqual(self.client.get(materials, query_string=selection).json["items"], [])
        self.assertEqual(self.client.get("/api/web/rph/availability",
            query_string={**selection, "unit": ppki.UNIT}).status_code, 503)
        listing = self.client.get("/api/rpt/2027/catalog").json
        entry, = [row for row in listing["subjects"] if row["code"] == ppki.RPT_CODE]
        self.assertIn("39 PdP Unit 1–3", entry["years"][1]["note"])
        self.assertIn("TAHUN_3_UNIT_1_2_3_2027.pdf", self.client.get(url).headers["Content-Disposition"])

        for unit, first, last in ((ppki.UNIT4, 40, 43), (ppki.UNIT5, 44, 49)):
            self.catalog_year3["additional_units"].append({
                "value": unit, "label": f"Unit {unit[1:3]}",
                "lessons": [{"value": f"{number:03d}", "label": f"PdP {number:03d}",
                             "formats": ["word", "pdf"], "textbook_ref": "Buku Teks"}
                            for number in range(first, last + 1)],
            })
            selection = {**selection, "unit": unit, "lesson": f"{last:03d}"}
            self.assertEqual(self.client.get("/api/web/rph/word", query_string=selection).status_code, 200)
            self.assertEqual(self.client.get(materials, query_string=selection).json["items"], [])
        listing = self.client.get("/api/rpt/2027/catalog").json
        entry, = [row for row in listing["subjects"] if row["code"] == ppki.RPT_CODE]
        self.assertIn("49 PdP Unit 1–5", entry["years"][1]["note"])
        self.assertIn("TAHUN_3_UNIT_1_2_3_4_5_2027.pdf", self.client.get(url).headers["Content-Disposition"])


    def test_year4_first_pengurusan_diri_unit(self):
        self.catalog_year4 = {
            **self.catalog, "year": 4,
            "units": [{"value": ppki.UNIT1, "label": "Unit 1 · Bertamu di Inap Desa"}],
            "lessons": [{"value": f"{number:03d}", "label": f"PdP {number:03d}",
                         "formats": ["word", "pdf"], "textbook_ref": "Buku Teks"}
                        for number in range(1, 10)],
        }
        selected = {"year": 4, "subject": ppki.SUBJECT, "unit": ppki.UNIT1, "lesson": "009"}
        opts = self.client.get("/api/options", query_string={
            "year": 4, "kind": "pdp", "subject": ppki.SUBJECT, "unit": ppki.UNIT1,
        })
        self.assertEqual([row["value"] for row in opts.json], [f"{n:03d}" for n in range(1, 10)])
        self.assertEqual(self.client.get("/api/web/rph/word", query_string=selected).status_code, 200)
        self.assertEqual(self.client.get("/api/web/rph/availability",
                         query_string={**selected, "lesson": "010"}).status_code, 503)
        rpt = self.client.get(f"/api/rpt/2027/all/{ppki.RPT_CODE}/4.pdf")
        self.assertEqual(rpt.status_code, 200)
        self.assertIn("TAHUN_4_UNIT_1", rpt.headers["Content-Disposition"])
        self.assertEqual(self.source_requests[-1][0], "rpt.pdf?year=4")
        self.assertEqual(self.client.get(f"/api/rpt/2027/all/{ppki.RPT_MANIPULATIVE_CODE}/4.pdf").status_code, 404)

    def test_year3_manipulative_rph_and_rpt(self):
        self.catalog_year3 = {
            **self.catalog, "year": 3,
            "units": [{"value": ppki.UNIT1, "label": "Unit 1 · Sekolah, Duniaku"}],
            "lessons": [{"value": f"{n:03d}", "label": f"PdP {n:03d}",
                         "formats": ["word", "pdf"], "textbook_ref": "Buku Teks"}
                        for n in range(1, 18)],
        }
        rpt = f"/api/rpt/2027/all/{ppki.RPT_MANIPULATIVE_CODE}/3.pdf"
        self.assertEqual(self.client.get(rpt).status_code, 404)
        self.catalog_year3["kemahiran_manipulatif"] = [{
            "value": unit, "label": unit,
            "lessons": [{"value": f"{n:03d}", "label": f"PdP {n:03d}",
                         "formats": ["word", "pdf"], "textbook_ref": "Buku Teks"}
                        for n in numbers],
        } for unit, numbers in ppki.YEAR3_MANIPULATIVE_UNIT_LESSONS.items()]
        selected = {"year": 3, "subject": ppki.SUBJECT, "unit": ppki.MANIPULATIVE_UNIT3, "lesson": "073"}
        self.assertEqual(self.client.get("/api/web/rph/word", query_string=selected).status_code, 200)
        self.assertEqual(self.client.get("/api/web/rph/availability",
                         query_string={**selected, "lesson": "064", "unit": ppki.UNIT1}).status_code, 503)
        data = self.client.get("/api/rpt/2027/catalog").json
        entry, = [row for row in data["subjects"] if row["code"] == ppki.RPT_MANIPULATIVE_CODE]
        self.assertEqual(entry["years"][0]["year"], 3)
        self.assertIn("24 PdP Unit 1–3", entry["years"][0]["note"])
        result = self.client.get(rpt)
        self.assertEqual(result.status_code, 200)
        self.assertIn("KEMAHIRAN_MANIPULATIF_TAHUN_3", result.headers["Content-Disposition"])
        self.assertEqual(self.source_requests[-1][0], "rpt-manipulatif.pdf?year=3")
        self.paid = False
        self.assertEqual(self.client.get(rpt).status_code, 403)

    def test_manipulative_component_selection_and_existing_rpt(self):
        opts = "/api/options"
        query = {"year": 2, "subject": ppki.SUBJECT}
        self.assertEqual(self.client.get(opts, query_string={**query, "kind": "components"}).json,
                         self.catalog["components"])
        self.catalog["kemahiran_manipulatif"] = [{
            "value": ppki.MANIPULATIVE_UNIT1, "label": "Unit 1 · Kami Aktif",
            "lessons": [{"value": f"{n:03d}", "label": f"PdP {n:03d}",
                         "formats": ["word", "pdf"], "textbook_ref": "Buku Teks hlm. 39"}
                        for n in range(40, 44)],
        }]
        self.assertEqual([row["value"] for row in self.client.get(
            opts, query_string={**query, "kind": "components"}).json],
            [ppki.COMPONENT, ppki.MANIPULATIVE_COMPONENT])
        self.assertEqual([row["value"] for row in self.client.get(
            opts, query_string={**query, "kind": "units", "component": ppki.MANIPULATIVE_COMPONENT}).json],
            [ppki.MANIPULATIVE_UNIT1])
        self.assertEqual([row["value"] for row in self.client.get(
            opts, query_string={**query, "kind": "pdp", "unit": ppki.MANIPULATIVE_UNIT1}).json],
            ["040", "041", "042", "043"])
        selected = {**query, "unit": ppki.MANIPULATIVE_UNIT1, "lesson": "040"}
        self.assertEqual(self.client.get("/api/web/rph/word", query_string=selected).status_code, 200)
        self.assertEqual(self.client.get("/api/web/rph/pdf", query_string=selected).status_code, 200)
        self.assertGreaterEqual(self.client.get("/api/web/rph/word", query_string={
            **selected, "unit": ppki.UNIT}).status_code, 400)
        entry, = [row for row in self.client.get("/api/rpt/2027/catalog").json["subjects"]
                  if row["code"] == ppki.RPT_CODE]
        self.assertIn("Pengurusan Diri · Agihan 14 PdP Unit 2", entry["years"][0]["note"])

    def test_complete_manipulative_catalog_and_paid_rpt(self):
        labels = ("Kami Aktif", "Jari Kreatif", "Lihat, Dengar dan Rasa")
        self.catalog["kemahiran_manipulatif"] = [
            {"value": unit_id, "label": label, "lessons": [
                {"value": f"{number:03d}", "label": f"PdP {number:03d}",
                 "formats": ["word", "pdf"], "textbook_ref": "Buku Teks"}
                for number in numbers]}
            for (unit_id, numbers), label in zip(ppki.MANIPULATIVE_UNIT_LESSONS.items(), labels, strict=True)
        ]
        query = {"year": 2, "subject": ppki.SUBJECT}
        units = self.client.get("/api/options", query_string={
            **query, "kind": "units", "component": ppki.MANIPULATIVE_COMPONENT,
        }).json
        self.assertEqual([row["value"] for row in units], list(ppki.MANIPULATIVE_UNIT_LESSONS))
        selected = {**query, "unit": ppki.MANIPULATIVE_UNIT3, "lesson": "071"}
        self.assertEqual(self.client.get("/api/web/rph/pdf", query_string=selected).status_code, 200)
        endpoint = f"/api/rpt/2027/all/{ppki.RPT_MANIPULATIVE_CODE}/2.pdf"
        self.paid = False
        self.assertEqual(self.client.get(endpoint).status_code, 403)
        self.paid = True
        entry, = [row for row in self.client.get("/api/rpt/2027/catalog").json["subjects"]
                  if row["code"] == ppki.RPT_MANIPULATIVE_CODE]
        self.assertIn("32 PdP Unit 1–3", entry["years"][0]["note"])
        self.assertEqual(self.client.get(endpoint).status_code, 200)
        self.assertEqual(self.source_requests[-1][0], "rpt-manipulatif.pdf")

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
