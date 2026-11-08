"""Web→Telegram native Science probe is off by default, never touches users."""
from __future__ import annotations
from io import BytesIO
from unittest.mock import patch
from zipfile import ZipFile,ZIP_DEFLATED
import os
import unittest

from tools.web_sains_native_telegram_e2e_smoke_20261108 import (
    FLAG,YEARS,probe,log_when_enabled,
)


def sample_document(fmt):
    if fmt=="pdf":
        return BytesIO(b"%PDF-1.5\n"+b"\x20"*1300+b"\n%%EOF\n")
    binary=BytesIO()
    with ZipFile(binary,"w") as target:
        target.writestr("word/document.xml",
                        b'<?xml version="1.0"?><w:document>'+b"a"*1600+
                        b'</w:document>')
    return BytesIO(binary.getvalue())


class WebNativeScienceNetworkProbe(unittest.TestCase):
    def test_opt_in_off_produces_zero_connections(self):
        with patch.dict(os.environ,{FLAG:"0"}), patch(
                "tools.web_sains_native_telegram_e2e_smoke_20261108.probe",
                side_effect=AssertionError("Do not call when flag OFF")):
            self.assertIsNone(log_when_enabled())

    def test_all_five_exact_native_pdp_http_contract_and_local_zip_check(self):
        seen=[]
        def units(year,subject):
            self.assertEqual(subject,"SCIENCE")
            return [{"value":f"u{year:024x}","label":"Unit 2: Manusia"}]
        def lessons(year,subject,unit):
            self.assertEqual(unit,f"u{year:024x}")
            return [{"value":f"SCI-Y{year}-PDP-001","label":"PdP 1: Sains"}]
        def available(year,subject,unit,lesson):
            self.assertEqual(lesson,f"SCI-Y{year}-PDP-001")
            return True
        def download(selection,fmt):
            self.assertEqual(selection["source"],"telegram-native-pdp-sequence")
            self.assertEqual(selection["teacher"],{
                "class":"","date":"","time":"","students":""})
            self.assertIn(fmt,("word","pdf"))
            seen.append((selection["year"],fmt))
            return sample_document(fmt)
        prefix="tools.web_sains_native_telegram_e2e_smoke_20261108.native."
        with patch(prefix+"list_native_units",side_effect=units),patch(
             prefix+"list_native_lessons",side_effect=lessons),patch(
             prefix+"verified_native_sequence_available",side_effect=available),patch(
             prefix+"request_native_sequence_rph",side_effect=download):
            result=probe()
        self.assertTrue(result["real_network_word_pdf_all_five_years"],result)
        self.assertEqual(len(seen),10)
        self.assertEqual(set(seen),{(year,fmt) for year in YEARS
                                    for fmt in ("word","pdf")})
        self.assertFalse(result["account_or_credit_changed"])
        self.assertFalse(result["authoring_342_release_approved"])
        self.assertEqual(len(result["years"]),5)

    def test_unavailable_telegram_fails_closed_without_secret_in_log(self):
        prefix="tools.web_sains_native_telegram_e2e_smoke_20261108.native."
        with patch(prefix+"list_native_units",side_effect=ValueError("token-secret-not-for-logs")):
            result=probe()
        self.assertFalse(result["real_network_word_pdf_all_five_years"])
        for row in result["years"].values():
            self.assertEqual(row["failed_stage"],"catalog")
            self.assertFalse(row["pdf_ready"])
            self.assertFalse(row["word_ready"])
        self.assertNotIn("token-secret-not-for-logs",str(result))

    def test_bad_document_is_not_marked_ready(self):
        prefix="tools.web_sains_native_telegram_e2e_smoke_20261108.native."
        with patch(prefix+"list_native_units",return_value=[{
                "value":"u"+"a"*24,"label":"Unit 1"}]),patch(
             prefix+"list_native_lessons",return_value=[{
                "value":"SCI-Y2-PDP-001","label":"PdP 1"}]),patch(
             prefix+"verified_native_sequence_available",return_value=True),patch(
             prefix+"request_native_sequence_rph",return_value=BytesIO(b"not a document")):
            result=probe()
        self.assertFalse(result["real_network_word_pdf_all_five_years"])
        self.assertTrue(all(row["failed_stage"]=="download_word"
                            for row in result["years"].values()))


if __name__=="__main__":
    unittest.main()
