"""Shared source-native Google RPH bundle adapter never creates fake TG IDs."""
from io import BytesIO
from unittest import TestCase
from unittest.mock import Mock
from zipfile import ZipFile, ZIP_DEFLATED

from web.google_native_rph_bundle import (
    render_native_google_rph_bundle, NativeGoogleRPHNotReady)

TEACHER={"class":"3 Amanah","date":"2026-11-07",
         "time":"08:00 - 09:00","students":"28"}
SELECTED={"source":"existing-standalone-rph",
          "lesson":3,"selection":"e-3-003","unit":"Unit One",
          "year":3,"subject":"ENGLISH"}
HASH="a"*64


def fake_word():
    stream=BytesIO()
    with ZipFile(stream,"w",ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml","<Types/>"*10)
        archive.writestr("word/document.xml","<document>"+("x"*800)+"</document>")
    return stream.getvalue().ljust(520,b" ")


PDF = b"%PDF-1.7\n" + b"X"*650 + b"\n%%EOF\n"


class GoogleNativeBridgeTests(TestCase):
    def setUp(self):
        self.preview=Mock(return_value=SELECTED.copy())
        self.fingerprint=Mock(return_value=HASH)
        self.layout=Mock(return_value={"style":"telegram-native-rph-v1"})
        self.renderer=Mock(side_effect=lambda data,fmt: BytesIO(
            fake_word() if fmt=="word" else PDF))

    def render(self,*,year=3,subject="ENGLISH",approval=None,teacher=None):
        return render_native_google_rph_bundle(
            year,subject,"Unit One","e-3-003",teacher or TEACHER,
            preview_reader=self.preview,
            fingerprint=self.fingerprint,
            layout_builder=self.layout,
            native_renderer=self.renderer,
            y5_approval=approval)

    def test_native_word_and_pdf_exactly_one_bundle(self):
        doc=self.render()
        self.assertEqual(doc["word"],fake_word())
        self.assertEqual(doc["pdf"],PDF)
        self.assertEqual(doc["source_digest"],HASH)
        self.assertEqual(len(doc["document_manifest_sha256"]),64)
        self.assertEqual(self.renderer.call_count,2)
        for call in self.renderer.call_args_list:
            selection=call.args[0]
            self.assertNotIn("telegram_user_id",selection)
            self.assertEqual(selection["teacher"]["class"],"3 Amanah")
            self.assertEqual(selection["source_digest"],HASH)
            self.assertEqual(selection["telegram_layout"]["style"],"telegram-native-rph-v1")

    def test_missing_source_fails_closed(self):
        self.preview.return_value=None
        with self.assertRaises(NativeGoogleRPHNotReady):
            self.render()
        self.renderer.assert_not_called()

    def test_bad_source_fingerprint_never_renders(self):
        self.fingerprint.return_value=None
        with self.assertRaises(NativeGoogleRPHNotReady):
            self.render()
        self.renderer.assert_not_called()

    def test_missing_native_format_cannot_be_debited(self):
        from web.native_telegram_rph_client import NativeRPHUnavailable
        def fail_pdf(selected,fmt):
            if fmt=="pdf":raise NativeRPHUnavailable("generator failed")
            return BytesIO(fake_word())
        self.renderer.side_effect=fail_pdf
        with self.assertRaises(NativeGoogleRPHNotReady):
            self.render()
        self.assertEqual(self.renderer.call_count,2)

    def test_unapproved_english_y5_never_renders(self):
        self.preview.return_value={**SELECTED,"year":5}
        with self.assertRaises(NativeGoogleRPHNotReady):
            self.render(year=5,approval=lambda lesson:False)
        self.renderer.assert_not_called()

    def test_invalid_teacher_and_selection_cannot_render(self):
        for value in (
            {"class":"3A","date":"bad","time":"08:00","students":"10"},
            {"class":"3A","date":"2026-11-07","time":"14:00 - 13:00","students":"10"},
            {"class":"3A","date":"2026-11-07","time":"08:00","students":"201"},
            {"class":"<script>","date":"","time":"","students":""},
        ):
            with self.subTest(value=value),self.assertRaises(ValueError):
                self.render(teacher=value)
        self.renderer.assert_not_called()

    def test_bad_pdf_rejected_without_legacy_fallback(self):
        self.renderer.side_effect=lambda data,fmt: BytesIO(
            fake_word() if fmt=="word" else b"%PDF-1.7"+b"X"*900)
        with self.assertRaises(NativeGoogleRPHNotReady):
            self.render()
        self.assertEqual(self.renderer.call_count,2)


if __name__ == "__main__":
    import unittest
    unittest.main()
