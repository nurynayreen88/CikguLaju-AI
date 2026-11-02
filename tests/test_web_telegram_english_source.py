"""Tests for the read-only Telegram English row bridge."""
import unittest
from unittest.mock import patch
from web.telegram_english_source import apply_telegram_english_rows


class TelegramEnglishSourceTests(unittest.TestCase):
    def test_year2_uses_production_adapter(self):
        rows = {'SET INDUKSI': 'Existing'}
        with patch('web.telegram_english_source.apply_y2', return_value={'source': 'y2'}) as adapter:
            self.assertEqual(apply_telegram_english_rows(2, 1, rows), {'source': 'y2'})
            adapter.assert_called_once_with({'year': 'Tahun 2', 'subject': 'English', 'lesson_no': 1}, rows)

    def test_year3_uses_production_adapter(self):
        with patch('web.telegram_english_source.apply_y3', return_value={'source': 'y3'}) as adapter:
            self.assertEqual(apply_telegram_english_rows(3, 160, {}), {'source': 'y3'})
            adapter.assert_called_once()

    def test_year1_does_not_fabricate_rows(self):
        rows = {'ACTIVITY': 'Legacy curriculum'}
        self.assertEqual(apply_telegram_english_rows(1, 1, rows), rows)
        self.assertIsNot(apply_telegram_english_rows(1, 1, rows), rows)

    def test_rejects_invalid_inputs(self):
        for year, lesson in [(2, 0), (2, 161), (True, 1), (7, 1), (2, '1')]:
            with self.assertRaises(ValueError):
                apply_telegram_english_rows(year, lesson, {})
        with self.assertRaises(TypeError):
            apply_telegram_english_rows(2, 1, None)


if __name__ == '__main__':
    unittest.main()
