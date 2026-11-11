"""Contract tests for read-only English selected-page and verified-track delivery."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from io import BytesIO

from flask import Flask
from pypdf import PdfReader, PdfWriter
from web.telegram_english_sb_audio_api_20261111 import (
    create_english_book_audio_blueprint, _verified_pages, _audio_rows,
)


class FakeRuntime:
    CIKGULAJU_Y4_WRONG_BOOK_AUDIO_HOLD_ACTIVE = True
    CIKGULAJU_Y4_L030_AUDIO_CONFLICT_GUARD_ACTIVE = True
    _EN4_AUDIO_ALL_V25259 = {
        93: [{"verified": 1, "audio_reference": "CD2 Track 16",
              "storage_file_id": "1AggUOHCnBT6QLAA47v8W4lH4MjGNo8Bz",
              "title": "English Year 4 • Lesson 93 • CD2 Track 16"}],
        30: [{"verified": 1, "audio_reference": "CD2 Track 29",
              "storage_file_id": "1AggUOHCnBT6QLAA47v8W4lH4MjGNo8Bz",
              "title": "English Year 4 • Lesson 30 • CD2 Track 29"}],
        7: [{"verified": 1, "audio_reference": "CD1 Track 9",
             "storage_file_id": "1FWD8yWIYH8qw0qgXRsjLgpcakl-FV5Jd",
             "title": "English Year 4 • Lesson 7 • CD1 Track 9"}],
    }

    def __init__(self, path):
        self.path = path

    def _en97_units(self, year):
        if year != "Tahun 4":
            return [], []
        return [{"lesson_no": n, "unit_name": "Our World"}
                for n in (18, 30, 7, 93)], ["Our World"]

    def _en34_verified_sb_pages_v25230(self, row, year):
        return ("15, 16" if row["lesson_no"] == 18 else
                "110–133" if row["lesson_no"] == 30 else
                "")

    def _local_book_chunk_v25234(self, state, kind, page):
        if kind != "textbook" or page not in (15, 16):
            return None
        return str(self.path), 14, 16

    def _book_physical_page_v25237(self, state, kind, page):
        return page


class EnglishSourceParityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        folder = root / "books" / "english"
        folder.mkdir(parents=True)
        path = folder / "y4_student_001_020.pdf"
        writer = PdfWriter()
        for _ in range(3):
            writer.add_blank_page(width=150, height=150)
        writer.add_metadata({"/Title": "Mock licensed lesson PDF " + "X" * 2000})
        with path.open("wb") as f:
            writer.write(f)
        self.runtime = FakeRuntime(path)
        app = Flask(__name__)
        app.register_blueprint(create_english_book_audio_blueprint(self.runtime, root=root))
        self.client = app.test_client()
        self.token = "t" * 40
        env = patch.dict(os.environ, {
            "CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN": self.token,
        })
        env.start()
        self.addCleanup(env.stop)
        self.headers = {"Authorization": "Bearer " + self.token}

    def test_student_book_only_verified_selected_pages(self):
        params = {"year": "4", "lesson": "18"}
        meta = self.client.get("/internal/rph/v1/english-extras/student-book",
                               headers=self.headers, query_string=params)
        self.assertEqual(meta.status_code, 200)
        self.assertEqual(meta.json["pages"], [15, 16])
        self.assertNotIn("file_id", meta.json)
        pdf = self.client.get("/internal/rph/v1/english-extras/student-book.pdf",
                              headers=self.headers, query_string=params)
        self.assertEqual(pdf.status_code, 200)
        self.assertEqual(pdf.mimetype, "application/pdf")
        self.assertEqual(len(PdfReader(BytesIO(pdf.data)).pages), 2)
        self.assertIn("Student_Book.pdf", pdf.headers["Content-Disposition"])
        self.assertEqual(pdf.headers["Cache-Control"], "private, no-store")

    def test_cutout_span_does_not_publish_entire_book(self):
        self.assertEqual(_verified_pages(self.runtime, {"lesson_no": 30}), [])
        bad = self.client.get("/internal/rph/v1/english-extras/student-book",
                              headers=self.headers,
                              query_string={"year": "4", "lesson": "30"})
        self.assertEqual(bad.status_code, 404)

    def test_audio_verified_track_without_drive_id_exposure(self):
        r = self.client.get("/internal/rph/v1/english-extras/audio",
                            headers=self.headers,
                            query_string={"year": "4", "lesson": "93"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json["tracks"][0]["reference"], "CD2 Track 16")
        self.assertNotIn("storage_file_id", str(r.json))
        response = Mock(status_code=200, headers={"Content-Type": "audio/mpeg"})
        response.iter_content.return_value = [b"ID3" + b"A" * 2000]
        with patch("requests.get", return_value=response):
            actual = self.client.get(
                "/internal/rph/v1/english-extras/audio.mp3",
                headers=self.headers,
                query_string={"year": "4", "lesson": "93", "track": "1"})
        self.assertEqual(actual.status_code, 200)
        self.assertEqual(actual.mimetype, "audio/mpeg")
        self.assertIn("Track_16.mp3", actual.headers["Content-Disposition"])
        self.assertTrue(response.close.called)

    def test_wrong_book_and_conflicting_audio_stay_hidden(self):
        for number in (7, 30):
            self.assertEqual(_audio_rows(self.runtime, 4, number), [])
            denied = self.client.get("/internal/rph/v1/english-extras/audio",
                                     headers=self.headers,
                                     query_string={"year": "4", "lesson": str(number)})
            self.assertEqual(denied.status_code, 404)
        self.runtime.CIKGULAJU_Y4_WRONG_BOOK_AUDIO_HOLD_ACTIVE = False
        self.assertEqual(_audio_rows(self.runtime, 4, 93), [])

    def test_auth_and_input_guards(self):
        bare = self.client.get("/internal/rph/v1/english-extras/audio",
                               query_string={"year": "4", "lesson": "93"})
        self.assertEqual(bare.status_code, 401)
        for query in ({"year": "3", "lesson": "93"},
                      {"year": "4", "lesson": "93", "extra": "x"},
                      {"year": "4", "lesson": "093"}):
            resp = self.client.get("/internal/rph/v1/english-extras/audio",
                                   headers=self.headers, query_string=query)
            self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()
