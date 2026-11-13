"""Contract tests for read-only English selected-page and verified-track delivery."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from io import BytesIO

from flask import Flask
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, NumberObject
from web.telegram_english_sb_audio_api_20261111 import (
    create_english_book_audio_blueprint, _book_selection, _audio_rows, YEAR2_AUDIO,
    YEAR2_AUDIO_BOOK_EVIDENCE, WMA_HEADER,
)


class FakeRuntime:
    CIKGULAJU_Y4_WRONG_BOOK_AUDIO_HOLD_ACTIVE = True
    CIKGULAJU_Y4_L030_AUDIO_CONFLICT_GUARD_ACTIVE = True
    Y4_AUDIO = {
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

    def _eng12_rows(self, year):
        assert year == "Tahun 2"
        return [{"year_label": year, "subject": "Bahasa Inggeris", "lesson_no": 26,
                 "textbook_title": "Super Minds 1", "textbook_page_start": 70,
                 "textbook_page_end": 70, "audio_status": "VERIFIED_AUDIO",
                 "audio_reference": "CD2-35; CD2-36"}]

    def _en97_units(self, year):
        if year not in ("Tahun 3", "Tahun 4"):
            return [], []
        return [{"lesson_no": n, "unit_name": "Our World"}
                for n in (18, 30, 7, 43, 93, 103, 157)], ["Our World"]

    def _en34_verified_sb_pages_v25230(self, row, year):
        return {18: "15, 16", 30: "110–133", 43: "27, 28, 29, 30, 31",
                103: "73, 74–75", 157: "110"}.get(row["lesson_no"], "")

    def _en_book_pages_v25232(self, state, kind):
        if state["year"] == "Tahun 2":
            return [state["textbook_page_start"]]
        return {18: [15], 30: list(range(110, 134)), 93: [61]}.get(state["lesson_no"], [])

    def _en_book_source_v25232(self, state, kind):
        from resources.english.y3.student_book_repaired_source import YEAR3_SB_DRIVE_FILE_ID
        return YEAR3_SB_DRIVE_FILE_ID, "Repaired Student Book"

    def _en4_audio_rows_v25257(self, state):
        return self.Y4_AUDIO.get(state["lesson_no"], [])

    def _lesson_media_rows_v2407(self, state):
        if state["lesson_no"] != 93:
            return []
        assert state["subject"] == "Bahasa Inggeris" and state["quick_content_v2391"] == "Our World"
        return [{"verified": 1, "media_type": "audio", "storage_provider": "google_drive",
                 "storage_file_id": "test_english_3_track_97", "title": "CD1 Track 97"}]

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
            page = writer.add_blank_page(width=150, height=150)
            page[NameObject("/Rotate")] = NumberObject(0)
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
        self.assertEqual(meta.json["pages"], [15])
        self.assertNotIn("file_id", meta.json)
        pdf = self.client.get("/internal/rph/v1/english-extras/student-book.pdf",
                              headers=self.headers, query_string=params)
        self.assertEqual(pdf.status_code, 200)
        self.assertEqual(pdf.mimetype, "application/pdf")
        self.assertEqual(len(PdfReader(BytesIO(pdf.data)).pages), 1)
        self.assertIn("Student_Book.pdf", pdf.headers["Content-Disposition"])
        self.assertEqual(pdf.headers["Cache-Control"], "private, no-store")

    def test_cutout_span_does_not_publish_entire_book(self):
        self.assertIsNone(_book_selection(self.runtime, 4, 30))
        bad = self.client.get("/internal/rph/v1/english-extras/student-book",
                              headers=self.headers,
                              query_string={"year": "4", "lesson": "30"})
        self.assertEqual(bad.status_code, 404)

    def test_year_four_corrected_sow_pages_match_real_book_excerpts(self):
        folder = self.runtime.path.parents[2] / "books" / "english"
        original = Path(__file__).resolve().parents[1] / "books" / "english"
        chunks = ((21, 100, "y4_student_021_100.pdf"), (101, 177, "y4_student_101_177.pdf"))
        from shutil import copyfile
        for _, _, name in chunks:
            copyfile(original / name, folder / name)
        self.runtime._local_book_chunk_v25234 = lambda state, kind, page: next(
            (str(folder / name), first, last) for first, last, name in chunks
            if first <= page <= last
        )
        for lesson, pages in ((43, [121]), (103, [73]), (157, [110, 111])):
            with self.subTest(lesson=lesson):
                params = {"year": 4, "lesson": lesson}
                prefix = "/internal/rph/v1/english-extras/student-book"
                metadata = self.client.get(prefix, query_string=params, headers=self.headers)
                self.assertEqual(metadata.status_code, 200)
                self.assertEqual(metadata.json["pages"], pages)
                result = self.client.get(prefix + ".pdf", query_string=params, headers=self.headers)
                self.assertEqual(result.status_code, 200)
                excerpts = PdfReader(BytesIO(result.data)).pages
                for excerpt, page in zip(excerpts, pages, strict=True):
                    file, first, _ = self.runtime._local_book_chunk_v25234({}, "textbook", page)
                    expected = PdfReader(file, strict=True).pages[page - first]
                    self.assertEqual(excerpt.get_contents().get_data(),
                                     expected.get_contents().get_data())

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

    def test_year_three_uses_repaired_book_and_original_track(self):
        params = {"year": "3", "lesson": "93"}
        book = self.client.get("/internal/rph/v1/english-extras/student-book",
                               headers=self.headers, query_string=params)
        self.assertEqual(book.json["pages"], [61])
        tracks = self.client.get("/internal/rph/v1/english-extras/audio",
                                 headers=self.headers, query_string=params)
        self.assertEqual(tracks.json["tracks"][0]["reference"], "CD1 Track 97")
        original = self.runtime.path.parent / "repaired.pdf"
        writer = PdfWriter()
        for page in range(1, 136):
            sheet = writer.add_blank_page(width=150 + page, height=150)
            sheet[NameObject("/Rotate")] = NumberObject(0)
        writer.write(original)
        with patch.object(self.runtime, "_drive_pdf_v25232", create=True,
                          return_value=original):
            excerpt = self.client.get("/internal/rph/v1/english-extras/student-book.pdf",
                                      headers=self.headers, query_string=params)
        self.assertEqual(excerpt.status_code, 200)
        result = PdfReader(BytesIO(excerpt.data)).pages
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].mediabox.width, 211)
        self.assertFalse(original.exists())

    def test_year_two_keeps_verified_book_page_and_original_wma(self):
        from shutil import copyfile
        root = Path(__file__).resolve().parents[1]
        name = "y12_student_061_080.pdf"
        file = self.runtime.path.parent / name
        copyfile(root / "books" / "english" / name, file)
        self.runtime._local_book_chunk_v25234 = lambda *_: (str(file), 61, 80)
        params = {"year": 2, "lesson": 26}
        prefix = "/internal/rph/v1/english-extras/"
        listing = self.client.get(prefix + "student-book", query_string=params, headers=self.headers)
        self.assertEqual(listing.json["pages"], [70])
        result = self.client.get(prefix + "student-book.pdf", query_string=params, headers=self.headers)
        actual = PdfReader(BytesIO(result.data)).pages
        self.assertEqual(len(actual), 1)
        expected = PdfReader(file).pages[9]
        self.assertEqual(actual[0].get_contents().get_data(), expected.get_contents().get_data())
        audio = self.client.get(prefix + "audio", query_string=params, headers=self.headers)
        self.assertEqual([t["reference"] for t in audio.json["tracks"]], ["CD2 Track 35", "CD2 Track 36"])
        raw = WMA_HEADER + b"A" * 1600
        source = Mock(status_code=200, headers={"Content-Type": "application/octet-stream"})
        source.iter_content.return_value = [raw]
        with patch("requests.get", return_value=source) as drive:
            data = self.client.get(prefix + "audio.wma", query_string={**params, "track": 2},
                                   headers=self.headers)
            self.assertEqual(data.data, raw)
            self.assertEqual(data.mimetype, "audio/x-ms-wma")
            self.assertTrue(data.headers["Content-Disposition"].endswith('.wma"'))
            self.assertEqual(drive.call_args.kwargs["params"]["id"], YEAR2_AUDIO[26][1]["CD2-36"])
            denied = self.client.get(prefix + "audio.mp3", query_string={**params, "track": 2},
                                     headers=self.headers)
            self.assertEqual(denied.status_code, 404)

    def test_year_two_track_ids_match_telegram_and_conflicts_are_hidden(self):
        from tools.audit_english_y2_l026_telegram_route_from_ast_20261105 import extract
        telegram, _ = extract()
        for _, tracks in YEAR2_AUDIO.values():
            self.assertEqual(tracks, {key: telegram[key] for key in tracks})
        row = self.runtime._eng12_rows("Tahun 2")[0]
        self.assertEqual(_audio_rows(self.runtime, 2, 26,
                                    year2_rows=[{**row, "audio_reference": "CD1-17"}]), [])
        self.assertEqual(_audio_rows(self.runtime, 2, 139,
                                    year2_rows=[{**row, "lesson_no": 139,
                                                 "audio_reference": "CD3-47"}]), [])

    def test_year_two_checked_ranges_and_single_digit_track_labels(self):
        from web.telegram_english_sb_audio_api_20261111 import REF

        source = self.runtime._eng12_rows("Tahun 2")[0]
        for lesson, (pages, tracks) in YEAR2_AUDIO.items():
            if lesson in YEAR2_AUDIO_BOOK_EVIDENCE:
                continue
            with self.subTest(lesson=lesson):
                row = {**source, "lesson_no": lesson, "textbook_page_start": pages[0],
                       "textbook_page_end": pages[1], "audio_reference": "; ".join(tracks)}
                entries = _audio_rows(self.runtime, 2, lesson, year2_rows=[row])
                self.assertEqual([entry["id"] for entry in entries], list(tracks.values()))
                self.assertTrue(all(REF.fullmatch(entry["reference"]) for entry in entries))

        wrong_page = {**source, "lesson_no": 33, "textbook_page_start": 74,
                      "textbook_page_end": 74, "audio_reference": "CD2-45"}
        self.assertEqual(_audio_rows(self.runtime, 2, 33, year2_rows=[wrong_page]), [])
        padded = {**source, "lesson_no": 57, "textbook_page_start": 83,
                  "textbook_page_end": 83, "audio_reference": "CD3-05"}
        self.assertEqual(_audio_rows(self.runtime, 2, 57, year2_rows=[padded])[0]["reference"],
                         "CD3 Track 5")

    def test_year_two_source_checked_audio_replaces_only_exact_legacy_rows(self):
        cases = (
            (96, (96, 96), (96, 96), "CD3-20", (21, 23)),
            (97, (97, 97), (97, 97), "CD3-21", (24, 25)),
            (98, (98, 99), (98, 99), "CD3-27", (26, 27)),
            (106, (99, 99), (99, 99), "CD3-29", (28, 29)),
            (108, (101, 101), (101, 101), "CD3-31", (31,)),
            (136, (110, 111), (110, 111), "CD3-44", (43, 44)),
            (137, (111, 111), (111, 111), "CD3-46", (45, 46)),
            (138, (112, 112), (112, 112), "CD3-48", (47, 48)),
        )
        source = self.runtime._eng12_rows("Tahun 2")[0]
        self.assertEqual(set(YEAR2_AUDIO_BOOK_EVIDENCE), {case[0] for case in cases})
        for lesson, (sb_first, sb_last), (wb_first, wb_last), legacy, tracks in cases:
            with self.subTest(lesson=lesson):
                row = {**source, "lesson_no": lesson,
                       "textbook_page_start": sb_first, "textbook_page_end": sb_last,
                       "workbook_page_start": wb_first, "workbook_page_end": wb_last,
                       "workbook_status": "LINKED_VERIFIED", "audio_reference": legacy}
                items = _audio_rows(self.runtime, 2, lesson, year2_rows=[row])
                self.assertEqual([item["reference"] for item in items],
                                 [f"CD3 Track {number}" for number in tracks])
                for change in ({"audio_reference": "CD3-99"}, {"textbook_page_start": sb_first - 1},
                               {"workbook_page_end": wb_last + 1}, {"workbook_status": "REVIEW_REQUIRED"}):
                    self.assertEqual(_audio_rows(self.runtime, 2, lesson, year2_rows=[{**row, **change}]), [])
                if lesson == 98:
                    self.assertTrue(items[0]["title"].endswith("Student Book pp. 98–99 Activity 1"))
                    self.assertTrue(items[1]["title"].endswith("Workbook p. 98 Activity 1"))

    def test_auth_and_input_guards(self):
        bare = self.client.get("/internal/rph/v1/english-extras/audio",
                               query_string={"year": "4", "lesson": "93"})
        self.assertEqual(bare.status_code, 401)
        for query in ({"year": "2", "lesson": "93"},
                      {"year": "4", "lesson": "93", "extra": "x"},
                      {"year": "4", "lesson": "093"}):
            resp = self.client.get("/internal/rph/v1/english-extras/audio",
                                   headers=self.headers, query_string=query)
            self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()
