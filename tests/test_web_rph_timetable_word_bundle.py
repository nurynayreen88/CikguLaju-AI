"""Authenticated weekly Word/PDF composition and subscription quota."""

from io import BytesIO
from unittest import TestCase
from unittest.mock import patch
from uuid import uuid4

from docx import Document
from docx.enum.section import WD_SECTION_START
from docx.shared import Mm
from flask import Flask
from pypdf import PdfReader, PdfWriter

from web.rph_timetable_word_bundle import (
    WORD_RECEIPT_HEADER, pdf_receipt_signer, word_receipt_claim, word_receipt_signer,
)
from web.rph_weekly_quota import weekly_usage
from web.unified_rph_web import create_blueprint


class TimetableWordBundleTests(TestCase):
    secret = "bundle-session-secret"
    teacher = {"authenticated": True, "telegram_user_id": 123, "rakan_pembangun": True}
    origin = {"Origin": "https://localhost"}
    pdf_url = "/api/web/rph/timetable/pdf-bundle"
    bundle_url = "/api/web/rph/timetable/word-bundle"

    def setUp(self):
        self.teacher = self.teacher.copy()
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

    def submit(self, files, receipts, *, url=None, export=None):
        headers = dict(self.origin)
        if export:
            headers["X-RPH-Weekly-Export"] = str(export)
        return self.client.post(url or self.bundle_url, headers=headers, data={
            "document": [(BytesIO(content), f"lesson-{i}.docx") for i, content in enumerate(files)],
            "receipt": receipts,
        })

    def test_combines_verified_word_in_order_with_no_additional_usage(self):
        files = [self.document("Isnin | 3 Bestari", 14), self.document("Rabu | 4 Amanah", 10)]
        with (patch("web.rph_delivery_quota.authorize_rendered_document") as debit,
              patch("web.rph_weekly_quota.weekly_usage") as subscription_usage):
            response = self.submit(files, [self.signed(content) for content in files])
        debit.assert_not_called()
        subscription_usage.assert_not_called()
        self.assertEqual(response.status_code, 200)
        self.assertIn("CIKGULAJU_RPH_MINGGU_INI.docx", response.headers["Content-Disposition"])
        result = Document(BytesIO(response.data))
        self.assertEqual([table.cell(0, 0).text for table in result.tables],
                         ["Isnin | 3 Bestari", "Rabu | 4 Amanah"])
        self.assertEqual(len(result.sections), 2)
        self.assertEqual(result.sections[1].start_type, WD_SECTION_START.NEW_PAGE)
        self.assertEqual([round(section.left_margin.mm) for section in result.sections], [14, 10])
        self.assertEqual(self.client.get(self.bundle_url).json, {"available": True, "access_mode": "partner"})

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


    def test_active_subscription_shares_two_completed_exports_between_formats(self):
        self.teacher.update(rakan_pembangun=False, vip_expires_at="2099-12-31T00:00:00Z")
        docs = [self.document("RPH Word", 12)]
        word_receipts = [self.signed(docs[0])]
        pdfs = []
        for width in (595, 610):
            writer = PdfWriter()
            writer.add_blank_page(width=width, height=842)
            output = BytesIO()
            writer.write(output)
            pdfs.append(output.getvalue())
        pdf_signer = pdf_receipt_signer(self.secret)
        pdf_receipts = [pdf_signer.dumps(word_receipt_claim(123, doc)) for doc in pdfs]
        status = {"available": True, "remaining": 2, "usage_week_start": "2026-11-15",
                  "usage_week_end": "2026-11-21", "limit": 2}
        used = {}

        def debit(_config, uid, *, export_id=None, content_hash=None):
            self.assertEqual(uid, 123)
            if export_id in used:
                allowed = used[export_id] == content_hash
            else:
                allowed = len(used) < 2
                if allowed and export_id is not None:
                    used[export_id] = content_hash
            return {**status, "available": allowed, "remaining": 2 - len(used)}

        first, second = uuid4(), uuid4()
        with patch("web.rph_weekly_quota.weekly_usage", side_effect=debit) as usage:
            preflight = self.client.get(self.pdf_url)
            self.assertEqual(preflight.json, {"access_mode": "subscription", **status})
            self.assertEqual(used, {})
            self.assertEqual(self.submit(docs, word_receipts).status_code, 400)
            unavailable = self.submit(pdfs, word_receipts * 2, url=self.pdf_url, export=first)
            self.assertEqual(unavailable.status_code, 400)
            with patch("web.rph_timetable_word_bundle.compose_pdf_bundle", side_effect=ValueError):
                failed = self.submit(pdfs, pdf_receipts, url=self.pdf_url, export=first)
            self.assertEqual(failed.status_code, 503)
            self.assertEqual(usage.call_count, 1)
            pdf = self.submit(pdfs, pdf_receipts, url=self.pdf_url, export=first)
            self.assertEqual(pdf.status_code, 200)
            self.assertEqual(pdf.headers["X-RPH-Weekly-Remaining"], "1")
            self.assertEqual([int(p.mediabox.width) for p in PdfReader(BytesIO(pdf.data)).pages], [595, 610])
            word = self.submit(docs, word_receipts, export=second)
            self.assertEqual(word.status_code, 200)
            self.assertEqual(word.headers["X-RPH-Weekly-Remaining"], "0")
            replay = self.submit(pdfs, pdf_receipts, url=self.pdf_url, export=first)
            self.assertEqual(replay.status_code, 200)
            self.assertEqual(replay.headers["X-RPH-Weekly-Remaining"], "0")
            self.assertEqual(self.submit(pdfs, pdf_receipts, url=self.pdf_url, export=uuid4()).status_code, 429)
            self.assertEqual(self.submit(docs, word_receipts, export=first).status_code, 429)

    def test_legacy_trial_downloads_can_combine_paid_for_parts(self):
        self.teacher.update(rakan_pembangun=False, free_remaining=0)
        doc = self.document("RPH dibayar dengan kredit percubaan", 12)
        with patch("web.rph_weekly_quota.weekly_usage") as quota:
            response = self.submit([doc], [self.signed(doc)])
        self.assertEqual(response.status_code, 200)
        quota.assert_not_called()

    def test_pdf_source_response_has_signed_exact_bytes(self):
        writer = PdfWriter()
        writer.add_blank_page(width=595, height=842)
        output = BytesIO()
        writer.write(output)
        output.seek(0)
        with patch("web.native_telegram_bm_rph_client.verified_native_bm_available"), patch(
            "web.native_telegram_bm_rph_client.request_native_bm_rph", return_value=output
        ):
            result = self.client.get("/api/web/rph/pdf", query_string={
                "year": "2", "subject": "BM", "unit": "Unit 1", "lesson": "bm-2-pdp",
                "rph_context": "hari-ini",
            })
        self.assertEqual(result.status_code, 200)
        claim = pdf_receipt_signer(self.secret).loads(result.headers["X-RPH-PDF-Receipt"])
        self.assertEqual(claim, word_receipt_claim(123, result.data))


    def test_weekly_usage_preserves_the_quota_period_from_the_database(self):
        for start, end in (("2026-11-15", "2026-11-21"), ("2026-11-16", "2026-11-22")):
            with self.subTest(start=start), patch("web.rph_weekly_quota._request", return_value=[
                {"allowed": True, "remaining": 2, "usage_week_start": start},
            ]):
                status = weekly_usage({"account_backend": "supabase"}, 123)
                self.assertEqual((status["usage_week_start"], status["usage_week_end"]), (start, end))
