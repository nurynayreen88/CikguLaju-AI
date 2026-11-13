"""Source-specific Web RPH preview tests with no production imports or mutations."""
from io import BytesIO
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from flask import Flask, jsonify

from web.unified_rph_web import (
    _docx, SUBJECT_LABELS, english_index, source_records, unit_options,
    pdp_options, verified_preview, create_blueprint,
)

class UnifiedWebRPHTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Flask(__name__)
        cls.app.register_blueprint(create_blueprint())
        cls.client = cls.app.test_client()
        cls.native_fake = patch("web.native_telegram_rph_client.request_native_rph",
            side_effect=lambda selected, fmt: _docx(selected))
        cls.native_fake.start()
        cls.addClassCleanup(cls.native_fake.stop)

    def test_all_subject_codes_have_one_shared_entry_point(self):
        self.assertEqual(set(SUBJECT_LABELS), {
            "ENGLISH", "BM", "MATH", "SCIENCE", "PI",
            "PJPK", "MORAL", "PSV", "SEJARAH", "ARAB", "MUZIK", "RBT",
        })
        self.assertEqual(sum(k.startswith("6/") for k in english_index()), 160)
        self.assertEqual(len(source_records(6, "ENGLISH")), 160)

    def test_moral_and_pjpk_are_source_backed_not_generic(self):
        moral = source_records(2, "MORAL")
        self.assertEqual(len(moral), 42)
        pj = source_records(2, "PJPK", "PJ")
        pk = source_records(2, "PJPK", "PK")
        self.assertGreater(len(pj), 20)
        self.assertGreater(len(pk), 20)
        self.assertTrue(all(r["token"].startswith("p-2-PJ-") for r in pj))
        self.assertTrue(all(r["token"].startswith("p-2-PK-") for r in pk))

    def test_wrong_subject_year_and_unit_are_rejected(self):
        r = source_records(6, "ENGLISH")[0]
        self.assertIsNotNone(verified_preview(6, "ENGLISH", r["unit"], r["token"]))
        self.assertIsNone(verified_preview(5, "ENGLISH", r["unit"], r["token"]))
        self.assertIsNone(verified_preview(6, "ENGLISH", "Wrong unit", r["token"]))
        self.assertIsNone(verified_preview(6, "BM", r["unit"], r["token"]))
        self.assertIsNone(verified_preview(2, "PSV", "Wrong unit", "v-2-001"))
        self.assertEqual(len(source_records(2, "PSV")), 42)

    @patch("web.unified_rph_web._account", return_value=(None, ({"error": "Login required"}, 401)))
    def test_non_authenticated_read_rejected(self, _):
        self.assertEqual(self.client.get("/api/web/rph/preview").status_code, 401)
        self.assertEqual(self.client.post("/api/web/rph/pdf",json={"reflection":"Contoh"}).status_code,401)

    @patch("web.unified_rph_web._has_paid_access", return_value=True)
    @patch("web.unified_rph_web._account", return_value=({"telegram_user_id":123},None))
    def test_custom_reflection_passes_only_in_download_body(self, *_):
        row=source_records(4,"ENGLISH")[0]
        args={"year":4,"subject":"ENGLISH","unit":row["unit"],"lesson":row["token"]}
        reflection="24 murid mencapai objektif.\nLatihan susulan."
        with patch("web.native_telegram_rph_client.request_native_rph",
                   side_effect=lambda _, fmt: BytesIO(fmt.encode())) as native:
            for fmt in ("word","pdf"):
                path="/api/web/rph/"+fmt
                response=self.client.post(path,query_string=args,json={"reflection":" "+reflection+" "})
                self.assertEqual(response.status_code,200,response.get_json())
                self.assertEqual(native.call_args.args[0]["teacher"]["reflection"],reflection)
                response=self.client.get(path,query_string=args)
                self.assertEqual(response.status_code,200)
                self.assertNotIn("reflection",native.call_args.args[0]["teacher"])
                native.reset_mock()
                for bad in (None,"x"*501,"a\n"*6+"a"):
                    response=self.client.post(path,query_string=args,json={"reflection":bad})
                    self.assertEqual(response.status_code,400)
                native.assert_not_called()

    @patch("web.unified_rph_web._has_paid_access", return_value=False)
    @patch("web.unified_rph_web._account", return_value=(
        {"authenticated":True,"telegram_user_id":123,"free_remaining":5},None))
    def test_full_preview_stays_gated_without_trial_debit(self, *_):
        r = source_records(6, "ENGLISH")[0]
        resp = self.client.get("/api/web/rph/preview", query_string={
            "year": 6, "subject": "ENGLISH", "unit": r["unit"], "lesson": r["token"],
        })
        self.assertEqual(resp.status_code, 403)

    @patch("web.unified_rph_web._has_paid_access", return_value=True)
    @patch("web.unified_rph_web._account", return_value=({"telegram_user_id": 123}, None))
    def test_english_y6_view_and_word_match_exact_selected_lesson(self, *_):
        r = source_records(6, "ENGLISH")[0]
        args = {"year": 6, "subject": "ENGLISH", "unit": r["unit"], "lesson": r["token"]}
        resp = self.client.get("/api/web/rph/preview", query_string=args)
        self.assertEqual(resp.status_code, 200, resp.get_json())
        payload = resp.get_json()
        self.assertEqual(payload["selection"], "e-6-001")
        self.assertEqual(payload["lesson"], 1)
        self.assertTrue(len(payload["fields"]) >= 8)
        word = self.client.get("/api/web/rph/word", query_string=args)
        self.assertEqual(word.status_code, 200)
        with ZipFile(__import__("io").BytesIO(word.data)) as zipdoc:
            doc = zipdoc.read("word/document.xml").decode()
            self.assertIn("Bahasa Inggeris", doc)
        self.assertEqual(word.headers["Cache-Control"], "no-store, private")
        self.assertEqual(self.client.get("/api/web/rph/preview", query_string={**args, "unit": "another topic"}).status_code, 503)
        self.assertEqual(self.client.get("/api/web/rph/word", query_string={**args, "subject": "MORAL"}).status_code, 503)

    @patch("web.unified_rph_web._has_paid_access", return_value=True)
    @patch("web.unified_rph_web._account", return_value=({"telegram_user_id": 123}, None))
    def test_english_year_4_and_5_real_source_files_and_teacher_details(self, *_):
        for year in (4, 5):
            records = source_records(year, "ENGLISH")
            self.assertEqual(len(records), 160, year)
            row = records[0]
            payload = verified_preview(year, "ENGLISH", row["unit"], row["token"])
            self.assertIsNotNone(payload, (year, row))
            query = {"year": year, "subject": "ENGLISH",
                     "unit": row["unit"], "lesson": row["token"],
                     "teacher_class": "5 Bestari", "teacher_date": "2027-03-08",
                     "teacher_time": "08:30"}
            result = self.client.get("/api/web/rph/preview", query_string=query)
            if year == 5:
                # The source file exists but Telegram's per-lesson release
                # manifest has no approvals. Never silently serve a different
                # Web-only Year 5 draft while Telegram uses another version.
                self.assertEqual(result.status_code, 503)
                self.assertEqual(result.get_json()["code"], "TELEGRAM_RPH_PARITY_NOT_READY")
                self.assertEqual(
                    self.client.get("/api/web/rph/word", query_string=query).status_code, 503)
                continue
            self.assertEqual(result.status_code, 200, result.get_json())
            self.assertEqual(result.get_json()["teacher"], {
                "class": "5 Bestari", "date": "2027-03-08", "time": "08:30",
                "students": ""})
            docx = self.client.get("/api/web/rph/word", query_string=query)
            self.assertEqual(docx.status_code, 200)
            with ZipFile(__import__("io").BytesIO(docx.data)) as z:
                xml = z.read("word/document.xml").decode("utf8")
                self.assertIn("5 Bestari", xml)
                self.assertIn("08/03/2027", xml)
                self.assertIn("08:30", xml)

    @patch("web.unified_rph_web._has_paid_access", return_value=True)
    @patch("web.unified_rph_web._account", return_value=({"telegram_user_id": 123}, None))
    def test_word_and_pdf_use_saved_roster_count_unless_teacher_overrides(self, *_):
        row = source_records(4, "ENGLISH")[0]
        query = {"year":4, "subject":"ENGLISH", "unit":row["unit"], "lesson":row["token"],
                 "teacher_class":"4 Bestari", "teacher_date":"2027-03-08",
                 "teacher_start":"08:30", "teacher_end":"09:30"}
        config = {"account_backend":"supabase"}
        with patch("web_v1_telegram_auth_routes._config", return_value=config), \
             patch("web.pbd_store.roster_count", return_value=28) as lookup, \
             patch("web.native_telegram_rph_client.request_native_rph",
                   side_effect=lambda _, fmt: BytesIO(fmt.encode())) as native:
            for fmt in ("word", "pdf"):
                response = self.client.get("/api/web/rph/" + fmt, query_string=query)
                self.assertEqual(response.status_code, 200, response.get_json())
                self.assertEqual(native.call_args.args[0]["teacher"]["students"], "28")
                lookup.assert_called_with(config, 123, {
                    "class_name":"eq.4 Bestari", "school_year":"eq.2027",
                })
            lookup.reset_mock()
            response = self.client.get("/api/web/rph/pdf", query_string={**query, "teacher_students":"26"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(native.call_args.args[0]["teacher"]["students"], "26")
            lookup.assert_not_called()
            lookup.return_value = 0
            response = self.client.get("/api/web/rph/word", query_string=query)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(native.call_args.args[0]["teacher"]["students"], "")

    @patch("web.unified_rph_web._has_paid_access", return_value=True)
    @patch("web.unified_rph_web._account", return_value=({"telegram_user_id": 123}, None))
    def test_print_context_rejects_invalid_and_ambiguous_metadata(self, *_):
        row = source_records(4, "ENGLISH")[0]
        base = {"year": 4, "subject": "ENGLISH",
                "unit": row["unit"], "lesson": row["token"]}
        bad = (
            {"teacher_class": "4 A<script>"},
            {"teacher_date": "2027-02-30"},
            {"teacher_date": "2001-02-03"},
            {"teacher_time": "49:99"},
            {"teacher_time": "hello"},
        )
        for addition in bad:
            response = self.client.get("/api/web/rph/preview",
                                       query_string={**base, **addition})
            self.assertEqual(response.status_code, 400, (addition,response.get_json()))
        repeated = self.client.get("/api/web/rph/word",
                                   query_string=list(base.items())+[
                                       ("teacher_class","4A"),("teacher_class","4B")])
        self.assertEqual(repeated.status_code, 400)

    @patch("web.unified_rph_web._has_paid_access", return_value=True)
    @patch("web.unified_rph_web._account", return_value=({"telegram_user_id": 123}, None))
    def test_unavailable_subject_is_explicitly_unavailable(self, *_):
        r = self.client.get("/api/web/rph/preview", query_string={"year": 2, "subject": "MATH", "unit": "Unit", "lesson": "33"})
        self.assertEqual(r.status_code, 503)
        self.assertEqual(r.get_json()["code"], "TELEGRAM_NATIVE_PDP_RPH_NOT_READY")
        invalid = self.client.get("/api/web/rph/preview", query_string={"year": 2, "subject": "ENGLISH", "unit": "Introduction", "lesson": "e-2-001", "component": "PJ"})
        self.assertEqual(invalid.status_code, 400)
        repeated = self.client.get("/api/web/rph/preview?year=6&year=2&subject=ENGLISH&unit=x&lesson=e-6-001")
        self.assertEqual(repeated.status_code, 400)

if __name__ == "__main__":
    unittest.main()
