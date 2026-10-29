"""Unit tests for fail-closed KP2027 standards audit; no DB access."""
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("audit_standards", Path(__file__).with_name("audit_standards.py"))
audit_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_module)


def sample():
    return {"curriculum": "KP2027", "year": 1, "subject": "Alam dan Manusia",
            "unit": "Unit disahkan", "lesson": 1, "standard_code": "KOD-UNTUK-UJIAN",
            "standard_text": "Teks untuk ujian sahaja", "source_url": "https://www.moe.gov.my/",
            "source_page": 1, "verification_status": "pending"}


class AuditTests(unittest.TestCase):
    def test_empty_rejected(self):
        self.assertTrue(audit_module.audit([]))

    def test_pending_structurally_valid_but_not_approved(self):
        row = sample()
        self.assertEqual(audit_module.audit([row]), [])
        self.assertNotEqual(row["verification_status"], "approved")

    def test_wrong_curriculum_rejected(self):
        row = sample()
        row["curriculum"] = "KSSR"
        self.assertTrue(audit_module.audit([row]))

    def test_missing_source_rejected(self):
        row = sample()
        row["source_url"] = ""
        self.assertTrue(audit_module.audit([row]))

    def test_duplicates_rejected(self):
        row = sample()
        self.assertTrue(audit_module.audit([row, dict(row)]))

    def test_malformed_identity_does_not_crash(self):
        row = sample()
        row["unit"] = ["unexpected", "list"]
        self.assertTrue(audit_module.audit([row]))

    def test_malformed_url_does_not_crash(self):
        row = sample()
        row["source_url"] = "https://[invalid-ipv6"
        self.assertTrue(audit_module.audit([row]))

    def test_non_https_source_rejected(self):
        row = sample()
        row["source_url"] = "http://example.com/standards.pdf"
        self.assertTrue(audit_module.audit([row]))

    def test_invalid_approval_date_rejected(self):
        row = sample()
        row["verification_status"] = "approved"
        row["approved_by"] = "reviewer"
        row["approved_at"] = "tomorrow"
        self.assertTrue(audit_module.audit([row]))

    def test_approval_requires_reviewer_and_date(self):
        row = sample()
        row["verification_status"] = "approved"
        self.assertTrue(audit_module.audit([row]))
        row["approved_by"] = "reviewer"
        row["approved_at"] = "2026-10-29"
        self.assertEqual(audit_module.audit([row]), [])


if __name__ == "__main__":
    unittest.main()
