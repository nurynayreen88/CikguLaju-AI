from datetime import date
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
    def test_aliases_both_download_one_pdf_through_telegram_without_local_fallback(self, *_):
        app = Flask(__name__)
        app.register_blueprint(create_blueprint())
        client = app.test_client()
        rows = {r["lesson"]: r for r in source_records(3, "ENGLISH")}
        with patch("web.native_telegram_integrated_english_client.request_integrated",
                   side_effect=lambda selected, fmt: [13, 14] if fmt == "metadata"
                   else BytesIO(b"%PDF-1.4\n" + b"0" * 1400)) as render:
            for n in (13, 14):
                args = {"year": 3, "subject": "ENGLISH", "unit": rows[n]["unit"],
                        "lesson": rows[n]["token"], "teacher_class": "3 Amanah",
                        "teacher_date": "2027-01-18", "teacher_start": "08:00",
                        "teacher_end": "09:00", "teacher_students": "24", "rph_context": "hari-ini"}
                available = client.get("/api/web/rph/availability", query_string=args)
                self.assertEqual(available.json["lessons"], [13, 14])
                response = client.get("/api/web/rph/pdf", query_string=args)
                self.assertEqual(response.status_code, 200, response.json)
                self.assertIn("013-014.pdf", response.headers["Content-Disposition"])
            self.assertEqual([c.args[1] for c in render.call_args_list],
                             ["metadata", "metadata", "pdf"] * 2)
