"""Tests for the authoritative remote curriculum reader."""
import unittest
from unittest.mock import Mock
from web.authoritative_http_source import AuthoritativeHttpCurriculumSource
from web.authoritative_curriculum_source import CurriculumKey, SharedSourceUnavailable


class RemoteCurriculumTests(unittest.TestCase):
    def setUp(self):
        self.transport = Mock()
        self.client = AuthoritativeHttpCurriculumSource(
            "https://curriculum.example.org", "a" * 40, transport=self.transport)

    def test_authenticated_read_only_request(self):
        response = Mock(status_code=200)
        response.json.return_value = {"source": "telegram-runtime-v1", "items": [{"value": "ENGLISH"}]}
        self.transport.get.return_value = response
        self.assertEqual(self.client.list_subjects(2), [{"value": "ENGLISH"}])
        args, kwargs = self.transport.get.call_args
        self.assertEqual(args[0], "https://curriculum.example.org/internal/curriculum/v1/subjects")
        self.assertEqual(kwargs["params"], {"year": 2})
        self.assertFalse(kwargs["allow_redirects"])
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer " + "a" * 40)

    def test_no_snapshot_fallback_on_invalid_response(self):
        for status, data in ((503, {}), (200, {"items": []}),
                             (200, {"source": "telegram-runtime-v1", "items": "bad"})):
            response = Mock(status_code=status)
            response.json.return_value = data
            self.transport.get.return_value = response
            with self.subTest(status=status, data=data), self.assertRaises(SharedSourceUnavailable):
                self.client.list_subjects(2)

    def test_rejects_insecure_source_and_bad_selection(self):
        for url in ("http://curriculum.example.org", "https://user@curriculum.example.org",
                    "https://curriculum.example.org:8443", "https://curriculum.example.org?q=1",
                    "https://curriculum.example.org/redirected-base"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                AuthoritativeHttpCurriculumSource(url, "a" * 40)
        with self.assertRaises(ValueError):
            self.client.list_lessons(2, "ENGLISH", "")
        with self.assertRaises(ValueError):
            self.client.get_approved_materials(CurriculumKey(2, "ENGLISH", ""))


if __name__ == "__main__":
    unittest.main()
