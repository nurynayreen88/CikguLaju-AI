"""Regression for the exact 696-PdP private PI collection and fail-closed delivery."""
import io
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from web import pi_696_private_bundle as pi


class TestPIPremiumPrivateBundle(unittest.TestCase):
    def test_storage_auth_headers_modern_secret_and_legacy_jwt(self):
        """Both key types read PRIVATE ZIPs without treating opaque secrets as JWTs."""
        from hashlib import sha256

        buf = io.BytesIO()
        with ZipFile(buf, "w") as z:
            z.writestr("health.txt", "Private source fixture")
        blob = buf.getvalue()
        spec = {
            "object": "rph-premium/pi-2027/v2/696-word-pdf-bundle.zip",
            "bytes": len(blob),
            "sha256": sha256(blob).hexdigest(),
        }

        class Response(io.BytesIO):
            status = 200

        for key, expected_bearer in (
            ("sb_secret_" + "x" * 40, False),
            ("eyJ" + "y" * 55, True),
        ):
            with self.subTest(key_type="modern" if not expected_bearer else "legacy"):
                requests = []

                def fake_urlopen(request, timeout):
                    requests.append(request)
                    return Response(blob)

                pi._verified_zip.cache_clear()
                try:
                    with patch.dict(pi.ARCHIVES, {"v2": spec}), patch.object(
                        pi, "urlopen", side_effect=fake_urlopen
                    ):
                        z = pi._verified_zip(
                            "https://soxakntcanbycjoygrcx.supabase.co", key, "v2"
                        )
                        self.assertIn("health.txt", z.namelist())
                    headers = {name.lower(): value for name, value in requests[0].header_items()}
                    self.assertEqual(headers["apikey"], key)
                    self.assertEqual(headers["accept"], "application/zip")
                    self.assertEqual("authorization" in headers, expected_bearer)
                    if expected_bearer:
                        self.assertEqual(headers["authorization"], "Bearer " + key)
                finally:
                    pi._verified_zip.cache_clear()

    def test_publishable_key_cannot_access_private_pi_archive(self):
        with self.assertRaises(pi.PrivatePIRPHUnavailable):
            pi._settings({
                "supabase_url": "https://soxakntcanbycjoygrcx.supabase.co",
                "supabase_key": "sb_publishable_" + "x" * 40,
            })

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
        # PDF serializers randomize /ID on each call; compare source content, not bytes.
        self.assertEqual(len(source), 1)
        self.assertEqual(source[0].get_text(), "")
        parsed = fitz.open(stream=amended, filetype="pdf")
        rendered = parsed[0].get_text()
        for field in ("4 Bestari", "2027-01-11", "08:00 - 09:00", "32"):
            self.assertIn(field, rendered)

    def test_roman_teacher_details_remain_left_to_right_in_jawi_word(self):
        for value in ("4 Bestari", "2027-01-11", "08:00 - 09:00", "32",
                      "30 murid mencapai objektif."):
            self.assertEqual(pi._rtl_safe_value(value), "\u200e" + value + "\u200e")
        self.assertEqual(pi._rtl_safe_value("موريد برايسي"), "موريد برايسي")

    def test_word_fields_use_directional_isolation_without_editing_lesson(self):
        from docx import Document
        base = Document()
        first = base.add_table(rows=1, cols=2)
        first.cell(0, 0).text = "Original RPH content"
        teacher_cell = first.cell(0, 1)
        teacher_cell.paragraphs[0].text = "کلس : "
        for label in ("تاريخ : ", "ماس : ", "بيلڠن موريد : "):
            teacher_cell.add_paragraph(label)
        last = base.add_table(rows=3, cols=2)
        last.cell(2, 0).text = "رفليكسي (مانوال)"
        original = io.BytesIO()
        base.save(original)
        personal = pi._personalize_word(original.getvalue(), {
            "class": "4 Bestari", "date": "2027-01-11",
            "time": "08:00 - 09:00", "students": "32",
            "reflection": "30 murid mencapai objektif.",
        })
        self.assertEqual(Document(io.BytesIO(original.getvalue())).tables[0].cell(0,0).text,
                         "Original RPH content")
        changed = Document(io.BytesIO(personal))
        self.assertEqual(changed.tables[0].cell(0, 0).text, "Original RPH content")
        for paragraph, expected in zip(changed.tables[0].cell(0, 1).paragraphs,
                                       ("4 Bestari", "2027-01-11", "08:00 - 09:00", "32")):
            self.assertIn("\u200e" + expected + "\u200e", paragraph.text)
        self.assertIn("\u200e30 murid mencapai objektif.\u200e",
                      changed.tables[-1].cell(2, 1).text)

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
