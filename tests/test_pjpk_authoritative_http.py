"""PJPK HTTP adapter contract tests; no network or production database."""
import unittest
from web.authoritative_http_source import AuthoritativeHttpCurriculumSource


class FakeResponse:
    status_code = 200
    def json(self):
        return {"source": "telegram-runtime-v1", "items": []}


class FakeTransport:
    def __init__(self):
        self.calls = []
    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return FakeResponse()


class PJPKHttpTests(unittest.TestCase):
    def setUp(self):
        self.transport = FakeTransport()
        self.source = AuthoritativeHttpCurriculumSource(
            "https://curriculum.example.org", "x" * 32, transport=self.transport
        )

    def test_pj_units_forward_component(self):
        self.source.list_units(2, "PJPK", "PJ")
        self.assertEqual(self.transport.calls[-1][1]["params"], {
            "year": 2, "subject": "PJPK", "component": "PJ"
        })

    def test_pk_lessons_forward_component(self):
        self.source.list_lessons(2, "PJPK", "Unit A", "PK")
        self.assertEqual(self.transport.calls[-1][1]["params"], {
            "year": 2, "subject": "PJPK", "unit": "Unit A", "component": "PK"
        })

    def test_pjpk_without_component_rejected_without_network(self):
        with self.assertRaises(ValueError):
            self.source.list_units(2, "PJPK")
        self.assertEqual(self.transport.calls, [])

    def test_other_subject_rejects_component(self):
        with self.assertRaises(ValueError):
            self.source.list_lessons(2, "ENGLISH", "Unit A", "PJ")
        self.assertEqual(self.transport.calls, [])

    def test_other_subject_preserves_old_contract(self):
        self.source.list_units(2, "ENGLISH")
        self.assertEqual(self.transport.calls[-1][1]["params"], {
            "year": 2, "subject": "ENGLISH"
        })


if __name__ == "__main__":
    unittest.main()
