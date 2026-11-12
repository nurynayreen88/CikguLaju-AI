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
    def test_source_only_verified_year2_to_4(self):
        for year, lesson in ((2,2),(3,8),(4,30)):
            with self.subTest(year=year):
                source=_material(year,lesson)
                self.assertIsNotNone(source)
                self.assertTrue(source["path"].is_file())
                data=_extract(source)
                self.assertTrue(data.startswith(b"%PDF-"))
                self.assertEqual(len(PdfReader(BytesIO(data)).pages),
                                 source["last"]-source["first"]+1)
                self.assertLess(len(data),8*1024*1024)
        self.assertIsNone(_material(5,2))
        self.assertIsNone(_material(3,1))
        self.assertIsNone(_material(4,999))

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



class StudentBookYear4Materials(unittest.TestCase):
    def test_complete_main_page_tokens_not_only_legacy_first_page(self):
        from web.telegram_english_workbook_api_20261106 import (
            _verified_y4_student_main_pages,
        )
        self.assertEqual(_verified_y4_student_main_pages("15, 16"), [15, 16])
        self.assertEqual(_verified_y4_student_main_pages("73, 74–75"), [73, 74, 75])
        self.assertEqual(_verified_y4_student_main_pages("20-21"), [20, 21])
        self.assertEqual(_verified_y4_student_main_pages("110"), [110])
        for invalid in (
            "110–133", "27, 28, 29, 30, 31", "20, 22", "74, 74",
            "73, 74x", "p.73", "0", "178", "", "2,,3",
        ):
            with self.subTest(invalid=invalid):
                self.assertEqual(_verified_y4_student_main_pages(invalid), [])

    def test_real_y4_student_book_chunk_integrity_and_boundaries(self):
        """Read source PDFs from the repository, not synthetic blank pages."""
        from pathlib import Path
        from pypdf import PdfReader
        root = Path(__file__).resolve().parents[1] / "books" / "english"
        for filename, first, last in (
            ("y4_student_001_020.pdf", 1, 20),
            ("y4_student_021_100.pdf", 21, 100),
            ("y4_student_101_177.pdf", 101, 177),
        ):
            with self.subTest(filename=filename):
                source = root / filename
                self.assertTrue(source.is_file())
                reader = PdfReader(str(source), strict=True)
                self.assertFalse(reader.is_encrypted)
                self.assertEqual(len(reader.pages), last - first + 1)
                for page in (reader.pages[0], reader.pages[-1]):
                    self.assertGreater(float(page.mediabox.width), 100)
                    self.assertGreater(float(page.mediabox.height), 100)

    def test_all_81_original_source_mappings_fail_closed_or_extract_exact_pdf_pages(self):
        """Exercise all 81 actual Y4 source map entries, not just sample lessons.

        Verifies the excerpt bytes against the three original repository PDF
        parts. This is source-integrity QA, not visual/academic or copyright
        approval of the printed pages.
        """
        import ast
        from pathlib import Path
        import re
        from types import SimpleNamespace
        from web.telegram_english_workbook_api_20261106 import (
            _student_book_material, _extract_student_book,
            _verified_y4_student_main_pages,
        )

        root = Path(__file__).resolve().parents[1]
        app_source = (root / "app.py").read_text(encoding="utf-8")
        def literal_map(name):
            match = re.search(
                r"(?ms)^" + re.escape(name) + r"\s*=\s*(\{.*?^\})",
                app_source,
            )
            self.assertIsNotNone(match, f"Telegram source {name} missing")
            return ast.literal_eval(match.group(1))

        page_map = literal_map("_Y4_SB_PAGES_V25230")
        main_map = literal_map("_EN34_MAIN_SB_V25231")
        self.assertEqual(len(page_map), 81)
        self.assertTrue(all(type(lesson) is int and 1 <= lesson <= 160
                            for lesson in page_map))
        self.assertEqual(main_map.get((4, 157)), "110")

        valid = {
            lesson: _verified_y4_student_main_pages(
                main_map.get((4, lesson), source)
            )
            for lesson, source in page_map.items()
        }
        self.assertEqual(sum(bool(pages) for pages in valid.values()), 80)
        self.assertEqual([n for n, pages in valid.items() if not pages], [43])
        self.assertEqual(valid[103], [73, 74, 75])
        self.assertEqual(valid[157], [110])

        chunks = [
            (1, 20, "books/english/y4_student_001_020.pdf"),
            (21, 100, "books/english/y4_student_021_100.pdf"),
            (101, 177, "books/english/y4_student_101_177.pdf"),
        ]
        origin = {}
        for first, last, relpath in chunks:
            original = PdfReader(str(root / relpath), strict=True)
            self.assertFalse(original.is_encrypted)
            self.assertEqual(len(original.pages), last - first + 1)
            origin[relpath] = original

        rows = [{"lesson_no": str(n), "unit_name": "original-source"}
                for n in page_map]
        runtime = SimpleNamespace(
            _en97_units=lambda year: (rows, ["original-source"])
                if year == "Tahun 4" else ([], []),
            _en34_verified_sb_pages_v25230=lambda row, year:
                main_map.get((year, int(row["lesson_no"])),
                             page_map.get(int(row["lesson_no"]), "")),
            _book_physical_page_v25237=lambda state, kind, page: page
                if state.get("year") == "Tahun 4" and kind == "textbook" else 0,
            _EN_LOCAL_BOOK_CHUNKS_V25234={(4, "textbook"): chunks},
        )

        checked = 0
        for lesson in sorted(page_map):
            with self.subTest(lesson=lesson):
                material = _student_book_material(runtime, 4, lesson,
                                                  root=root)
                self.assertIsNotNone(material)
                # Legacy app.py lists five unrelated Unit 3 pages for L043;
                # the source-specific API corrects Phonics 3 to SOW p.121.
                # Academic SOW crosswalk for three confirmed legacy mismaps.
                corrections = {43: [121], 103: [73], 157: [110, 111]}
                expected = corrections.get(lesson, valid[lesson])
                self.assertEqual(len(material["parts"]), len(expected))
                if lesson in corrections:
                    self.assertIn("m/s " + (
                        "121" if lesson == 43 else
                        "73" if lesson == 103 else "110–111"
                    ), material["label"])
                self.assertLessEqual(len(expected), 4)
                pdf = _extract_student_book(material)
                returned = PdfReader(BytesIO(pdf), strict=True)
                self.assertEqual(len(returned.pages), len(expected))
                for index, (path, offset) in enumerate(material["parts"]):
                    source_name = str(path.relative_to(root))
                    self.assertIn(source_name, origin)
                    original_page = origin[source_name].pages[offset]
                    self.assertEqual(
                        returned.pages[index].get_contents().get_data(),
                        original_page.get_contents().get_data(),
                    )
                checked += 1
        self.assertEqual(checked, 81)


    def test_main_student_book_pages_use_only_verified_runtime_map(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from types import SimpleNamespace
        from pypdf import PdfWriter
        from web.telegram_english_workbook_api_20261106 import (
            _student_book_material, _extract_student_book,
        )
        with TemporaryDirectory() as folder:
            root = Path(folder)
            book = root / "books" / "english"
            book.mkdir(parents=True)
            path = book / "y4_student_001_020.pdf"
            writer = PdfWriter()
            for _ in range(6):
                writer.add_blank_page(width=200, height=200)
            writer.add_metadata({"/Title": "Verified example " + "x" * 1500})
            with path.open("wb") as handle:
                writer.write(handle)
            runtime = SimpleNamespace(
                _en97_units=lambda year: ([{"lesson_no": 17, "unit_name": "Our World"}], ["Our World"])
                    if year == "Tahun 4" else ([], []),
                _en34_verified_sb_pages_v25230=lambda row, y: "1–2"
                    if row.get("unit_name") == "Our World" else "",
                _v25232_nums=lambda raw: [1, 2],
                _book_physical_page_v25237=lambda state, kind, page:
                    page if state.get("year") == "Tahun 4" and
                            state.get("lesson_no") == 17 and
                            state.get("_en98_selected_staging_row", {}).get("unit_name") == "Our World"
                    else 0,
                _EN_LOCAL_BOOK_CHUNKS_V25234={
                    (4, "textbook"): [(1, 20, "books/english/y4_student_001_020.pdf")]
                },
            )
            material = _student_book_material(runtime, 4, 17, root=root)
            self.assertIsNotNone(material)
            pdf = _extract_student_book(material)
            self.assertEqual(len(PdfReader(BytesIO(pdf)).pages), 2)
            self.assertIsNone(_student_book_material(runtime, 3, 17, root=root))
            self.assertIsNone(_student_book_material(runtime, 4, 161, root=root))
            self.assertIsNone(_student_book_material(runtime, 4, 18, root=root))
            # SOW-specific L043 correction must not whitelist five pages in
            # another Lesson or accept a different unverified source range.
            runtime._en34_verified_sb_pages_v25230 = lambda row, y: (
                "27, 28, 29, 30, 31"
            )
            self.assertIsNone(_student_book_material(runtime, 4, 17, root=root))
            runtime._en34_verified_sb_pages_v25230 = lambda row, y: "1–2"
            # A page mapping that includes a whole resource range is rejected.
            runtime._en34_verified_sb_pages_v25230 = lambda row, y: "1–24"
            self.assertIsNone(_student_book_material(runtime, 4, 17, root=root))
            runtime._en34_verified_sb_pages_v25230 = lambda row, y: "1–2"
            app = Flask(__name__ + "sb")
            app.register_blueprint(create_english_workbook_blueprint(runtime))
            client = app.test_client()
            params = {"year": "4", "lesson": "17"}
            with patch.dict(os.environ, {
                "CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1",
                "CIKGULAJU_AUTHORITATIVE_API_TOKEN": "z" * 40,
            }), patch(
                "web.telegram_english_workbook_api_20261106._student_book_material",
                side_effect=lambda rt, y, n: _student_book_material(rt, y, n, root=root),
            ), patch(
                "web.telegram_english_workbook_api_20261106._material",
                side_effect=RuntimeError("Workbook source deliberately unavailable"),
            ):
                # Student Book must never inspect or depend on Workbook sources.
                self.assertEqual(client.get(
                    "/internal/rph/v1/english-extras/student-book",
                    query_string=params).status_code, 401)
                headers = {"Authorization": "Bearer " + "z" * 40}
                found = client.get("/internal/rph/v1/english-extras/student-book",
                                   query_string=params, headers=headers)
                self.assertEqual(found.status_code, 200)
                self.assertEqual(found.json["type"], "student_book")
                pdf_response = client.get(
                    "/internal/rph/v1/english-extras/student-book.pdf",
                    query_string=params, headers=headers)
                self.assertEqual(pdf_response.status_code, 200)
                self.assertEqual(pdf_response.mimetype, "application/pdf")
                self.assertEqual(pdf_response.headers["Cache-Control"], "private, no-store")
                denied = client.get(
                    "/internal/rph/v1/english-extras/student-book",
                    query_string={"year":"3", "lesson":"17"}, headers=headers)
                self.assertEqual(denied.status_code, 404)


    def test_split_pdf_boundary_is_exact_and_ambiguous_sources_fail_closed(self):
        """m/s 20–21 must use page 20 of part A and page 1 of part B."""
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from types import SimpleNamespace
        from pypdf import PdfWriter
        from web.telegram_english_workbook_api_20261106 import (
            _student_book_material, _extract_student_book,
        )

        with TemporaryDirectory() as folder:
            root = Path(folder)
            book_dir = root / "books" / "english"
            book_dir.mkdir(parents=True)
            for filename, count, width in (
                ("y4_student_001_020.pdf", 20, 200),
                ("y4_student_021_100.pdf", 80, 400),
            ):
                writer = PdfWriter()
                for offset in range(count):
                    writer.add_blank_page(width=width + offset, height=300)
                with (book_dir / filename).open("wb") as fh:
                    writer.write(fh)

            source_row = {"lesson_no": 157, "unit_name": "Get Smart"}
            runtime = SimpleNamespace(
                _en97_units=lambda year: ([source_row], ["Get Smart"])
                    if year == "Tahun 4" else ([], []),
                _en34_verified_sb_pages_v25230=lambda row, year: "20–21",
                _v25232_nums=lambda raw: [20, 21],
                _book_physical_page_v25237=lambda state, kind, page: page,
                _EN_LOCAL_BOOK_CHUNKS_V25234={
                    (4, "textbook"): [
                        (1, 20, "books/english/y4_student_001_020.pdf"),
                        (21, 100, "books/english/y4_student_021_100.pdf"),
                    ],
                },
            )
            source = _student_book_material(runtime, 4, 157, root=root)
            self.assertIsNotNone(source)
            pages = PdfReader(BytesIO(_extract_student_book(source))).pages
            self.assertEqual(len(pages), 2)
            self.assertEqual([int(page.mediabox.width) for page in pages],
                             [219, 400])
            self.assertIn("m/s 20–21", source["label"])

            # A duplicated/overlapping manifest cannot select an arbitrary file.
            runtime._EN_LOCAL_BOOK_CHUNKS_V25234[(4, "textbook")].append(
                (20, 30, "books/english/y4_student_021_100.pdf")
            )
            self.assertIsNone(_student_book_material(runtime, 4, 157, root=root))
            runtime._EN_LOCAL_BOOK_CHUNKS_V25234[(4, "textbook")].pop()

            # Disconnected page lists must not export supplementary pages.
            runtime._en34_verified_sb_pages_v25230 = lambda row, y: "20, 22"
            self.assertIsNone(_student_book_material(runtime, 4, 157, root=root))
            runtime._en34_verified_sb_pages_v25230 = lambda row, y: "20–21"
            runtime._book_physical_page_v25237 = lambda state, kind, page: 20.9
            self.assertIsNone(_student_book_material(runtime, 4, 157, root=root))


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
