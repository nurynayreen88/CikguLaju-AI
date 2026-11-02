"""Contract tests for Telegram -> Web approved RPH metadata without network calls."""
import unittest
from web.authoritative_curriculum_source import CurriculumKey, SharedSourceUnavailable
from web.authoritative_http_source import AuthoritativeHttpCurriculumSource


class FakeResponse:
    status_code = 200
    def __init__(self, payload):
        self.payload = payload
    def json(self):
        return self.payload


class FakeTransport:
    def __init__(self, payload):
        self.payload = payload
        self.requests = []
    def get(self, url, *, params, headers, timeout, allow_redirects):
        self.requests.append((url, params, headers, allow_redirects))
        return FakeResponse(self.payload)


class ApprovedRphContractTests(unittest.TestCase):
    def test_telegram_metadata_contract_and_exact_rpt_id(self):
        transport = FakeTransport({"source": "telegram-runtime-v1", "items": [{
            "id": "english-rph-2-93",
            "title": "RPH English Tahun 2 Lesson 12",
            "type": "rph",
            "approved": True,
            "download_enabled": False,
        }]})
        adapter = AuthoritativeHttpCurriculumSource(
            "https://telegram.example", "x" * 40, transport=transport)
        result = adapter.get_approved_materials(CurriculumKey(2, "ENGLISH", "93"))
        self.assertEqual(result[0]["id"], "english-rph-2-93")
        url, params, headers, redirects = transport.requests[0]
        self.assertEqual(url, "https://telegram.example/internal/curriculum/v1/approved-materials")
        self.assertEqual(params, {"year": 2, "subject": "ENGLISH", "lesson": "93"})
        self.assertFalse(redirects)
        self.assertTrue(headers["Authorization"].startswith("Bearer "))

    def test_wrong_source_is_rejected(self):
        transport = FakeTransport({"source": "web-preview", "items": []})
        adapter = AuthoritativeHttpCurriculumSource(
            "https://telegram.example", "x" * 40, transport=transport)
        with self.assertRaises(SharedSourceUnavailable):
            adapter.get_approved_materials(CurriculumKey(2, "ENGLISH", "93"))

    def test_invalid_record_shape_is_rejected(self):
        transport = FakeTransport({"source": "telegram-runtime-v1", "items": ["not a record"]})
        adapter = AuthoritativeHttpCurriculumSource(
            "https://telegram.example", "x" * 40, transport=transport)
        with self.assertRaises(SharedSourceUnavailable):
            adapter.get_approved_materials(CurriculumKey(2, "ENGLISH", "93"))


if __name__ == "__main__":
    unittest.main()
