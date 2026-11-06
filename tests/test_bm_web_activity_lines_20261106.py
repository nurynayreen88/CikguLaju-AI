"""BM Web RPH numbering: preserve curriculum content, separate activity steps."""
import unittest
from unittest.mock import Mock
from web.telegram_native_bm_sequence_rph_bridge import (
    _numbered_bm_activity_lines, _content,
)


class BMActivityLineBreakTests(unittest.TestCase):
    def test_multiple_numbered_steps_on_one_line_become_separate_lines(self):
        value = ("Aktiviti Utama: 1. Guru memperdengarkan dialog. "
                 "2. Murid membaca dialog secara berpasangan. "
                 "3. Murid melakonkan dialog.")
        self.assertEqual(
            _numbered_bm_activity_lines(value),
            "Aktiviti Utama:\n1. Guru memperdengarkan dialog.\n"
            "2. Murid membaca dialog secara berpasangan.\n"
            "3. Murid melakonkan dialog.")

    def test_existing_lines_remain_unchanged_and_no_false_standards(self):
        samples = (
            "1. Guru bertanya.\n2. Murid menjawab.\n3. Guru merumuskan.",
            "SK 1.1.1 dan SP 2.1.3. Buku Teks m/s 12–13.",
            "Tahun 2, Masa 08:30. Tarikh 06/11/2026.",
            "1. Guru membimbing murid.",
            "Aktiviti A: 1. Dengar dan tuturkan.",
        )
        for s in samples:
            with self.subTest(text=s):
                self.assertEqual(_numbered_bm_activity_lines(s), s)

    def test_only_sequential_steps_are_split(self):
        sample = "Rujuk m/s 3. Contoh 1. Guru menerangkan. 2. Murid menulis."
        result = _numbered_bm_activity_lines(sample)
        self.assertIn("1. Guru menerangkan.\n2. Murid menulis.", result)
        self.assertEqual(result.count("2. Murid"), 1)

    def test_content_uses_same_native_text_without_rewriting_activities(self):
        native = ("Aktiviti Utama: 1. Baca cerita. 2. Bincang watak. "
                  "3. Tulis ayat.\n" + ("Rujukan Buku Teks m/s 2–3. " * 35))
        runtime = Mock()
        runtime._local_rph_text.return_value = native
        formatted = _content(runtime, {"subject": "Bahasa Melayu"})
        runtime._local_rph_text.assert_called_once_with({"subject": "Bahasa Melayu"})
        self.assertIn("1. Baca cerita.\n2. Bincang watak.\n3. Tulis ayat.", formatted)
        self.assertIn("Buku Teks m/s 2–3", formatted)
        self.assertEqual(formatted.replace("\n", " ").split(), native.split())


if __name__ == "__main__":
    unittest.main()
