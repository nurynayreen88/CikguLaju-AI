import tempfile
import unittest
from pathlib import Path
from rpt_pj_2027_delivery import (
    STATES, YEARS, FILE_PATTERN, RPTAccessDenied, RPTDocumentUnavailable,
    list_available, resolve_rpt,
)


class TestRPTDelivery(unittest.TestCase):
    def test_catalogue_and_access(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "RPT_PJ_2027_DOCX").mkdir()
            self.assertEqual(list_available(root), [])
            path = root / "RPT_PJ_2027_DOCX" / FILE_PATTERN.format(state="Johor", year=5)
            path.write_bytes(b"docx-placeholder")
            self.assertEqual(len(list_available(root)), 1)
            with self.assertRaises(RPTAccessDenied):
                resolve_rpt(root, negeri="Johor", tahun=5, authorized=False)
            self.assertEqual(resolve_rpt(root, negeri="Johor",
                                         tahun=5, authorized=True), path)
            with self.assertRaises(ValueError):
                resolve_rpt(root, negeri="../Johor", tahun=5, authorized=True)
            with self.assertRaises(ValueError):
                resolve_rpt(root, negeri="Johor", tahun=7, authorized=True)
            for bad_year in (True, False, 4.0, "04", "4.0", None):
                with self.subTest(bad_year=bad_year), self.assertRaises(ValueError):
                    resolve_rpt(root, negeri="Johor", tahun=bad_year, authorized=True)
            with self.assertRaises(RPTDocumentUnavailable):
                resolve_rpt(root, negeri="Kedah", tahun=5, authorized=True)

    def test_symlinked_document_is_never_listed_or_sent(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / "RPT_PJ_2027_DOCX"
            folder.mkdir()
            original = root / "external.docx"
            original.write_bytes(b"private")
            link = folder / FILE_PATTERN.format(state="Johor", year=4)
            link.symlink_to(original)
            self.assertEqual(list_available(root), [])
            with self.assertRaises(RPTDocumentUnavailable):
                resolve_rpt(root, negeri="Johor", tahun=4, authorized=True)

    def test_complete_catalogue(self):
        self.assertEqual(len(STATES) * len(YEARS), 48)
        self.assertEqual(len(set(STATES)), 16)


if __name__ == "__main__":
    unittest.main()
