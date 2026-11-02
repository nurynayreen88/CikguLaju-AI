"""Offline tests for render-then-authorize Web download boundary."""
import unittest
from web.rph_download_pipeline import prepare_approved_download

PDF = "application/pdf"


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.account = {"authenticated": True, "telegram_user_id": 123, "free_remaining": 2}

    def debit(self, url, key, uid, reference):
        self.calls.append(reference)
        return {"ok": True, "remaining": 1}

    def run_pipeline(self, renderer, account=None):
        return prepare_approved_download(
            object(), "pdf", self.account if account is None else account,
            123, "https://example.supabase.co", "secret",
            debit=self.debit, renderer=renderer)

    def test_render_then_atomic_debit(self):
        result = self.run_pipeline(lambda r, f: (b"%PDF-1.4", PDF))
        self.assertTrue(result["allowed"])
        self.assertEqual(result["document"], b"%PDF-1.4")
        self.assertEqual(len(self.calls), 1)

    def test_render_failure_never_debits(self):
        for renderer in (lambda r, f: (b"", PDF),
                         lambda r, f: (b"data", "text/plain")):
            with self.subTest(renderer=renderer):
                with self.assertRaises(ValueError):
                    self.run_pipeline(renderer)
        self.assertEqual(self.calls, [])

    def test_paid_user_no_trial_debit(self):
        result = self.run_pipeline(lambda r, f: (b"%PDF", PDF),
                                   {**self.account, "rakan_pembangun": True})
        self.assertTrue(result["allowed"])
        self.assertEqual(self.calls, [])

    def test_exhausted_trial_returns_no_document(self):
        result = self.run_pipeline(lambda r, f: (b"%PDF", PDF),
                                   {**self.account, "free_remaining": 0})
        self.assertFalse(result["allowed"])
        self.assertIsNone(result["document"])
        self.assertEqual(self.calls, [])

    def test_invalid_format_never_renders_or_debits(self):
        render_calls = []
        def renderer(rph, fmt):
            render_calls.append(fmt)
            return b"data", PDF
        with self.assertRaises(ValueError):
            prepare_approved_download(
                object(), "txt", self.account, 123,
                "https://example.supabase.co", "secret",
                debit=self.debit, renderer=renderer)
        self.assertEqual(render_calls, [])
        self.assertEqual(self.calls, [])


if __name__ == "__main__":
    unittest.main()
