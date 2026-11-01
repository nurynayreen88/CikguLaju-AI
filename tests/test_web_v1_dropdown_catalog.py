"""Isolated tests for read-only dropdown navigation."""
import unittest
from unittest.mock import patch
from web_v1_dropdown_catalog import subject_options, unit_options, pdp_options


class DropdownTests(unittest.TestCase):
    def test_year_validation(self):
        with self.assertRaises(ValueError):
            subject_options(0)
        with self.assertRaises(ValueError):
            subject_options('1')
        self.assertTrue(subject_options(1))

    @patch('web_v1_dropdown_catalog.VerifiedPdpCatalog')
    def test_unit_deduplication(self, catalog):
        catalog.return_value.list_pdp.return_value = [
            {'unit_title': 'Welcome'}, {'unit_title': 'Welcome'},
            {'unit_title': 'Animals'}, {'unit_title': ''}]
        self.assertEqual([x['label'] for x in unit_options('dummy', 3, 'ENGLISH')],
                         ['Welcome', 'Animals'])

    @patch('web_v1_dropdown_catalog.VerifiedPdpCatalog')
    def test_pdp_scoped_to_unit(self, catalog):
        catalog.return_value.list_pdp.return_value = [
            {'id': 8, 'pdp_no': 2, 'unit_title': 'Welcome', 'subtopic': 'Greetings'},
            {'id': 9, 'pdp_no': 3, 'unit_title': 'Animals', 'subtopic': 'Pets'}]
        result = pdp_options('dummy', 3, 'ENGLISH', 'Welcome')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['value'], '8')
        self.assertFalse(result[0]['standalone_rph_verified'])


if __name__ == '__main__':
    unittest.main()
