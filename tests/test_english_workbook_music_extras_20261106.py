"""Workbook excerpts and owner-hosted Music source links: authenticated integration."""
import os
import unittest
from io import BytesIO
from unittest.mock import Mock, patch

from flask import Flask
from pypdf import PdfReader
from web.telegram_english_workbook_api_20261106 import (
    _material, _extract, create_english_workbook_blueprint,
)
from web.telegram_provisional_arab_music_api import (
    create_provisional_subjects_blueprint, _unit_rows, _lesson_rows,
)


class EnglishWorkbookMaterials(unittest.TestCase):
    def test_source_only_verified_year2_to_6(self):
        for year, lesson in ((2,2),(3,8),(4,30),(5,29),(6,1)):
            with self.subTest(year=year):
                source=_material(year,lesson)
                self.assertIsNotNone(source)
                self.assertTrue(all(path.is_file() for path, _ in source["pages"]))
                data=_extract(source)
                self.assertTrue(data.startswith(b"%PDF-"))
                self.assertEqual(len(PdfReader(BytesIO(data)).pages),
                                 len(source["pages"]))
                self.assertLess(len(data),8*1024*1024)
        self.assertIsNone(_material(5,16))
        self.assertIsNone(_material(6,16))
        self.assertIsNone(_material(3,1))
        self.assertIsNone(_material(4,999))

    def test_upper_primary_excerpts_match_original_pdf_pages(self):
        for year, lesson, expected in ((5, 29, (18, 19)), (6, 13, (8, 16))):
            with self.subTest(year=year, lesson=lesson):
                source = _material(year, lesson)
                self.assertIsNotNone(source)
                self.assertTrue(source["label"].endswith(", ".join(map(str, expected))))
                excerpt = PdfReader(BytesIO(_extract(source)))
                for actual, (path, index) in zip(excerpt.pages, source["pages"], strict=True):
                    original = PdfReader(path, strict=True).pages[index - 1]
                    self.assertEqual(actual.get_contents().get_data(),
                                     original.get_contents().get_data())

    def test_pdf_route_requires_bearer_and_never_returns_whole_book_part(self):
        app=Flask(__name__)
        app.register_blueprint(create_english_workbook_blueprint())
        client=app.test_client()
        with patch.dict(os.environ, {"CIKGULAJU_WEB_NATIVE_RPH_ENABLED":"1",
                                     "CIKGULAJU_AUTHORITATIVE_API_TOKEN":"z"*40}):
            denied=client.get("/internal/rph/v1/english-extras/workbook",
                              query_string={"year":"2","lesson":"2"})
            self.assertEqual(denied.status_code,401)
            headers={"Authorization":"Bearer "+"z"*40}
            okay=client.get("/internal/rph/v1/english-extras/workbook",
                            query_string={"year":"2","lesson":"2"}, headers=headers)
            self.assertEqual(okay.status_code,200)
            self.assertEqual(okay.json["lesson"],2)
            pdf=client.get("/internal/rph/v1/english-extras/workbook.pdf",
                           query_string={"year":"2","lesson":"2"}, headers=headers)
            self.assertEqual(pdf.status_code,200)
            self.assertEqual(pdf.mimetype,"application/pdf")
            self.assertLessEqual(len(PdfReader(BytesIO(pdf.data)).pages),4)
            self.assertEqual(pdf.headers["Cache-Control"],"private, no-store")
            not_ready=client.get("/internal/rph/v1/english-extras/workbook",
                                 query_string={"year":"2","lesson":"1"}, headers=headers)
            self.assertEqual(not_ready.status_code,404)
            invalid=client.get("/internal/rph/v1/english-extras/workbook",
                               query_string={"year":"2","lesson":"2","extra":"x"},
                               headers=headers)
            self.assertEqual(invalid.status_code,404)


class MusicExternalLinkOnly(unittest.TestCase):
    def test_music_source_links_never_claim_download_or_audio_verification(self):
        runtime=Mock()
        runtime.create_word_file=lambda *args:None
        runtime.create_pdf_file=lambda *args:None
        app=Flask(__name__+"music")
        app.register_blueprint(create_provisional_subjects_blueprint(runtime))
        client=app.test_client()
        unit=_unit_rows(2,"MUZIK")[0]["value"]
        lesson=_lesson_rows(2,"MUZIK",unit)[0]["value"]
        params={"year":"2","subject":"MUZIK","unit":unit,"lesson":lesson}
        with patch.dict(os.environ,{"CIKGULAJU_WEB_NATIVE_RPH_ENABLED":"1",
                                    "CIKGULAJU_AUTHORITATIVE_API_TOKEN":"z"*40}):
            denied=client.get("/internal/rph/v1/other-drafts/audio-links",
                              query_string=params)
            self.assertEqual(denied.status_code,401)
            okay=client.get("/internal/rph/v1/other-drafts/audio-links",
                            query_string=params,headers={"Authorization":"Bearer "+"z"*40})
            self.assertEqual(okay.status_code,200)
            self.assertEqual(okay.json["status"],"DRAF")
            self.assertIs(okay.json["download_available"],False)
            for item in okay.json["links"]:
                self.assertTrue(item["url"].startswith("https://drive.google.com/file/d/"))
                self.assertIn("view?",item["url"])
                self.assertNotIn("download_url",item)
            self.assertNotIn("Content-Disposition",okay.headers)


if __name__=="__main__":
    unittest.main()
