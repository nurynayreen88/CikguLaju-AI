"""Isolated preview API tests; no production app imports."""
import unittest
from unittest.mock import patch
from tools.run_web_v1_preview import app


class PreviewApiTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    @patch('tools.run_web_v1_preview.Path.is_file', return_value=True)
    @patch('tools.run_web_v1_preview.available_subject_options')
    @patch.dict('os.environ', {'CIKGULAJU_WEB_PREVIEW_DB': '/tmp/preview-test.db'})
    def test_subjects_require_valid_year(self, options, is_file):
        options.side_effect = lambda db, year: (_ for _ in ()).throw(ValueError('invalid year')) if year == 0 else [{'value': 'ENGLISH', 'label': 'Bahasa Inggeris'}]
        self.assertEqual(self.client.get('/api/options?kind=subjects&year=0').status_code, 400)
        response = self.client.get('/api/options?kind=subjects&year=3')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(x['value'] == 'ENGLISH' for x in response.json))

    @patch.dict('os.environ', {'CIKGULAJU_WEB_PREVIEW_DB': ''})
    def test_subjects_fail_closed_without_database(self):
        self.assertEqual(self.client.get('/api/options?kind=subjects&year=3').status_code, 503)

    @patch('tools.run_web_v1_preview.available_subject_options')
    @patch.dict('os.environ', {'CIKGULAJU_WEB_PREVIEW_DB': '/tmp/preview-test.db'})
    def test_subjects_return_only_verified_catalog_results(self, options, is_file):
        options.return_value = [{'value': 'ENGLISH', 'label': 'Bahasa Inggeris'}]
        response = self.client.get('/api/options?kind=subjects&year=3')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, [{'value': 'ENGLISH', 'label': 'Bahasa Inggeris'}])
        options.assert_called_once_with('/tmp/preview-test.db', 3)

    @patch.dict('os.environ', {'CIKGULAJU_WEB_PREVIEW_DB': '/does/not/exist.db'})
    def test_missing_database_file_fails_closed(self):
        self.assertEqual(self.client.get('/api/options?kind=subjects&year=3').status_code, 503)

    def test_unknown_option_kind_is_bad_request(self):
        response = self.client.get("/api/options?kind=unknown&year=3")
        self.assertEqual(response.status_code, 400)

    @patch.dict('os.environ', {'CIKGULAJU_WEB_PREVIEW_DB': ''})
    def test_units_fail_closed_without_database(self):
        response = self.client.get('/api/options?kind=units&year=3&subject=ENGLISH')
        self.assertEqual(response.status_code, 503)

    @patch('tools.run_web_v1_preview.Path.is_file', return_value=True)
    @patch('tools.run_web_v1_preview.unit_options')
    @patch.dict('os.environ', {'CIKGULAJU_WEB_PREVIEW_DB': '/tmp/preview-test.db'})
    def test_units_return_only_catalog_results(self, options, is_file):
        options.return_value = [{'value': 'Welcome', 'label': 'Welcome'}]
        response = self.client.get('/api/options?kind=units&year=3&subject=ENGLISH')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json[0]['value'], 'Welcome')


if __name__ == '__main__':
    unittest.main()
