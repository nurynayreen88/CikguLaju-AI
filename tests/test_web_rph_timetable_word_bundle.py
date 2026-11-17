"""Authenticated weekly Word composition and duplicate-charge protection."""

from io import BytesIO
from unittest import TestCase
from unittest.mock import patch

from docx import Document
from docx.enum.section import WD_SECTION_START
from docx.shared import Mm
from flask import Flask

from web.rph_timetable_word_bundle import (
    WORD_RECEIPT_HEADER, word_receipt_claim, word_receipt_signer,
)
from web.unified_rph_web import create_blueprint


class TimetableWordBundleTests(TestCase):
    secret = "bundle-session-secret"
    teacher = {"authenticated": True, "telegram_user_id": 123, "rakan_pembangun": True}
    origin = {"Origin": "https://localhost"}
    bundle_url = "/api/web/rph/timetable/word-bundle"

    def setUp(self):
        app = Flask(__name__)
        app.register_blueprint(create_blueprint())
        self.client = app.test_client()
        for target, value in (
            ("web.unified_rph_web._account", (self.teacher, None)),
            ("web_v1_telegram_auth_routes._config", {"CIKGULAJU_WEB_SESSION_SECRET": self.secret}),
        ):
            mock = patch(target, return_value=value)
            mock.start()
            self.addCleanup(mock.stop)

    def document(self, text, margin):
        document = Document()
        document.sections[0].left_margin = Mm(margin)
        document.add_table(rows=1, cols=1).cell(0, 0).text = text
        buffer = BytesIO()
        document.save(buffer)
        return buffer.getvalue()

    def signed(self, content, uid=123):
        return word_receipt_signer(self.secret).dumps(word_receipt_claim(uid, content))

    def submit(self, files, receipts):
        return self.client.post(self.bundle_url, headers=self.origin, data={
            "document": [(BytesIO(content), f"lesson-{i}.docx") for i, content in enumerate(files)],
            "receipt": receipts,
        })

    def test_combines_verified_word_in_order_with_no_additional_usage(self):
        files = [self.document("Isnin | 3 Bestari", 14), self.document("Rabu | 4 Amanah", 10)]
        with patch("web.rph_delivery_quota.authorize_rendered_document") as debit:
            response = self.submit(files, [self.signed(content) for content in files])
        debit.assert_not_called()
        self.assertEqual(response.status_code, 200)
        self.assertIn("CIKGULAJU_RPH_MINGGU_INI.docx", response.headers["Content-Disposition"])
        result = Document(BytesIO(response.data))
        self.assertEqual([table.cell(0, 0).text for table in result.tables],
                         ["Isnin | 3 Bestari", "Rabu | 4 Amanah"])
        self.assertEqual(len(result.sections), 2)
        self.assertEqual(result.sections[1].start_type, WD_SECTION_START.NEW_PAGE)
        self.assertEqual([round(section.left_margin.mm) for section in result.sections], [14, 10])
        self.assertEqual(self.client.get(self.bundle_url).json, {"available": True})

    def test_requires_a_receipt_bound_to_the_same_bytes_and_account(self):
        original = self.document("RPH asal", 14)
        other = self.document("RPH lain", 14)
        with patch("web.rph_timetable_word_bundle.compose_word_bundle") as compose:
            for receipt in (self.signed(other), self.signed(original, uid=987), "invalid"):
                result = self.submit([original], [receipt])
                self.assertEqual(result.status_code, 400)
        compose.assert_not_called()

    def test_normal_timetable_word_delivers_a_receipt_for_the_exact_file(self):
        content = self.document("Kandungan Word RPH", 14)
        with patch("web.native_telegram_bm_rph_client.verified_native_bm_available"), patch(
            "web.native_telegram_bm_rph_client.request_native_bm_rph", return_value=BytesIO(content)
        ):
            result = self.client.get("/api/web/rph/word", query_string={
                "year": "2", "subject": "BM", "unit": "Unit 1", "lesson": "bm-2-pdp",
                "rph_context": "hari-ini",
            })
        self.assertEqual(result.status_code, 200)
        claim = word_receipt_signer(self.secret).loads(result.headers[WORD_RECEIPT_HEADER])
        self.assertEqual(claim, word_receipt_claim(123, result.data))
