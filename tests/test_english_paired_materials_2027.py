from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock, patch

from flask import Flask
from pypdf import PdfReader, PdfWriter

from resources.english.y3.student_book_repaired_source import YEAR3_SB_DRIVE_FILE_ID
from web import english_paired_materials_2027 as materials


def excerpt(keys):
    writer = PdfWriter()
    for key in keys:
        coordinate = key[-1] if isinstance(key, tuple) else key
        writer.add_blank_page(width=100 + coordinate, height=200)
    return materials._pdf_bytes(writer)


def test_two_lesson_aliases_deliver_one_copy_of_each_source():
    runtime = SimpleNamespace(_eng12_rows=Mock(return_value=[]))
    app = Flask(__name__)
    app.register_blueprint(materials.create_blueprint(runtime))
    client = app.test_client()
    base = "/internal/rph/v1/english-paired-materials"
    params = {"year": 2, "lesson": 2, "partner": 3}
    shared = {"id": "one", "reference": "CD2 Track 18"}
    other = {"id": "two", "reference": "CD2 Track 20"}
    workbook = {2: [("book-a", 2), ("book-a", 3)], 3: [("book-a", 3), ("book-b", 4)]}
    with (
        patch.object(materials.integrated, "enabled", return_value=True),
        patch.object(materials, "_book_selection", side_effect=lambda _r, _y, n, **_: (
            {"year": "Tahun 2"}, [58, 59] if n == 2 else [59, 60])),
        patch.object(materials, "_pdf", side_effect=lambda _r, _s, pages: excerpt(pages)),
        patch.object(materials, "_material", side_effect=lambda _y, n, **_: {
            "pages": workbook[n], "label": f"English • Buku Aktiviti m/s {n}"}),
        patch.object(materials, "_extract", side_effect=lambda m: excerpt(m["pages"])),
        patch.object(materials, "_audio_rows", side_effect=lambda _r, _y, n, **_: (
            [shared] if n == 2 else [shared, other])),
        patch.object(materials, "_verified_audio", return_value=b"original-file") as audio,
    ):
        assert client.get(base, query_string=params).status_code == 401
        with patch.object(materials, "_authorization", return_value=True):
            assert client.get(base + "/workbook", query_string={**params, "partner": 4}).status_code == 404
            first = client.get(base, query_string=params)
            second = client.get(base, query_string={"year": 2, "lesson": 3, "partner": 2})
            assert first.json == second.json
            assert first.json["lessons"] == [2, 3]
            assert [item["id"] for item in first.json["items"]] == [
                "student-book", "workbook", "audio-1", "audio-2"]
            assert "002 + 003" in first.json["items"][2]["title"]
            for key, widths in (("student-book", [158, 159, 160]), ("workbook", [102, 103, 104])):
                reply = client.get(base + "/" + key, query_string=params)
                assert reply.status_code == 200
                assert "L002-003" in reply.headers["Content-Disposition"]
                assert [float(p.mediabox.width) for p in PdfReader(BytesIO(reply.data)).pages] == widths
            reply = client.get(base + "/audio-2", query_string=params)
            assert reply.mimetype == "audio/x-ms-wma"
            audio.assert_called_once_with(other, wma=True)
            assert client.get(base + "/audio-3", query_string=params).status_code == 404


def test_missing_materials_and_year4_shared_song():
    track = {"id": "song", "reference": "CD2 Track 21"}
    rt = SimpleNamespace(send=Mock(), send_document=Mock(),
                         _send_document_before_v25277=Mock(return_value={"ok": True}),
                         _telegram_delivery_ok_v25279=Mock(return_value=True))
    with (
        patch.object(materials.integrated, "enabled", return_value=True),
        patch.object(materials, "_book_selection", return_value=None),
        patch.object(materials, "_material", return_value=None),
        patch.object(materials, "_audio_rows", return_value=[track]),
    ):
        materials.telegram_callback(rt, 12, "en27materials:4:98")
        assert rt.send.call_args.args[2] == [[{
            "text": "Audio • Lesson 097 + 098 • CD2 Track 21",
            "callback_data": "en27materials:4:97:audio-1"}]]
        with patch.object(materials, "_verified_audio", return_value=b"recording"):
            result = materials.telegram_callback(rt, 12, "en27materials:4:98:audio-1")
            assert result == {"ok": True}
        rt._send_document_before_v25277.assert_called_once()
        rt.send_document.assert_not_called()


def test_year3_download_includes_verified_workbook_reference_once_per_pair():
    for pair, printed, physical in (((86, 87), 45, 46), ((91, 92), 46, 47), ((102, 103), 53, 53)):
        workbook = materials._workbook(3, pair)
        assert [lesson for lesson, _ in workbook] == list(pair)
        for lesson, reference in workbook:
            assert reference["label"].endswith(f"m/s {printed}")
            assert [(path.name, page) for path, page in reference["pages"]] == [
                ("y3_workbook_001_080.pdf", physical)]
            assert materials._material(3, lesson) is None
        data, mime, _ = materials.download(None, 3, pair, "workbook")
        assert mime == "application/pdf"
        assert len(PdfReader(BytesIO(data), strict=True).pages) == 1


def test_year3_welcome_pairs_share_the_printed_workbook_page():
    for pair, printed in (((1, 2), 2), ((6, 7), 3)):
        workbook = materials._workbook(3, pair)
        assert [lesson for lesson, _ in workbook] == list(pair)
        assert len({tuple(item["pages"]) for _, item in workbook}) == 1
        assert all(item["label"].endswith(f"m/s {printed}") for _, item in workbook)
        data, mime, _ = materials.download(None, 3, pair, "workbook")
        assert mime == "application/pdf"
        assert len(PdfReader(BytesIO(data), strict=True).pages) == 1


def test_paired_year3_uses_sow_references_instead_of_old_page_metadata():
    pairs = [((22, 23), [17]), ((65, 66), [45, 47]), ((81, 82), [55]), ((91, 92), [59])]
    numbers = [number for pair, _ in pairs for number in pair]
    runtime = SimpleNamespace(
        _en97_units=lambda _: ([{"lesson_no": n, "subject": "Bahasa Inggeris"} for n in numbers], []),
        _en_book_source_v25232=Mock(return_value=(YEAR3_SB_DRIVE_FILE_ID, "Student’s Book")),
        _en_book_pages_v25232=Mock(return_value=[15]),
    )
    with patch.object(materials, "_pdf", side_effect=lambda _r, _s, pages: excerpt(pages)):
        for pair, pages in pairs:
            selected = materials._student_book(runtime, 3, pair, {})
            assert [n for n, _ in selected] == list(pair)
            data, mime, _ = materials.download(runtime, 3, pair, "student-book")
            assert mime == "application/pdf"
            assert [float(p.mediabox.width) for p in PdfReader(BytesIO(data)).pages] == [
                100 + number for number in pages]
    assert materials._book_selection(runtime, 3, 22)[1] == [15]
    runtime._en_book_source_v25232.return_value = ("old-edition", "Student’s Book")
    assert materials._student_book(runtime, 3, (81, 82), {}) == []


def test_paired_year4_uses_verified_textbook_pages_from_both_lessons():
    pairs = [((19, 20), [16, 17]), ((33, 34), [27, 118]), ((38, 39), [29]),
             ((65, 66), [49, 120]), ((139, 140), [97, 98])]
    numbers = [number for pair, _ in pairs for number in pair]
    runtime = SimpleNamespace(
        _en97_units=lambda _: ([{"lesson_no": n, "subject": "Bahasa Inggeris"} for n in numbers], []),
        _en34_verified_sb_pages_v25230=Mock(return_value="21"),
        _en_book_pages_v25232=Mock(return_value=[21]),
    )
    with patch.object(materials, "_pdf", side_effect=lambda _r, _s, pages: excerpt(pages)):
        for pair, pages in pairs:
            data, mime, _ = materials.download(runtime, 4, pair, "student-book")
            assert mime == "application/pdf"
            assert [float(p.mediabox.width) for p in PdfReader(BytesIO(data)).pages] == [
                100 + number for number in pages]
    assert materials._book_selection(runtime, 4, 19)[1] == [21]
    assert materials._book_selection(runtime, 4, 39, paired_reference=True) is None


def test_telegram_book_view_when_verified_pdf_is_unavailable():
    rt = SimpleNamespace(send=Mock())
    with (patch.object(materials.integrated, "enabled", return_value=True),
          patch.object(materials, "inventory", return_value=[])):
        for code, ending in (("en27materials:3:2", "rmzft/wwgq/mobile/index.html?pageIndex=3"),
                             ("en27materials:3:7", "rmzft/wwgq/mobile/index.html?pageIndex=4"),
                             ("en27materials:6:89", "hykyg/rrpd/mobile/index.html?pageIndex=75")):
            materials.telegram_callback(rt, 1, code)
            assert rt.send.call_args.args[2][0][0]["url"] == "https://online.anyflip.com/" + ending
    with (patch.object(materials.integrated, "enabled", return_value=True),
          patch.object(materials, "inventory", return_value=[{"id": "student-book", "title": "PDF"}])):
        materials.telegram_callback(rt, 1, "en27materials:6:89")
        assert rt.send.call_args.args[2] == [[{"text": "PDF", "callback_data": "en27materials:6:88:student-book"}]]
