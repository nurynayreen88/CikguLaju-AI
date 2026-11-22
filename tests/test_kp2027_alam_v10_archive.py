"""Release gate contract for KP2027 V10: original QA archive cannot go public."""
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from web import kp2027_alam_v10_archive as source


class KP2027V10PrivateSourceTests(unittest.TestCase):
    def test_invalid_lesson_and_format_cannot_be_path_traversal(self):
        for value in (-1, 0, 65, True, "../../etc/passwd", "0", "65", "1.0", " 1", "1/"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                source.lesson_number(value)
        for value in (1, 3, 19, 64, "001", "064"):
            self.assertEqual(source.lesson_number(value), int(value))
        with self.assertRaises(ValueError):
            source.load_approved_document(1, "jpg", config={})

    def test_fail_closed_without_independent_approval_even_with_storage_config(self):
        with patch.object(source, "_read_private_source", side_effect=AssertionError("must not fetch")):
            with self.assertRaises(source.KP2027ArchiveUnavailable):
                source.load_approved_document(3, "pdf", config={}, approved=False)

    def test_bad_host_and_credentials_refused(self):
        bad = [
            {"supabase_url": "http://soxakntcanbycjoygrcx.supabase.co", "supabase_key": "x" * 40},
            {"supabase_url": "https://evil.example", "supabase_key": "x" * 40},
            {"supabase_url": "https://soxakntcanbycjoygrcx.supabase.co.evil.example", "supabase_key": "x" * 40},
            {"supabase_url": "https://soxakntcanbycjoygrcx.supabase.co/path", "supabase_key": "x" * 40},
            {"supabase_url": "https://soxakntcanbycjoygrcx.supabase.co", "supabase_key": "weak"},
        ]
        for config in bad:
            with self.subTest(config=config), self.assertRaises(source.KP2027ArchiveUnavailable):
                source._private_settings(config)

    def test_archive_requires_pinned_bytes_and_sha(self):
        for invalid in (b"", b"not a zip", b"PK\x03\x04" + b"x" * 5000):
            with self.assertRaises(source.KP2027ArchiveUnavailable):
                source.verify_qa_archive(invalid)

    def test_verified_original_archive_is_still_qa_not_ready(self):
        archive_path = os.environ.get("KP2027_V10_QA_ZIP")
        if not archive_path or not Path(archive_path).is_file():
            self.skipTest("Owner's QA file is external to Git and not a release dependency")
        raw = Path(archive_path).read_bytes()
        archive = source.verify_qa_archive(raw)
        self.assertEqual(len(archive.namelist()), 131)
        with patch.object(source, "_read_private_source", return_value=archive):
            with self.assertRaisesRegex(source.KP2027ArchiveUnavailable, "approval absent"):
                source.load_approved_document(3, "pdf", config={}, approved=True)
        damaged = raw[:100] + b"BAD" + raw[103:]
        with self.assertRaises(source.KP2027ArchiveUnavailable):
            source.verify_qa_archive(damaged)


if __name__ == "__main__":
    unittest.main()
