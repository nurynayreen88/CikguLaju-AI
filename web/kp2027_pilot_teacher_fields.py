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
import unicodedata


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
        "_reflection_mode": mode,
        "_reflection": reflection if mode == "manual" else "",
    }


def _clean_success_criterion(value):
    criterion = " ".join(str(value or "").split()).strip(" .")
    if not 12 <= len(criterion) <= 380 or any(ord(ch) < 32 for ch in criterion):
        raise TeacherFieldError("Kriteria kejayaan RPH tidak dapat disahkan untuk refleksi automatik.")
    return criterion


def _proposed_support_action(criterion):
    """Rule-based, topic-appropriate follow-up; never claim it has occurred."""
    value = criterion.casefold()
    if "deria" in value or ("objek" in value and ("membanding" in value or "ciri" in value)):
        return ("latihan berpandu membandingkan dua objek selamat menggunakan kad ciri dan deria",
                "latihan membandingkan dua objek selamat")
    if any(key in value for key in ("sentuhan", "situasi tidak selamat", "keselamatan", "meminta bantuan")):
        return ("simulasi situasi selamat dan latihan meminta bantuan daripada orang dewasa dipercayai",
                "simulasi keselamatan secara berpandu")
    if any(key in value for key in ("tambah", "tolak", "ikatan nombor", "operasi")):
        return ("latihan berperingkat menggunakan pembilang dan kad operasi serta semakan semula",
                "latihan operasi dengan pembilang")
    if any(key in value for key in ("nombor", "kuantiti", "membilang", "angka")):
        return ("latihan individu menggunakan kad nombor, pembilang dan padanan kuantiti",
                "latihan nombor menggunakan pembilang")
    if any(key in value for key in ("wang", "syiling", "ringgit", "sen")):
        return ("aktiviti padanan nilai menggunakan wang replika dan situasi jual beli mudah",
                "latihan nilai wang menggunakan replika")
    if any(key in value for key in ("piktograf", "data", "maklumat harian")):
        return ("latihan membaca piktograf serta mengumpul dan mengelaskan data mudah",
                "latihan membaca data berpandu")
    if any(key in value for key in ("mengukur", "ukuran", "panjang", "sentimeter")):
        return ("aktiviti mengukur semula objek sebenar dengan alat yang sesuai",
                "amali mengukur objek secara berpandu")
    if any(key in value for key in ("bentuk", "pola")):
        return ("latihan mengelaskan bentuk dan menyusun pola dengan kad dan bahan konkrit",
                "latihan mengelaskan bentuk menggunakan kad")
    if any(key in value for key in ("jam", "waktu", "kalendar", "masa")):
        return ("latihan membaca jam model dan kalendar melalui contoh harian",
                "latihan masa menggunakan jam model")
    if any(key in value for key in ("lagu", "nyanyi", "irama", "muzik", "gerak mengikut")):
        return ("latihan ulangan secara berkumpulan kecil menggunakan contoh irama dan pergerakan",
                "latihan irama dan gerakan berpandu")
    if any(key in value for key in ("melukis", "lukisan", "poster", "kraf", "model", "menghasilkan")):
        return ("tunjuk cara langkah demi langkah menggunakan contoh visual dan bahan maujud",
                "tunjuk cara menggunakan contoh visual")
    if any(key in value for key in ("emosi", "perasaan")):
        return ("aktiviti kad situasi untuk mengenal pasti dan menerangkan emosi secara berpandu",
                "latihan kad situasi emosi")
    if re.search(r"\b(?:anggota|tubuh)\b", value):
        return ("latihan berpandu memadankan nama anggota tubuh pada carta serta menyebutnya semula",
                "padanan nama anggota tubuh menggunakan carta")
    # Match WHOLE words: "menu" is a substring of "menunjukkan" and
    # previously caused incorrect food follow-up for body-parts lessons.
    if re.search(r"\b(?:makanan|hidangan|menu|pemakanan)\b", value):
        return ("latihan mengelaskan gambar makanan dan membina menu mudah berpandu",
                "latihan mengelaskan gambar makanan")
    if any(key in value for key in ("bunyi", "cahaya", "hidupan", "hidup", "keperluan")):
        return ("pemerhatian berstruktur dengan bahan sebenar dan kad pengelasan",
                "aktiviti pemerhatian dan pengelasan")
    return ("bimbingan kumpulan kecil melalui contoh langkah demi langkah dan pentaksiran semula",
            "latihan berpandu dan pentaksiran semula")


def _reflection_candidates(criterion):
    """Auto text: leave both pupil counts blank and propose a criterion-specific action.

    No mastery numbers can be inferred from class size or document metadata.
    Every variant retains both blank fields, the full verified criterion, and
    a follow-up action; compact variants accommodate one-page PDF templates.
    """
    criterion = _clean_success_criterion(criterion)
    action, short_action = _proposed_support_action(criterion)
    # Turn the verified "Murid <kata kerja> ..." into a natural, complete
    # mastery sentence; never assert actual counts or compute them.
    clause = criterion[6:] if criterion.casefold().startswith("murid ") else criterion
    clause = clause[0].lower() + clause[1:]
    return (
        "PdP dilaksanakan mengikut perancangan. ____ orang murid menguasai "
        "kemahiran " + clause + ". "
        "____ orang murid belum menguasai dan akan mengikuti " + action + ".",
        "____ orang murid menguasai kemahiran " + clause + ". "
        "____ orang murid belum menguasai; tindakan: " + short_action + ".",
        "____ orang menguasai kemahiran " + clause + ". "
        "____ orang belum menguasai; tindakan: " + short_action + ".",
    )

def _word_success_criterion(document):
    rows = [
        row for table in document.tables for row in table.rows
        if len(row.cells) >= 2 and " ".join(row.cells[0].text.split()) == "Kriteria Kejayaan"
    ]
    if len(rows) != 1:
        raise TeacherFieldError("Kriteria kejayaan RPH Word tidak ditemukan.")
    return _clean_success_criterion(rows[0].cells[1].text)


def _pdf_success_criterion(page):
    import fitz
    labels = [box for box in page.search_for("Kriteria Kejayaan") if box.x0 < 130]
    next_labels = [box for box in page.search_for("EMK / Nilai") if box.x0 < 130]
    if len(labels) != 1 or len(next_labels) != 1 or not labels[0].y0 < next_labels[0].y0:
        raise TeacherFieldError("Kriteria kejayaan RPH PDF tidak ditemukan.")
    # Start at the criterion row, not 8pt above it. The old clip pulled
    # the last line of Objektif Pembelajaran into the automatic reflection.
    region = fitz.Rect(155.0, labels[0].y0, page.rect.width - 35,
                       next_labels[0].y0 - 1.0)
    if not 15 <= region.height <= 150:
        raise TeacherFieldError("Ruang kriteria kejayaan PDF tidak sepadan dengan templat.")
    return _clean_success_criterion(page.get_text("text", clip=region, sort=True))


def _pdf_safe_reflection(value):
    translation = str.maketrans({
        "–": "-", "—": "-", "−": "-", "’": "'", "‘": "'",
        "“": '"', "”": '"', "•": "-", "×": "x", "≤": "<=", "≥": ">=",
        "…": "...", "\u00a0": " ",
    })
    value = unicodedata.normalize("NFKC", value.translate(translation))
    try:
        value.encode("latin-1")
    except UnicodeEncodeError as exc:
        raise TeacherFieldError("Kriteria kejayaan mengandungi aksara yang belum disokong dalam PDF.") from exc
    return value


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
    reflection_rows = [
        row for table in document.tables for row in table.rows
        if len(row.cells) >= 2 and "Refleksi" in row.cells[0].text
    ]
    if len(reflection_rows) != 1:
        raise TeacherFieldError("Kotak refleksi Word tidak ditemukan.")
    # UI-only mode belongs on the Web form, not the printed RPH.
    # Preserve the label's existing run typography and table geometry.
    label_cell = reflection_rows[0].cells[0]
    if re.fullmatch(r"Refleksi\s*\(\s*Auto(?:matik)?\s*/\s*Manual\s*\)",
                    label_cell.text.strip(), flags=re.IGNORECASE):
        runs = [run for paragraph in label_cell.paragraphs for run in paragraph.runs]
        if not runs:
            raise TeacherFieldError("Label refleksi Word tidak lengkap.")
        runs[0].text = "Refleksi"
        for run in runs[1:]:
            run.text = ""
    reflection = (
        fields["_reflection"] if fields["_reflection_mode"] == "manual"
        else _reflection_candidates(_word_success_criterion(document))[0]
    )
    reflection_cell = reflection_rows[0].cells[1]
    original_runs = [run for paragraph in reflection_cell.paragraphs for run in paragraph.runs]
    source_font = next((run.font.name for run in original_runs if run.font.name), None)
    source_size = next((run.font.size for run in original_runs if run.font.size), None)
    reflection_cell.text = reflection
    for paragraph in reflection_cell.paragraphs:
        for run in paragraph.runs:
            if source_font:
                run.font.name = source_font
            if source_size:
                run.font.size = source_size
    # Keep the subject, title, curriculum standard and lesson number inside
    # the RPH table, but remove the duplicate KP2027 banner line and footer.
    for paragraph in list(document.paragraphs):
        if paragraph.text.strip().startswith("KP2027 • TAHUN 1 •"):
            paragraph._element.getparent().remove(paragraph._element)
    for section in document.sections:
        for paragraph in section.footer.paragraphs:
            if "KP2027 TAHUN 1" in paragraph.text:
                paragraph.text = ""
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
        anchors = [a for a in page.search_for("Refleksi") if a.x0 < 130 and a.y0 > 500]
        if len(anchors) != 1:
            raise TeacherFieldError("Ruang refleksi PDF tidak ditemukan.")
        # Never try to remove just '(Auto / Manual)' from a split line:
        # a broken source label leaves 'Manual)' behind. The entire left
        # label cell is redacted and recreated with its original font.
        # A page may contain a second 'Refleksi' in the original instruction
        # and a second 'Rujukan' in the footer; only the left-column labels
        # around the reserved reflection row are reliable anchors.
        footers = [a for a in page.search_for("Rujukan")
                   if a.x0 < 100 and a.y0 > anchors[0].y1]
        if not footers:
            raise TeacherFieldError("Sempadan ruang refleksi PDF tidak ditemukan.")
        # The reflection label is vertically CENTRED, while the original
        # text can start 10-35pt ABOVE it. Use the full table-cell boundaries
        # so the original reflection is completely erased before inserting
        # one consistently sized replacement. Preserve all table borders.
        horizontal_lines = [
            d["rect"].y0 for d in page.get_drawings()
            if d["type"] == "s"
            and abs(d["rect"].y0 - d["rect"].y1) < 1
            and d["rect"].x0 < 50
            and d["rect"].x1 > page.rect.width - 65
        ]
        footer_top = min(a.y0 for a in footers)
        previous_borders = [
            y for y in horizontal_lines if anchors[0].y0 - 110 < y < anchors[0].y0
        ]
        following_borders = [
            y for y in horizontal_lines if anchors[0].y1 < y < footer_top
        ]
        if previous_borders and following_borders:
            row_top = max(previous_borders)
            row_bottom = min(following_borders)
        else:
            # Legacy source PDFs without drawn borders.
            row_top = anchors[0].y0 - 25.0
            row_bottom = footer_top - 4.0
        top, bottom = row_top + 1.0, row_bottom - 1.0
        region = fitz.Rect(155.0, top, page.rect.width - 39, bottom)
        label_region = fitz.Rect(37.0, top, 153.0, bottom)
        if region.height < 24 or region.height > 110:
            raise TeacherFieldError("Saiz kotak refleksi PDF tidak dijangka.")
        candidates = (
            (fields["_reflection"],)
            if fields["_reflection_mode"] == "manual"
            else _reflection_candidates(_pdf_success_criterion(page))
        )
        from web.kp2027_native_pdf_reflection import (
            native_reflection_plan, append_native_reflection,
        )
        safe_candidates = tuple(_pdf_safe_reflection(sentence) for sentence in candidates)
        try:
            native_stream = native_reflection_plan(
                document, page, safe_candidates, row_top, row_bottom,
            )
        except ValueError as exc:
            if not str(exc).startswith("Refleksi tidak muat pada fon asal 9 pt."):
                raise TeacherFieldError(str(exc)) from exc
            # A fixed source PDF may have too little room or a subset font
            # without all characters. Keep the original font where possible,
            # otherwise use a full 9-pt serif face and, if needed, continuation.
            native_stream = None
            native_overflow = True
        else:
            native_overflow = False

        chosen, size = None, 0.0
        continuation = None
        if native_stream is None:
            # Older PDF templates without embedded Noto Serif still use the
            # verified safe fallback; never replace their label only halfway.
            for sentence in safe_candidates:
                for font_size in ((9.0,) if native_overflow else (9.0, 8.7, 8.3, 8.0, 7.6, 7.0)):
                    scratch = fitz.open()
                    scratch_page = scratch.new_page(
                        width=page.rect.width, height=page.rect.height,
                    )
                    result = scratch_page.insert_textbox(
                        region, sentence, fontname="tiro",
                        fontsize=font_size, lineheight=1.05,
                    )
                    scratch.close()
                    if result >= 0:
                        chosen, size = sentence, font_size
                        break
                if chosen is not None:
                    break
            if chosen is None:
                # Preserve the complete manual reflection or full linked auto
                # reflection, never truncate or invent mastery counts.
                continuation = safe_candidates[0]
                chosen, size = "Refleksi bersambung pada halaman seterusnya.", 9.0
                scratch = fitz.open()
                try:
                    check = scratch.new_page(width=page.rect.width, height=page.rect.height)
                    if check.insert_textbox(region, chosen, fontname="tiro", fontsize=size,
                                            lineheight=1.05) < 0:
                        raise TeacherFieldError("Sempadan kotak refleksi PDF tidak sah.")
                finally:
                    scratch.close()
        page.add_redact_annot(label_region, fill=None, cross_out=False)
        page.add_redact_annot(region, fill=None, cross_out=False)
        # Remove only the redundant KP2027 subtitle and footer (where present).
        # Do not touch the actual subject title, PdP content or DK citation.
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", ()):
                for span in line["spans"]:
                    y0, y1 = span["bbox"][1], span["bbox"][3]
                    if "KP2027" in span["text"] and (y0 < 80 or y0 > 750):
                        page.add_redact_annot(
                            fitz.Rect(25, y0 - 1, page.rect.width - 25, y1 + 1),
                            fill=(1, 1, 1), cross_out=False,
                        )
        page.apply_redactions(images=0, graphics=0, text=0)
        if native_stream is not None:
            try:
                append_native_reflection(document, page, native_stream)
            except ValueError as exc:
                raise TeacherFieldError(str(exc)) from exc
        else:
            page.insert_text(
                (38.0, (row_top + row_bottom) / 2 + 4.7),
                "Refleksi", fontname="tibo", fontsize=9.0,
            )
            if page.insert_textbox(
                region, chosen, fontname="tiro",
                fontsize=size, lineheight=1.05,
            ) < 0:
                raise TeacherFieldError("Refleksi PDF tidak dapat dimuatkan dengan selamat.")
        if continuation is not None:
            # Source content and its original A4 page remain intact.
            extra = document.new_page(width=595.28, height=841.89)
            extra.insert_text((37, 48), "RANCANGAN PENGAJARAN HARIAN", fontname="tibo", fontsize=12)
            extra.draw_rect(fitz.Rect(37, 64, 558, 88), color=(.48,.54,.6), fill=(.93,.95,.97), width=.6)
            extra.insert_text((44, 80), "Refleksi (sambungan)", fontname="tibo", fontsize=9)
            # Full-size text, with a generous A4 area for the validated limit.
            if extra.insert_textbox(fitz.Rect(44, 96, 551, 795), continuation,
                                    fontname="tiro", fontsize=9, lineheight=1.2) < 0:
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
    """Return a personalized copy; automatic reflection uses the real success criterion."""
    fields = parse_teacher_fields(payload)
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
