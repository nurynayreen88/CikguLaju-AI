"""Unauthenticated catalog API must fail closed before reading the preview DB."""
import unittest
from unittest.mock import patch
from tools.run_web_v1_preview import app


class PreviewApiTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    @patch('tools.run_web_v1_preview.available_subject_options')
    @patch('tools.run_web_v1_preview.unit_options')
    def test_unauthenticated_requests_never_read_catalog(self, units, subjects):
        for query in (
            'kind=subjects&year=3',
            'kind=subjects&year=0',
            'kind=units&year=3&subject=ENGLISH',
            'kind=units&year=99&subject=ENGLISH',
            'kind=pdp&year=abc&subject=ENGLISH',
            'kind=unknown&year=3',
        ):
            with self.subTest(query=query):
                response = self.client.get('/api/options?' + query)
                self.assertIn(response.status_code, (401, 503))
        subjects.assert_not_called()
        units.assert_not_called()

    @patch.dict('os.environ', {'CIKGULAJU_WEB_PREVIEW_DB': ''})
    def test_missing_database_fails_closed(self):
        response = self.client.get('/api/options?kind=subjects&year=3')
        self.assertIn(response.status_code, (401, 503))


if __name__ == '__main__':
    unittest.main()
