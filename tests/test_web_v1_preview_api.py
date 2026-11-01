"""Isolated preview API tests; no production app imports."""
import unittest
from unittest.mock import patch
from tools.run_web_v1_preview import app


class PreviewApiTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_subjects_require_valid_year(self):
        self.assertEqual(self.client.get('/api/options?kind=subjects&year=0').status_code, 400)
        response = self.client.get('/api/options?kind=subjects&year=3')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(x['value'] == 'ENGLISH' for x in response.json))

    @patch.dict('os.environ', {'CIKGULAJU_WEB_PREVIEW_DB': ''})
    def test_units_fail_closed_without_database(self):
        response = self.client.get('/api/options?kind=units&year=3&subject=ENGLISH')
        self.assertEqual(response.status_code, 503)

    @patch('tools.run_web_v1_preview.unit_options')
    @patch.dict('os.environ', {'CIKGULAJU_WEB_PREVIEW_DB': '/tmp/preview-test.db'})
    def test_units_return_only_catalog_results(self, options):
        options.return_value = [{'value': 'Welcome', 'label': 'Welcome'}]
        response = self.client.get('/api/options?kind=units&year=3&subject=ENGLISH')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json[0]['value'], 'Welcome')


if __name__ == '__main__':
    unittest.main()
