"""Gather verified materials for the two Lessons in one English RPH."""
from io import BytesIO
import re
from pathlib import Path
from tempfile import TemporaryDirectory

from flask import Blueprint, Response, jsonify, request
from pypdf import PdfReader, PdfWriter

from web import english_integrated_rph_2027 as integrated
from web.telegram_english_sb_audio_api_20261111 import (
    _audio_rows, _book_selection, _pdf, _pdf_bytes, _verified_audio,
)
from web.telegram_english_workbook_api_20261106 import _extract, _material
from web.telegram_verified_rpt_rph_bridge import _authorization

SOURCE = "telegram-english-paired-materials-2027"
PDF_LIMIT = 32 * 1024 * 1024
ASSET = re.compile(r"(?:student-book|workbook|audio-[1-8])")


def verified_pair(year, lesson):
    if not integrated.enabled() or year not in range(2, 7):
        return None
    pair = integrated.pair_numbers(year, lesson)
    return pair if pair and integrated.sources_available(year, pair) else None


def _student_book(runtime, year, pair, options):
    return [(n, selection) for n in pair
            if (selection := _book_selection(runtime, year, n, **options))]


def _workbook(year, pair):
    return [(n, material) for n in pair if (material := _material(year, n, paired_reference=True))]


def _audio(runtime, year, pair, options):
    unique = {}
    for lesson in pair:
        for row in _audio_rows(runtime, year, lesson, **options):
            key = row.get("id") or row["publisher_url"]
            if key not in unique:
                unique[key] = (row, [])
            covered = unique[key][1]
            if lesson not in covered:
                covered.append(lesson)
    return list(unique.values())


def _label(kind, covered, reference=""):
    lessons = " + ".join(f"{n:03d}" for n in covered)
    return f"{kind} • Lesson {lessons}" + (f" • {reference}" if reference else "")


def inventory(runtime, year, pair):
    options = {"year2_rows": runtime._eng12_rows("Tahun 2")} if year == 2 else {}
    items = []
    student = _student_book(runtime, year, pair, options)
    if student:
        pages = dict.fromkeys(page for _, (_, pages) in student for page in pages)
        items.append({"id": "student-book", "title": _label(
            "Student’s Book", [n for n, _ in student], "m/s " + ", ".join(map(str, pages)))})
    workbook = _workbook(year, pair)
    if workbook:
        references = dict.fromkeys(material["label"].split(" • Buku Aktiviti ", 1)[1]
                                   for _, material in workbook)
        items.append({"id": "workbook", "title": _label(
            "Activity Book", [n for n, _ in workbook], ", ".join(references))})
    for i, (row, covered) in enumerate(_audio(runtime, year, pair, options), 1):
        items.append({"id": f"audio-{i}", "title": _label("Audio", covered, row["reference"])})
    return items


def _gather_pdf(selections):
    writer, seen, streams = PdfWriter(), set(), []
    for keys, extract in selections:
        missing = [key for key in keys if key not in seen]
        if not missing:
            continue
        stream = BytesIO(extract(missing))
        streams.append(stream)
        pages = PdfReader(stream, strict=True).pages
        if len(pages) != len(missing):
            raise ValueError("Paired excerpt differs from verified page selection")
        for key, page in zip(missing, pages, strict=True):
            writer.add_page(page)
            seen.add(key)
    return _pdf_bytes(writer, limit=PDF_LIMIT) if seen else None


def download(runtime, year, pair, asset):
    options = {"year2_rows": runtime._eng12_rows("Tahun 2")} if year == 2 and asset != "workbook" else {}
    if asset == "student-book":
        selections = [(pages, lambda keys, state=state: _pdf(runtime, state, keys))
                      for _, (state, pages) in _student_book(runtime, year, pair, options)]
        data = _gather_pdf(selections)
        extension, mime = "pdf", "application/pdf"
    elif asset == "workbook":
        selections = [(material["pages"], lambda keys: _extract({"pages": keys}))
                      for _, material in _workbook(year, pair)]
        data = _gather_pdf(selections)
        extension, mime = "pdf", "application/pdf"
    else:
        audio = _audio(runtime, year, pair, options)
        index = int(asset.removeprefix("audio-"))
        if not 1 <= index <= len(audio):
            return None
        row, _ = audio[index - 1]
        data = _verified_audio(row, wma=year == 2)
        extension, mime = ("wma", "audio/x-ms-wma") if year == 2 else ("mp3", "audio/mpeg")
    if data is None:
        return None
    first, second = pair
    return data, mime, f"CikguLaju_English_Y{year}_L{first:03d}-{second:03d}_{asset}.{extension}"


def create_blueprint(runtime):
    blueprint = Blueprint("english_paired_materials_2027", __name__)

    @blueprint.after_request
    def private(response):
        response.headers["Cache-Control"] = "private, no-store"
        response.headers["Vary"] = "Authorization"
        return response

    @blueprint.get("/internal/rph/v1/english-paired-materials")
    @blueprint.get("/internal/rph/v1/english-paired-materials/<asset>")
    def materials(asset=None):
        if not _authorization():
            return jsonify({"error": "Unauthorized"}), 401
        if (set(request.args) != {"year", "lesson", "partner"}
                or any(len(request.args.getlist(k)) != 1 for k in request.args)
                or not re.fullmatch("[2-6]", request.args["year"])
                or not re.fullmatch("[1-9][0-9]{0,2}", request.args["lesson"])
                or not re.fullmatch("[1-9][0-9]{0,2}", request.args["partner"])
                or (asset is not None and not ASSET.fullmatch(asset))):
            return jsonify({"error": "Invalid paired English selection"}), 404
        year, lesson = int(request.args["year"]), int(request.args["lesson"])
        pair = verified_pair(year, lesson)
        if pair != tuple(sorted((lesson, int(request.args["partner"])))):
            return jsonify({"error": "No verified RPH pair"}), 404
        try:
            if asset is None:
                return jsonify({"source": SOURCE, "year": year, "lessons": pair,
                                "items": inventory(runtime, year, pair)})
            result = download(runtime, year, pair, asset)
            if result is None:
                return jsonify({"error": "Unverified paired material"}), 404
            data, mime, name = result
        except Exception:
            return jsonify({"error": "Original materials unavailable"}), 503
        response = Response(data, mimetype=mime)
        response.headers["Content-Disposition"] = f'attachment; filename="{name}"'
        return response

    return blueprint


def telegram_callback(runtime, cid, code):
    match = re.fullmatch(r"en27materials:([2-6]):([1-9][0-9]{0,2})(?::(student-book|workbook|audio-[1-8]))?", code)
    if not match:
        return runtime.send(cid, "Pilihan bahan gabungan tidak sah.")
    year, lesson, asset = int(match[1]), int(match[2]), match[3]
    pair = verified_pair(year, lesson)
    if pair is None:
        return runtime.send(cid, "Bahan gabungan belum tersedia.")
    try:
        if asset is None:
            items = inventory(runtime, year, pair)
            buttons = [[{"text": item["title"], "callback_data":
                         f"en27materials:{year}:{pair[0]}:{item['id']}"}] for item in items]
            if buttons:
                return runtime.send(cid, _label("Bahan English", pair), buttons)
            return runtime.send(cid, "Bahan sumber untuk pasangan ini belum tersedia.")
        result = download(runtime, year, pair, asset)
        if result:
            data, _, name = result
            with TemporaryDirectory(prefix="english-paired-") as folder:
                path = Path(folder) / name
                path.write_bytes(data)
                # The public sender may settle a pending RPH trial. This is a
                # reference document and must use the pre-RPH delivery path.
                sent = runtime._send_document_before_v25277(
                    cid, str(path), _label("Bahan English", pair))
            if runtime._telegram_delivery_ok_v25279(sent):
                return sent
    except Exception:
        pass
    return runtime.send(cid, "Bahan sumber belum dapat dihantar. Cuba lagi.")
