"""Mathematics user-facing quality hold before Web RPH trial credit debit."""
from __future__ import annotations

from io import BytesIO
from unittest.mock import patch
import unittest

from docx import Document
from flask import Flask
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4

from web.math_rph_delivery_quality_20261110 import (
    MathQualityReadError, inspect_math_rph_document,
)
from web.unified_rph_web import create_blueprint


UNIT = "u" + "b" * 24
SLOT = {
    "source": "telegram-native-pdp-sequence",
    "subject": "MATH", "year": 3, "unit": UNIT,
    "lesson": "Y3-MATH-060",
    "teacher": {"class": "4 Ikhlas", "date": "2026-11-10",
                "time": "08:00 - 09:00", "students": "30"},
}
PHASES_INVALID = (
    ("Set Induksi", 5), ("Aktiviti 1", 12), ("Aktiviti 2", 18),
    ("Aktiviti 3", 20), ("Pengukuhan", 5), ("Penutup", 5),
)
PHASES_VALID = (
    ("Set Induksi", 5), ("Aktiviti 1", 10), ("Aktiviti 2", 15),
    ("Aktiviti 3", 15), ("Pengukuhan", 10), ("Penutup", 5),
)
GENERIC = "Murid menunjukkan pengetahuan atau kemahiran berdasarkan standard"
MEASURABLE = "Murid menjawab sekurang-kurangnya 4 daripada 5 soalan darab wang."


def sample(fmt, *, bad=True):
    phases = PHASES_INVALID if bad else PHASES_VALID
    lines = [
        "RANCANGAN PENGAJARAN HARIAN MATEMATIK TAHUN 3",
        "STANDARD KANDUNGAN: " + ("4.4 4.4 Darab wang" if bad else "4.4 Darab wang"),
        "STANDARD PEMBELAJARAN: 4.4.1 Darab wang",
        "OBJEKTIF PEMBELAJARAN: " + (GENERIC if bad else MEASURABLE),
        "KRITERIA KEJAYAAN: 4 daripada 5 soalan tepat",
    ] + [f"{heading} ({minutes} minit)" for heading, minutes in phases]
    output = BytesIO()
    if fmt == "word":
        doc = Document()
        for line in lines:
            doc.add_paragraph(line)
        doc.save(output)
    else:
        canvas = Canvas(output, pagesize=A4)
        for i, line in enumerate(lines):
            canvas.drawString(36, 790 - 24 * i, line)
        canvas.showPage()
        canvas.save()
    return output.getvalue()


class MathQualityReadOnlyTests(unittest.TestCase):
    def test_problematic_year3_wang_detected_in_real_word_pdf(self):
        for fmt in ("word", "pdf"):
            with self.subTest(fmt=fmt):
                source = sample(fmt, bad=True)
                report = inspect_math_rph_document(SLOT, fmt, source)
                self.assertEqual(set(report["issues"]), {
                    "GENERIC_OBJECTIVE", "DUPLICATE_SK_DISPLAY",
                    "EXPLICIT_PHASES_EXCEED_SLOT",
                })
                self.assertEqual(report["slot_minutes"], 60)
                self.assertEqual(report["phase_minutes"], 65)
                self.assertEqual(report["explicit_phase_count"], 6)
                self.assertEqual(source, sample(fmt, bad=True))

    def test_complete_sixty_minute_plan_is_not_blocked(self):
        for fmt in ("word", "pdf"):
            with self.subTest(fmt=fmt):
                result = inspect_math_rph_document(SLOT, fmt, sample(fmt, bad=False))
                self.assertEqual(result["issues"], [])
                self.assertEqual(result["phase_minutes"], 60)

    def test_unproven_partial_timings_do_not_trigger_overrun(self):
        source = "MATEMATIK Tahun 3\n" + "\n".join([
            "Set Induksi (10 minit)",
            "Aktiviti 1 (20 minit)",
            "Aktiviti 2 (40 minit)",
            "RPH source wording and teacher review.",
        ])
        from web.math_rph_delivery_quality_20261110 import _explicit_phase_minutes
        self.assertEqual(len(_explicit_phase_minutes(source)), 3)
        self.assertEqual(_explicit_phase_minutes(source)["aktiviti 2"], 40)

    def test_no_cross_subject_effect_and_unreadable_mathematics_fail_closed(self):
        self.assertEqual(
            inspect_math_rph_document({**SLOT, "subject": "SCIENCE"}, "word", b"invalid")["issues"],
            [])
        for fmt in ("word", "pdf"):
            with self.assertRaises(MathQualityReadError):
                inspect_math_rph_document(SLOT, fmt, b"invalid")


class MathWebQuotaBoundaryTests(unittest.TestCase):
    def setUp(self):
        app = Flask("web-math-rph-quality-precharge")
        app.register_blueprint(create_blueprint())
        self.client = app.test_client()
        self.balance = 10
        self.debits = []
        self.account = {
            "authenticated": True, "telegram_user_id": 918003,
            "rakan_pembangun": False, "vip_until": None,
            "vip_expires_at": None, "free_remaining": 10,
        }
        patches = [
            patch("web.unified_rph_web._account",
                  side_effect=lambda: (dict(self.account, free_remaining=self.balance), None)),
            patch("web.native_telegram_sequence_rph_client.verified_native_sequence_available",
                  return_value=True),
            patch("web.native_telegram_sequence_rph_client.request_native_sequence_rph",
                  side_effect=lambda selected, fmt: BytesIO(sample(fmt, bad=self.bad))),
            patch("web_v1_telegram_auth_routes._config",
                  return_value={"account_backend": "supabase",
                                "supabase_url": "https://example.supabase.co",
                                "supabase_key": "synthetic-key"}),
            patch("web.rph_delivery_quota.authorize_rendered_document",
                  side_effect=self.debit),
        ]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)
        self.bad = True

    def debit(self, account, uid, data, url, key):
        self.debits.append((uid, len(data)))
        self.balance -= 1
        return {"allowed": True, "remaining": self.balance, "reference": "synthetic"}

    def query(self):
        return {
            "year": "3", "subject": "MATH", "unit": UNIT,
            "lesson": "Y3-MATH-060",
            "teacher_class": "4 Ikhlas", "teacher_date": "2026-11-10",
            "teacher_start": "08:00", "teacher_end": "09:00",
            "teacher_students": "30",
        }

    def test_defective_word_pdf_never_spend_trial_credit(self):
        for fmt in ("word", "pdf"):
            with self.subTest(fmt=fmt):
                response = self.client.get("/api/web/rph/" + fmt, query_string=self.query())
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.json["code"], "MATH_RPH_QUALITY_REVIEW_REQUIRED")
                self.assertNotIn(b"PK\x03\x04", response.data)
                self.assertNotIn(b"%PDF-", response.data)
        self.assertEqual(self.debits, [])
        self.assertEqual(self.balance, 10)

    def test_verified_sixty_minute_word_pdf_are_delivered_and_debited(self):
        self.bad = False
        for fmt in ("word", "pdf"):
            with self.subTest(fmt=fmt):
                response = self.client.get("/api/web/rph/" + fmt, query_string=self.query())
                self.assertEqual(response.status_code, 200, response.get_json(silent=True))
                self.assertEqual(response.headers["X-RPH-Access-Mode"], "trial")
        self.assertEqual(self.balance, 8)
        self.assertEqual(len(self.debits), 2)

    def test_paid_user_is_also_protected_from_invalid_math_output(self):
        self.account["rakan_pembangun"] = True
        response = self.client.get("/api/web/rph/word", query_string=self.query())
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json["code"], "MATH_RPH_QUALITY_REVIEW_REQUIRED")
        self.assertEqual(self.debits, [])
        self.bad = False
        response = self.client.get("/api/web/rph/word", query_string=self.query())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.debits, [])


if __name__ == "__main__":
    unittest.main()
