from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock, patch

from flask import Flask
from pypdf import PdfReader, PdfWriter

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
        patch.object(materials, "_material", side_effect=lambda _y, n: {
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
    rt = SimpleNamespace(send=Mock())
    with (
        patch.object(materials.integrated, "enabled", return_value=True),
        patch.object(materials, "_book_selection", return_value=None),
        patch.object(materials, "_material", return_value=None),
        patch.object(materials, "_audio_rows", side_effect=lambda _r, _y, n, **_: [track] if n == 98 else []),
    ):
        materials.telegram_callback(rt, 12, "en27materials:4:98")
        assert rt.send.call_args.args[2] == [[{
            "text": "Audio • Lesson 097 + 098 • CD2 Track 21",
            "callback_data": "en27materials:4:97:audio-1"}]]
