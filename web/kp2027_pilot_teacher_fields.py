"""Safely personalize an approved KP2027 RPH without changing its lesson content.

The original Word/PDF is always checked against the private source manifest by
the calling route *before* this module runs. This module only fills empty
header fields and, when explicitly requested, the reflection box. Errors fail
closed before quota is charged.
"""
from __future__ import annotations

from datetime import date
from io import BytesIO
import re


class TeacherFieldError(ValueError):
    """Teacher fields or a document's reserved field layout are invalid."""


EXTRA_FIELDS = frozenset({
    "teacher_class", "teacher_date", "teacher_start", "teacher_end",
    "teacher_students", "reflection_mode", "reflection",
})


def parse_teacher_fields(payload):
    if not isinstance(payload, dict):
        raise TeacherFieldError("Maklumat RPH tidak sah.")
    if set(payload) - EXTRA_FIELDS:
        raise TeacherFieldError("Medan RPH tidak dikenali.")
    values = {}
    for key in EXTRA_FIELDS:
        raw = payload.get(key, "")
        if not isinstance(raw, str):
            raise TeacherFieldError("Format maklumat guru tidak sah.")
        if any(ord(ch) < 32 and ch not in "\n\r" for ch in raw):
            raise TeacherFieldError("Maklumat guru mengandungi aksara kawalan.")
        values[key] = raw.strip()
    cls = values["teacher_class"]
    if len(cls) > 40 or "\n" in cls or "\r" in cls:
        raise TeacherFieldError("Nama kelas tidak boleh melebihi 40 aksara.")
    raw_date = values["teacher_date"]
    if raw_date:
        if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", raw_date):
            raise TeacherFieldError("Tarikh PdP mesti menggunakan format YYYY-MM-DD.")
        try:
            date.fromisoformat(raw_date)
        except ValueError as exc:
            raise TeacherFieldError("Tarikh PdP tidak sah.") from exc
    start, end = values["teacher_start"], values["teacher_end"]
    if bool(start) != bool(end):
        raise TeacherFieldError("Isi kedua-dua waktu mula dan tamat.")
    if start:
        if any(not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", t) for t in (start, end)) or start >= end:
            raise TeacherFieldError("Sila semak waktu mula dan tamat PdP.")
    count = values["teacher_students"]
    if count and (not re.fullmatch(r"[1-9]\d{0,2}", count) or int(count) > 200):
        raise TeacherFieldError("Bilangan murid mesti antara 1 hingga 200.")
    mode = values["reflection_mode"] or "auto"
    if mode not in ("auto", "manual"):
        raise TeacherFieldError("Pilihan refleksi tidak sah.")
    reflection = values["reflection"]
    if mode == "manual":
        if not reflection or len(reflection) > 500 or len(reflection.splitlines()) > 6:
            raise TeacherFieldError("Refleksi manual mesti diisi, maksimum 500 aksara dan 6 baris.")
    elif reflection:
        raise TeacherFieldError("Refleksi manual hanya untuk pilihan Manual.")
    return {
        "Kelas:": cls,
        "Tarikh:": date.fromisoformat(raw_date).strftime("%d/%m/%Y") if raw_date else "",
        "Masa:": f"{start} - {end}" if start else "",
        "Bil. Murid:": count,
        "_reflection": reflection if mode == "manual" else "",
    }


def _word_personalize(original, fields):
    from docx import Document
    from docx.shared import Pt

    document = Document(BytesIO(original))
    if not document.tables or len(document.tables[0].rows) != 1 or len(document.tables[0].columns) < 2:
        raise TeacherFieldError("Ruang maklumat RPH Word tidak sepadan dengan templat KP2027.")
    header = document.tables[0].cell(0, 1)
    if "Maklumat PdP" not in header.text:
        raise TeacherFieldError("Kotak maklumat PdP tidak ditemukan.")
    found = set()
    for paragraph in header.paragraphs:
        label = paragraph.text.strip()
        if label in ("Kelas:", "Tarikh:", "Masa:", "Bil. Murid:"):
            found.add(label)
            if fields[label]:
                run = paragraph.add_run(" " + fields[label])
                run.font.size = Pt(8)
    if len(found) != 4:
        raise TeacherFieldError("Kotak kelas, tarikh, masa atau bilangan murid tidak lengkap.")
    if fields["_reflection"]:
        reflection_rows = [
            row for table in document.tables for row in table.rows
            if len(row.cells) >= 2 and "Refleksi" in row.cells[0].text
        ]
        if len(reflection_rows) != 1:
            raise TeacherFieldError("Kotak refleksi Word tidak ditemukan.")
        reflection_rows[0].cells[1].text = fields["_reflection"]
    result = BytesIO()
    document.save(result)
    return result.getvalue()


def _pdf_personalize(original, fields):
    import fitz

    try:
        document = fitz.open(stream=original, filetype="pdf")
        if document.page_count != 1:
            raise TeacherFieldError("RPH PDF KP2027 asal bukan satu halaman.")
        page = document[0]
        for label in ("Kelas:", "Tarikh:", "Masa:", "Bil. Murid:"):
            value = fields[label]
            if not value:
                continue
            try:
                value.encode("latin-1")
            except UnicodeEncodeError as exc:
                raise TeacherFieldError("Nama kelas mengandungi aksara yang belum disokong dalam PDF.") from exc
            anchors = page.search_for(label)
            if len(anchors) != 1:
                raise TeacherFieldError("Ruangan " + label + " tidak ditemukan dalam PDF.")
            anchor = anchors[0]
            if not 70 <= anchor.y0 <= 180 or not 370 <= anchor.x0 <= 470:
                raise TeacherFieldError("Kedudukan kotak maklumat PdP tidak dijangka.")
            left = anchor.x1 + 5
            width = page.rect.width - 37 - left
            size = 8.3
            while size >= 5.5 and fitz.get_text_length(value, fontname="helv", fontsize=size) > width:
                size -= 0.3
            if size < 5.5:
                raise TeacherFieldError("Nama kelas terlalu panjang untuk ruang PDF; gunakan nama yang lebih ringkas.")
            page.insert_text((left, anchor.y1 - 2), value, fontname="helv", fontsize=size, color=(0, 0, 0))
        if fields["_reflection"]:
            anchors = page.search_for("Refleksi")
            footers = page.search_for("Rujukan")
            if len(anchors) != 1 or len(footers) != 1:
                raise TeacherFieldError("Ruang refleksi PDF tidak ditemukan.")
            top = anchors[0].y0 - 1.0
            bottom = footers[0].y0 - 4
            region = fitz.Rect(155.9, top, page.rect.width - 39, bottom)
            if region.height < 24 or region.height > 110:
                raise TeacherFieldError("Saiz kotak refleksi PDF tidak dijangka.")
            try:
                fields["_reflection"].encode("latin-1")
            except UnicodeEncodeError as exc:
                raise TeacherFieldError("Refleksi mengandungi aksara yang belum disokong dalam PDF.") from exc
            # Check the reflection fits BEFORE replacing any original text.
            fits = False
            for size in (9.0, 8.3, 7.6, 7.0, 6.4):
                scratch = fitz.open()
                scratch_page = scratch.new_page(width=page.rect.width, height=page.rect.height)
                result = scratch_page.insert_textbox(region, fields["_reflection"], fontname="helv",
                                                      fontsize=size, lineheight=1.0)
                scratch.close()
                if result >= 0:
                    fits = True
                    break
            if not fits:
                raise TeacherFieldError("Refleksi terlalu panjang untuk kotak PDF. Ringkaskan atau gunakan Word.")
            page.add_redact_annot(region, fill=(1, 1, 1), cross_out=False)
            page.apply_redactions(images=0, graphics=0, text=0)
            if page.insert_textbox(region, fields["_reflection"], fontname="helv",
                                   fontsize=size, lineheight=1.0) < 0:
                raise TeacherFieldError("Refleksi PDF tidak dapat dimuatkan dengan selamat.")
        data = document.tobytes(garbage=4, deflate=True)
        if not data.startswith(b"%PDF-"):
            raise TeacherFieldError("Dokumen PDF peribadi tidak dapat disahkan.")
        return data
    finally:
        try:
            document.close()
        except UnboundLocalError:
            pass


def personalize_approved_rph(original, fmt, payload):
    """Return immutable original when fields empty; otherwise a customized copy."""
    fields = parse_teacher_fields(payload)
    if not any(fields.values()):
        return original
    try:
        if fmt == "word":
            return _word_personalize(original, fields)
        if fmt == "pdf":
            return _pdf_personalize(original, fields)
    except TeacherFieldError:
        raise
    except Exception as exc:
        raise TeacherFieldError("Maklumat PdP tidak dapat diserap ke fail RPH asal.") from exc
    raise TeacherFieldError("Format RPH belum disokong.")
