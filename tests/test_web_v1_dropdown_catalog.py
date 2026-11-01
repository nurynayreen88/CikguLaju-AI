"""Isolated tests for read-only dropdown navigation."""
import sqlite3
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from web_v1_dropdown_catalog import subject_options, available_subject_options, unit_options, pdp_options


class DropdownTests(unittest.TestCase):
    def test_year_validation(self):
        with self.assertRaises(ValueError):
            subject_options(0)
        with self.assertRaises(ValueError):
            subject_options('1')
        self.assertTrue(subject_options(1))

    def test_available_subjects_use_verified_non_superseded_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'catalog.db'
            with sqlite3.connect(db) as conn:
                conn.execute('CREATE TABLE rpt_entries (year_label TEXT, subject TEXT, verified INTEGER, notes TEXT)')
                conn.executemany('INSERT INTO rpt_entries VALUES (?, ?, ?, ?)', [
                    ('Tahun 3', 'Bahasa Inggeris', 1, ''),
                    ('Tahun 3', 'Matematik', 0, ''),
                    ('Tahun 3', 'Sains', 1, 'superseded'),
                    ('Tahun 4', 'Bahasa Melayu', 1, ''),
                ])
            self.assertEqual([x['value'] for x in available_subject_options(db, 3)], ['ENGLISH'])
            self.assertEqual([x['value'] for x in available_subject_options(db, 4)], ['BM'])
            with self.assertRaises(ValueError):
                available_subject_options(db, 0)

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
