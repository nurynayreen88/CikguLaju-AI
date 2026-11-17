from datetime import date
import os
from io import BytesIO
from unittest import TestCase
from unittest.mock import patch

from flask import Flask

from web.rph_hari_ini_web import day_payload, weekly_rpt_suggestion
from web.unified_rph_web import create_blueprint, source_records


class IntegratedWebTests(TestCase):
    @patch("web.native_telegram_integrated_english_client.integrated_enabled", return_value=True)
    def test_one_pair_is_one_hour_in_capacity_and_last_week_is_october(self, _flag):
        now = date(2027, 1, 4)
        entry = {"day": "Isnin", "class_name": "2 Amanah", "subject": "English",
                 "start": "08:00", "end": "09:00"}
        day = day_payload({"state_name": "Selangor"}, {"entries": [entry]}, now, today=now)
        first = day["entries"][0]
        self.assertEqual(first["rpt_suggestion"]["sessions"], [[1], [2, 3], [4]])
        self.assertEqual(first["rpt_capacity"]["required_minutes"], 180)
        late = weekly_rpt_suggestion("Selangor", date(2027, 11, 1), "ENGLISH", 2)
        self.assertEqual(late["sessions"], [])

    @patch("web.native_telegram_integrated_english_client.integrated_enabled", return_value=True)
    @patch("web.unified_rph_web._has_paid_access", return_value=True)
    @patch("web.unified_rph_web._account", return_value=({"telegram_user_id": 123}, None))
    def test_aliases_both_download_one_word_and_pdf_through_telegram(self, *_):
        app = Flask(__name__)
        app.register_blueprint(create_blueprint())
        client = app.test_client()
        rows = {r["lesson"]: r for r in source_records(3, "ENGLISH")}
        with patch("web.native_telegram_integrated_english_client.request_integrated",
                   side_effect=lambda selected, fmt: [13, 14] if fmt == "metadata"
                   else BytesIO(b"PK\x03\x04word") if fmt == "word"
                   else BytesIO(b"%PDF-1.4\n" + b"0" * 1400)) as render:
            for n in (13, 14):
                args = {"year": 3, "subject": "ENGLISH", "unit": rows[n]["unit"],
                        "lesson": rows[n]["token"], "teacher_class": "3 Amanah",
                        "teacher_date": "2027-01-18", "teacher_start": "08:00",
                        "teacher_end": "09:00", "teacher_students": "24", "rph_context": "hari-ini"}
                available = client.get("/api/web/rph/availability", query_string=args)
                self.assertEqual(available.json["lessons"], [13, 14])
                for fmt, extension in (("word", "docx"), ("pdf", "pdf")):
                    response = client.get(f"/api/web/rph/{fmt}", query_string=args)
                    self.assertEqual(response.status_code, 200, response.json)
                    self.assertIn(f"013-014.{extension}", response.headers["Content-Disposition"])
                    self.assertEqual(response.headers["X-RPH-Generator"], "telegram-native")
                    response.close()
            self.assertEqual([c.args[1] for c in render.call_args_list],
                             ["metadata", "metadata", "word", "metadata", "pdf"] * 2)


    def test_revised_rpt_requires_verified_bytes_and_preserves_cover_entitlement(self):
        from web.rpt_2027_all_http import ROOT, create_all_rpt_blueprint
        from web_v1_sessions import issue_session_ticket
        from web_v1_telegram_auth_routes import COOKIE

        app = Flask(__name__)
        app.register_blueprint(create_all_rpt_blueprint())
        client = app.test_client()
        conf = {"CIKGULAJU_WEB_SESSION_SECRET": "local-test-session-" * 3}
        secret = conf["CIKGULAJU_WEB_SESSION_SECRET"]
        access = {"telegram_user_id": 123, "authenticated": True, "rakan_pembangun": True}
        with patch.dict(os.environ, {"CIKGULAJU_ENGLISH_2027_INTEGRATED_RPH_ENABLED": "1"}), \
                patch("web_v1_telegram_auth_routes._config", return_value=conf), \
                patch("web_v1_telegram_auth_routes._lookup", return_value=access):
            url = "/api/rpt/2027/all/english/2.pdf"
            self.assertEqual(client.get(url).status_code, 401)
            client.set_cookie(COOKIE, issue_session_ticket(123, secret))
            response = client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers["X-RPT-Personalization-Allowed"], "1")
            path = ROOT / "english" / "RPT_English_SK_2027_Year_2_A_B.pdf"
            self.assertEqual(response.data, path.read_bytes())
            response.close()
            access["rakan_pembangun"] = False
            response = client.get(url)
            self.assertEqual(response.headers["X-RPT-Personalization-Allowed"], "0")
            response.close()


    @patch("web.native_telegram_integrated_english_client.integrated_enabled", return_value=True)
    @patch("web.unified_rph_web._account", return_value=({"telegram_user_id": 123}, None))
    def test_both_aliases_list_and_download_the_same_pair_materials(self, *_):
        app = Flask(__name__)
        app.register_blueprint(create_blueprint())
        client = app.test_client()
        rows = {row["lesson"]: row for row in source_records(3, "ENGLISH")}
        bridge = "web.native_telegram_extra_materials_20261106."
        original = b"ID3" + b"x" * 1000
        listing = {"source": "telegram-english-paired-materials-2027", "year": 3,
                   "lessons": [13, 14], "items": [
                       {"id": "student-book", "title": "Student’s Book • Lesson 013 + 014"},
                       {"id": "audio-1", "title": "Audio • Lesson 014"}]}
        with patch(bridge + "_json", return_value=listing) as source, patch(
            bridge + "_get", return_value=original,
        ) as fetch:
            for lesson in (13, 14):
                args = {"year": 3, "subject": "ENGLISH", "unit": rows[lesson]["unit"],
                        "lesson": rows[lesson]["token"], "paired": 1}
                response = client.get("/api/web/rph/extra-materials", query_string=args)
                assert response.status_code == 200
                assert response.json["lessons"] == [13, 14]
                assert [item["type"] for item in response.json["items"]] == ["textbook", "audio"]
                source.assert_called_with("/internal/rph/v1/english-paired-materials",
                                          {"year": 3, "lesson": 13, "partner": 14})
                audio = client.get(response.json["items"][1]["url"])
                assert audio.status_code == 200
                assert audio.data == original
                assert "L013-014_audio-1.mp3" in audio.headers["Content-Disposition"]
                fetch.assert_called_with("/internal/rph/v1/english-paired-materials/audio-1",
                                         {"year": 3, "lesson": 13, "partner": 14},
                                         accept="audio/mpeg", limit=12 * 1024 * 1024)
            with patch(bridge + "_json", return_value={**listing, "lessons": [12, 13]}):
                assert client.get("/api/web/rph/extra-materials", query_string=args).status_code == 503
            assert client.get("/api/web/rph/english-paired-material/audio-9", query_string=args).status_code == 404
            with (patch(bridge + "_json", return_value=None),
                  patch(bridge + "english_workbook_metadata", return_value="Activity Book • Lesson 014"),
                  patch(bridge + "english_student_book_metadata", return_value=None),
                  patch(bridge + "english_audio_tracks", return_value=[])):
                fallback = client.get("/api/web/rph/extra-materials", query_string=args)
                assert "Lesson 014" in fallback.json["pair_note"]
                assert fallback.json["items"][0]["url"].startswith("/api/web/rph/english-workbook?")

    @patch("web.native_telegram_integrated_english_client.integrated_enabled", return_value=True)
    @patch("web.unified_rph_web._account", return_value=({"telegram_user_id": 123}, None))
    def test_verified_online_book_view_for_both_pair_aliases_without_pdf(self, *_):
        app = Flask(__name__)
        app.register_blueprint(create_blueprint())
        client = app.test_client()
        bridge = "web.native_telegram_extra_materials_20261106.english_paired_materials"
        cases = [(3, (1, 2), "workbook", "rmzft/wwgq", 3, "2"),
                 (3, (6, 7), "workbook", "rmzft/wwgq", 4, "3"),
                 (6, (88, 89), "student-book", "hykyg/rrpd", 75, "75, 78")]
        for year, pair, asset, viewer, leaf, pages in cases:
            with self.subTest(year=year, pair=pair):
                rows = {row["lesson"]: row for row in source_records(year, "ENGLISH")}
                results = []
                for lesson in pair:
                    args = {"year": year, "subject": "ENGLISH", "unit": rows[lesson]["unit"],
                            "lesson": rows[lesson]["token"], "paired": 1}
                    with patch(bridge, return_value=[]):
                        result = client.get("/api/web/rph/extra-materials", query_string=args)
                    self.assertEqual(result.status_code, 200)
                    item, = result.json["items"]
                    self.assertEqual(item["action"], "Buka Buku Asal")
                    self.assertEqual(item["url"], f"https://online.anyflip.com/{viewer}/mobile/index.html?pageIndex={leaf}")
                    self.assertTrue(item["title"].endswith(f"m/s {pages}"))
                    results.append(item)
                    with patch(bridge, return_value=[{"id": asset, "title": "Buku PDF"}]):
                        result = client.get("/api/web/rph/extra-materials", query_string=args)
                    self.assertEqual([item["action"] for item in result.json["items"]], ["Download"])
                self.assertEqual(*results)
