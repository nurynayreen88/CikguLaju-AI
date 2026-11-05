"""Web PDF personalization proxy runs with only Flask + standard library."""
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from hashlib import sha256
import json
import unittest

from web.rpt_school_cover import request_telegram_school_rpt
from web.teacher_profile_store import ProfileUnavailable


class FakeResult:
    def __init__(self,data):
        self.status=200
        self.headers={"Content-Type":"application/pdf"}
        self.data=data
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def read(self, size): return self.data[:size]


class FakeOpener:
    def __init__(self):
        self.request=None
    def open(self, request, timeout=0):
        self.request=request
        return FakeResult(b"%PDF-"+b"x"*9000)


class SchoolRptProxyTests(unittest.TestCase):
    def test_uses_telegram_private_pdf_with_exact_web_source_hash(self):
        with TemporaryDirectory() as tmp:
            source=Path(tmp)/"RPT.pdf"
            original=b"%PDF-"+b"source"*2000
            source.write_bytes(original)
            identity={"school":"SK Taman Bunga","teacher":"Cikgu Suria",
                      "state":"Johor","logo":b"\x89PNG\r\n\x1a\n"+b"x"*64}
            transport=FakeOpener()
            with patch.dict("os.environ",{
                    "CIKGULAJU_AUTHORITATIVE_API_URL":"https://cikgulaju-ai.onrender.com",
                    "CIKGULAJU_AUTHORITATIVE_API_TOKEN":"a"*64}):
                file=request_telegram_school_rpt(
                    source,"bahasa_melayu",2,identity,opener=transport)
            self.assertTrue(file.getvalue().startswith(b"%PDF-"))
            sent=json.loads(transport.request.data)
            self.assertEqual(sent["source_sha256"],sha256(original).hexdigest())
            self.assertEqual(sent["school"],"SK Taman Bunga")
            self.assertEqual(sent["subject"],"bahasa_melayu")
            self.assertIn("/internal/rpt/v1/personalize",transport.request.full_url)
            self.assertEqual(source.read_bytes(),original)
            self.assertNotIn(b"SK Taman Bunga",source.read_bytes())

    def test_rejects_unsigned_wrong_year_or_non_pdf_source(self):
        with TemporaryDirectory() as tmp:
            source=Path(tmp)/"RPT.pdf"
            source.write_bytes(b"not pdf"+b"x"*9000)
            with self.assertRaises(ProfileUnavailable):
                request_telegram_school_rpt(source,"english",2027,
                  {"school":"School","state":"","teacher":"","logo":None})
            with self.assertRaises(ProfileUnavailable):
                request_telegram_school_rpt(source,"english",1,
                  {"school":"School","state":"","teacher":"","logo":None})

    def test_web_source_imports_without_pdf_image_packages(self):
        from web.rpt_school_cover import school_identity,for_download
        from web.school_logo_store import normalized_png
        self.assertTrue(callable(school_identity))
        self.assertTrue(callable(for_download))
        self.assertTrue(callable(normalized_png))


if __name__=="__main__":
    unittest.main()
