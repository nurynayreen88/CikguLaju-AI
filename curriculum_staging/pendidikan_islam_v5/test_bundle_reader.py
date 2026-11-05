"""Pendidikan Islam V5 staging reader verification (does not touch prod)."""
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from bundle_reader import PIBundleV5, BundleValidationError

class PIBundleReaderTest(unittest.TestCase):
    def test_live_mode_is_blocked(self):
        with self.assertRaises(PermissionError):
            PIBundleV5('/tmp/nonexistent.zip')

    def test_integration_bundle_optional(self):
        archive = os.environ.get('PI_V5_ARCHIVE')
        if not archive:
            self.skipTest('Set PI_V5_ARCHIVE to run full real bundle test')
        bundle = PIBundleV5(archive,staging=True)
        self.assertEqual(len(bundle.lesson_ids()),696)
        self.assertEqual(sum(1 for key in bundle.lesson_ids() if bundle.record(*key)['optional_tasmi_guide'] is not None),8)
        with self.assertRaises(PermissionError):
            bundle.read_rph(2,35)
        self.assertTrue(bundle.read_rph(2,35,allow_teacher_draft=True).startswith(b'PK'))
        self.assertTrue(bundle.read_optional_tasmi_guide(2,35).startswith(b'%PDF-'))
        self.assertIsNone(bundle.read_optional_tasmi_guide(2,1))
        self.assertEqual(bundle.record(6,141)['source_exception'],'4_surah_juz30_julat_cadangan')

if __name__ == '__main__':
    unittest.main()