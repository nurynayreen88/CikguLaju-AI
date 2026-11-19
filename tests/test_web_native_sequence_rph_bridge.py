"""Web must use Telegram's grouped Sains/Matematik PdP source, not RPT weeks."""
import unittest
from unittest.mock import patch

from flask import Flask
from pathlib import Path

from web.native_telegram_sequence_rph_client import (
    _selection, list_native_units, NativeRPHUnavailable,
    SCIENCE_2027_ROUTE, DLP_ROUTE, MATH_SK_2027_ROUTE, MATH_SK_DPK_2027_ROUTE, SEQUENCE_ROUTE,
)
from web.unified_rph_web import create_blueprint
from web.native_verified_rpt_rph_client import _selection as _rpt_selection

ROOT=Path(__file__).resolve().parents[1]


class WebNativePdPBridgeTests(unittest.TestCase):
    def test_math_science_use_opaque_telegram_unit_and_pdp_code(self):
        unit="u"+"a"*24
        self.assertEqual(_selection(2,"MATH",unit,"M2-PDP-007")[1]["lesson"],
                         "M2-PDP-007")
        self.assertEqual(_selection(4,"SCIENCE",unit,"S4-PDP-011")[1]["subject"],
                         "SCIENCE")
        for bad in (("MATH","1","M2-PDP-007"),
                    ("ENGLISH",unit,"M2-PDP-007"),
                    ("MATH",unit,"")):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                _selection(2,*bad)

    def test_web_rph_proxies_only_to_native_telegram_engine(self):
        code=(ROOT/"web"/"unified_rph_web.py").read_text("utf-8")
        self.assertIn('if subject in ("MATH", "SCIENCE", "MATH_DLP", "SCIENCE_DLP", "MATH_DPK3"):',code)
        self.assertIn('verified_native_sequence_available(year, subject, unit, token)',code)
        self.assertIn('request_native_sequence_rph(selected, fmt)',code)
        self.assertIn('source": "telegram-native-pdp-sequence"',code)
        self.assertIn("authorize_rendered_document(",code)
        self.assertIn("lesson_tag",code)

    def test_math_science_navigation_from_active_telegram_only(self):
        code=(ROOT/"tools"/"run_web_v1_preview.py").read_text("utf-8")
        self.assertIn('if subject in ("MATH", "SCIENCE") and kind in ("units", "pdp"):',code)
        self.assertIn("list_native_units(year, subject)",code)
        self.assertIn("list_native_lessons(",code)
        self.assertIn("TELEGRAM_NATIVE_PDP_UNAVAILABLE",code)

    def test_dpk_units_and_lessons_do_not_use_legacy_route(self):
        units = {"source": "telegram-runtime-v1", "items": [
            {"value": f"u{i:024x}", "label": f"Unit {i}"} for i in range(8)
        ]}
        with patch("web.native_telegram_sequence_rph_client._read", return_value=units) as read:
            unit = list_native_units(2, "MATH_DPK3")[0]["value"]
            self.assertEqual(read.call_args.kwargs, {"route": MATH_SK_DPK_2027_ROUTE})
        route, selection = _selection(2, "MATH_DPK3", unit, "SK27-DPK3-MATH-Y2-L117")
        self.assertEqual((route, selection["subject"]), (MATH_SK_DPK_2027_ROUTE, "MATH"))
        for year, subject, selected_unit, lesson in (
            (2, "MATH", unit, "SK27-DPK3-MATH-Y2-L117"),
            (2, "MATH_DPK3", unit, "SK27-DPK3-MATH-Y3-L117"),
            (3, "MATH_DPK3", unit, "MT3-PDP-117"),
            (4, "MATH_DPK3", unit, "SK27-DPK3-MATH-Y4-L117"),
        ):
            with self.assertRaises(ValueError):
                _selection(year, subject, selected_unit, lesson)


    def test_new_science_catalogue_cannot_relabel_legacy_choices(self):
        verified = {"source": "telegram-runtime-v1", "items": [
            {"value": "u" + "a" * 24, "label": "Unit 1: Kemahiran Saintifik"}]}
        with patch("web.native_telegram_sequence_rph_client._read", return_value=verified) as read:
            new, = list_native_units(5, "SCIENCE")
            self.assertEqual(new["value"], "v" + "a" * 24)
            self.assertEqual(read.call_args.kwargs, {"route": SCIENCE_2027_ROUTE})
            legacy, = list_native_units(5, "SCIENCE", current_unit=verified["items"][0]["value"])
            self.assertEqual(legacy, verified["items"][0])
            self.assertEqual(read.call_args.kwargs, {})
            route, selection = _selection(5, "SCIENCE", new["value"], "SK27-SCI-Y5-PDP-001")
            self.assertEqual(route, SCIENCE_2027_ROUTE)
            self.assertEqual(selection["unit"], legacy["value"])
        with patch("web.native_telegram_sequence_rph_client._read",
                   side_effect=[NativeRPHUnavailable("missing"), verified]):
            self.assertEqual(list_native_units(5, "SCIENCE"), verified["items"])
        with self.assertRaises(ValueError):
            _selection(6, "SCIENCE", new["value"])
        with patch("web.native_telegram_sequence_rph_client._read", return_value=verified) as read:
            year6, = list_native_units(6, "SCIENCE")
            self.assertEqual(year6["value"], "w" + "a" * 24)
            route, selection = _selection(6, "SCIENCE", year6["value"], "SK27-SCI-Y6-PDP-013")
            self.assertEqual(route, "/internal/rph/v1/sains-sk-y6-2027")
            self.assertEqual(selection["unit"], "u" + "a" * 24)
            self.assertEqual(read.call_args.kwargs, {"route": route})
        with self.assertRaises(ValueError):
            _selection(5, "SCIENCE", year6["value"])

    def test_dlp_exact_ids_keep_year_and_subject(self):
        self.assertEqual(_selection(4, "SCIENCE_DLP", "10", "DLP-SCI-Y4-L59")[0], DLP_ROUTE)
        self.assertEqual(_selection(4, "SCIENCE_DLP", "10", "DLP-SCI-Y4-R10")[0], DLP_ROUTE)
        self.assertEqual(_selection(4, "MATH_DLP", "08", "DLP-MAT-Y4-L69")[0], DLP_ROUTE)
        self.assertEqual(_selection(4, "MATH_DLP", "08", "DLP-MAT-Y4-R08")[0], DLP_ROUTE)
        for subject, unit, lesson in (("MATH_DLP", "01", "DLP-SCI-Y4-L01"),
                                      ("MATH_DLP", "08", "DLP-MAT-Y4-L70"),
                                      ("MATH_DLP", "08", "DLP-MAT-Y4-R09"),
                                      ("SCIENCE_DLP", "11", "DLP-SCI-Y4-L59"),
                                      ("SCIENCE_DLP", "10", "DLP-SCI-Y4-L60"),
                                      ("SCIENCE_DLP", "10", "DLP-SCI-Y4-R11"),
                                      ("SCIENCE_DLP", "10", "DLP-SCI-Y5-R10")):
            with self.subTest(subject=subject, unit=unit, lesson=lesson), self.assertRaises(ValueError):
                _selection(4, subject, unit, lesson)
        self.assertEqual(_selection(5, "MATH_DLP", "08", "DLP-MATH-Y5-L61")[0], DLP_ROUTE)
        self.assertEqual(_selection(5, "SCIENCE_DLP", "10", "DLP-SCI-Y5-R10")[0], DLP_ROUTE)
        self.assertEqual(_selection(6, "MATH_DLP", "01", "DLP-MATH-Y6-L01")[0], DLP_ROUTE)
        self.assertEqual(_selection(6, "SCIENCE_DLP", "13", "DLP-SCI-Y6-R09")[0], DLP_ROUTE)
        for unit, lesson in (("14", "DLP-SCI-Y6-L14"), ("01", "DLP-MATH-Y6-L01"),
                             ("01", "DLP-SCI-Y6-L53"), ("01", "DLP-SCI-Y2-L01")):
            with self.subTest(unit=unit, lesson=lesson), self.assertRaises(ValueError):
                _selection(6, "SCIENCE_DLP", unit, lesson)
        for year, unit, lesson in ((5, "01", "DLP-MATH-Y6-L01"), (6, "09", "DLP-MATH-Y6-L01"),
                                   (6, "01", "DLP-MATH-Y6-R09"), (6, "01", "DLP-MATH-Y2-L01")):
            with self.subTest(year=year, unit=unit, lesson=lesson), self.assertRaises(ValueError):
                _selection(year, "MATH_DLP", unit, lesson)

    def test_math_sk_2027_routes_keep_legacy_and_dlp_selections_intact(self):
        unit = "u" + "a" * 24
        data = {"source": "telegram-runtime-v1", "items": [
            {"value": unit, "label": "Unit 7 • Koordinat, nisbah dan kadaran"}]}
        with patch("web.native_telegram_sequence_rph_client._read", return_value=data) as read:
            for year in (4, 5, 6):
                new, = list_native_units(year, "MATH")
                self.assertEqual(new["value"], "m" + unit[1:])
                self.assertEqual(read.call_args.kwargs, {"route": MATH_SK_2027_ROUTE})
                route, selection = _selection(year, "MATH", new["value"], f"SK27-MATH-Y{year}-L097")
                self.assertEqual(route, MATH_SK_2027_ROUTE)
                self.assertEqual(selection["unit"], unit)
                self.assertEqual(list_native_units(year, "MATH", current_unit=unit), data["items"])
                self.assertEqual(read.call_args.kwargs, {})
            self.assertEqual(_selection(6, "MATH", unit, "MT6-PDP-097")[0], SEQUENCE_ROUTE)
            with self.assertRaises(ValueError):
                _selection(3, "MATH", new["value"])
            with self.assertRaises(ValueError):
                _selection(6, "MATH_DLP", new["value"])

    def test_web_options_preserve_science_completion_and_enable_mathematics_in_dlp_year4(self):
        from tools.run_web_v1_preview import app

        from web.rph_today_progress import lesson_signer

        config = {"CIKGULAJU_WEB_SESSION_SECRET": "local-test-secret", "account_backend": "supabase"}
        unit = {"value": "08", "label": "Unit 8 Materials"}
        lesson = {"value": "DLP-SCI-Y4-L46", "label": "Lesson 46 Sources of Basic Materials"}
        review = {"value": "DLP-SCI-Y4-R08", "label": "Review 08 Materials Review"}
        invalid = {"value": "DLP-SCI-Y4-R11", "label": "Review 11"}
        math_lessons = [{"value": "DLP-MAT-Y4-L69", "label": "Lesson 69"},
                        {"value": "DLP-MAT-Y4-R08", "label": "Review 08"}]
        with (
            patch("web_v1_telegram_auth_routes._config", return_value=config),
            patch("web_v1_sessions.verify_session_ticket", return_value=123),
            patch("web_v1_telegram_auth_routes._lookup", return_value={"telegram_user_id": 123}),
            patch("web.native_telegram_sequence_rph_client.list_native_units", return_value=[unit]) as units,
            patch("web.native_telegram_sequence_rph_client.list_native_lessons", return_value=[lesson, review, invalid]) as lessons,
        ):
            client = app.test_client()
            selection = {"curriculum": "dlp", "year": 4, "subject": "SCIENCE_DLP"}
            response = client.get("/api/options", query_string={**selection, "kind": "units"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json, [unit])
            response = client.get("/api/options", query_string={
                **selection, "kind": "pdp", "unit": "08", "rph_today": "1",
            })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers["Vary"], "Cookie")
            signer = lesson_signer(config)
            first, second, bad = response.json
            self.assertEqual(signer.loads(first["completion_token"]), [123, 4, "SCIENCE_DLP", "", 46])
            self.assertEqual(signer.loads(second["completion_token"]), [123, 4, "SCIENCE_DLP", "", 108])
            self.assertNotIn("completion_token", bad)
            response = client.get("/api/options", query_string={**selection, "kind": "units", "subject": "MATH_DLP"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json, [unit])
            self.assertEqual([args.args for args in units.call_args_list],
                             [(4, "SCIENCE_DLP"), (4, "MATH_DLP")])
            lessons.assert_called_once_with(4, "SCIENCE_DLP", "08")
            lessons.return_value = math_lessons
            response = client.get("/api/options", query_string={
                **selection, "subject": "MATH_DLP", "kind": "pdp", "unit": "08", "rph_today": "1",
            })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json, math_lessons)
            self.assertNotIn("completion_token", response.json[0])
            lessons.assert_called_with(4, "MATH_DLP", "08")

    @patch("web.unified_rph_web._has_paid_access", return_value=True)
    @patch("web.unified_rph_web._account", return_value=({"telegram_user_id": 123}, None))
    def test_web_availability_uses_verified_dlp_service(self, *_):
        app = Flask(__name__)
        app.register_blueprint(create_blueprint())
        for year, subject, prefix in ((4, "SCIENCE_DLP", "SCI"), (4, "MATH_DLP", "MAT"),
                                      (5, "MATH_DLP", "MATH"), (5, "SCIENCE_DLP", "SCI"),
                                      (6, "MATH_DLP", "MATH"), (6, "SCIENCE_DLP", "SCI")):
            selection = {"year": year, "subject": subject, "unit": "01",
                         "lesson": f"DLP-{prefix}-Y{year}-L01"}
            with patch("web.native_telegram_sequence_rph_client._read", return_value={"available": True}) as remote:
                result = app.test_client().get("/api/web/rph/availability", query_string=selection)
                self.assertEqual(result.status_code, 200)
                self.assertEqual(result.json["generator"], "telegram-native")
                remote.assert_called_once_with("availability", selection, route=DLP_ROUTE)


if __name__=="__main__":
    unittest.main()
