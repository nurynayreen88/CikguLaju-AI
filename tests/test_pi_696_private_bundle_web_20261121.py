"""Regression for the exact 696-PdP private PI collection and fail-closed delivery."""
import io
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from web import pi_696_private_bundle as pi


class TestPIPremiumPrivateBundle(unittest.TestCase):
    def test_exact_696_choices_include_six_formerly_held(self):
        self.assertEqual(sum(pi.YEARS.values()), 696)
        self.assertEqual({year: len(pi.pdp_options(year)) for year in pi.YEARS}, pi.YEARS)
        self.assertEqual(pi.valid_pdp(2, "35"), 35)
        for n in (6, 14, 18, 60, 117):
            self.assertEqual(pi.valid_pdp(6, str(n)), n)
        for year in pi.YEARS:
            options = pi.pdp_options(year)
            self.assertEqual(len({row["value"] for row in options}), pi.YEARS[year])
            self.assertEqual(options[-1]["pdp_no"], pi.YEARS[year])
            self.assertEqual(pi.unit_option(year)[0]["value"], "RPH Premium 2027")

    def test_jawi_detection(self):
        self.assertTrue(pi._is_jawi("موريد برايسي"))
        self.assertTrue(pi._is_jawi("4 ڤرماتا"))
        self.assertFalse(pi._is_jawi("4 Bestari"))
        self.assertFalse(pi._is_jawi("2027-01-11"))

    def test_pdf_header_can_accept_class_details_without_changing_source(self):
        try:
            import fitz
        except ImportError:
            self.skipTest("PyMuPDF not installed in minimal Web security test")
        source = fitz.open()
        source.new_page(width=595, height=842)
        original = source.tobytes()
        amended = pi._fill_pdf_fields(original, {
            "class": "4 Bestari", "date": "2027-01-11",
            "time": "08:00 - 09:00", "students": "32",
            "reflection": "",
        })
        self.assertEqual(original, source.tobytes())
        parsed = fitz.open(stream=amended, filetype="pdf")
        rendered = parsed[0].get_text()
        for field in ("4 Bestari", "2027-01-11", "08:00 - 09:00", "32"):
            self.assertIn(field, rendered)

    def test_invalid_years_and_lesson_tokens_are_rejected(self):
        for selection in ((1, "1"), (7, "1"), (2, "0"), (2, "113"),
                          (6, "144"), (2, "001"), (2, "-2"), (2, "1/../x")):
            with self.assertRaises(ValueError):
                pi.valid_pdp(*selection)

    def test_document_path_is_exact_by_year_pdp_and_format(self):
        with io.BytesIO() as handle:
            with ZipFile(handle, "w") as z:
                z.writestr("Pendidikan_Islam/Tahun_2/PDF/"
                           "CIKGULAJU_RPH_PI_T2_PDP035.pdf",
                           b"%PDF-" + b"0" * 1100)
            handle.seek(0)
            with ZipFile(handle) as source, \
                 patch.object(pi, "_settings", return_value=("https://test.example", "secret")), \
                 patch.object(pi, "_verified_zip", return_value=source):
                result = pi._file(2, 35, "pdf", {"ignored": True})
                self.assertTrue(result.startswith(b"%PDF-"))
                with self.assertRaises(pi.PrivatePIRPHUnavailable):
                    pi._file(2, 34, "pdf", {"ignored": True})

    def test_never_access_archive_for_bad_pdp(self):
        with patch.object(pi, "_file") as file:
            with self.assertRaises(ValueError):
                pi.request_private_document(6, 144, "word", {}, {})
            file.assert_not_called()

    def test_blank_metadata_returns_source_bytes_without_reflow(self):
        with patch.object(pi, "_file", return_value=b"%PDF-" + b"0" * 1200):
            stream = pi.request_private_document(6, 117, "pdf", {
                "class": "", "date": "", "time": "",
                "students": "", "reflection": "",
            }, {})
            self.assertTrue(stream.getvalue().startswith(b"%PDF-"))


if __name__ == "__main__":
    unittest.main()
