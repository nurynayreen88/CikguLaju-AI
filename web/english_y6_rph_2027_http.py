"""Paid, authenticated Year 6 RPH view and Word export for isolated Web staging.

Shares precisely the same 160 Markdown files and SOW task overlay as Telegram.
Does not mutate the database, debit RPH trial credits or call the bot.
Free account RPH delivery remains closed until a shared quota backend is proven.
"""
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZipFile, ZIP_DEFLATED
from flask import Blueprint, jsonify, request, send_file
from web.english_rpt_2027_http import _account, _has_paid_access
from web.english_y6_standalone_runtime import adapt_rows

FIELDS = (
    ("TAJUK", "Topic"),
    ("STANDARD KANDUNGAN", "Content Standard"),
    ("STANDARD PEMBELAJARAN", "Learning Standard"),
    ("OBJEKTIF PEMBELAJARAN", "Learning Objectives"),
    ("KRITERIA KEJAYAAN", "Success Criteria"),
    ("BAHAN BANTU MENGAJAR", "Teaching and Learning Materials"),
    ("PENTAKSIRAN", "PBD / Assessment"),
    ("SET INDUKSI", "Set Induction (5 min)"),
    ("AKTIVITI UTAMA", "Main Activities and Reinforcement (51 min)"),
    ("PENUTUP", "Closure (4 min)"),
    ("PEMULIHAN / PENGAYAAN", "Differentiation and Follow-up"),
    ("REFLEKSI", "Reflection"),
)


def source_rows(lesson):
    if type(lesson) is not int or not 1 <= lesson <= 160:
        return None
    initial = {"TAJUK": "English Year 6 — Lesson %03d" % lesson}
    selection = {"subject": "English", "year": "Tahun 6", "lesson_no": lesson}
    rows = adapt_rows(selection, initial)
    if rows is initial or not rows.get("AKTIVITI UTAMA"):
        return None
    return rows


def _docx_paragraph(text, *, bold=False):
    text = str(text or "")
    parts = []
    style = "<w:rPr><w:rFonts w:ascii='Aptos' w:hAnsi='Aptos'/><w:sz w:val='18'/>" + ("<w:b/>" if bold else "") + "</w:rPr>"
    for chunk in text.split("\n"):
        content = "<w:t xml:space='preserve'>" + escape(chunk) + "</w:t>"
        parts.append("<w:p><w:pPr><w:spacing w:after='60' w:line='200' w:lineRule='auto'/></w:pPr><w:r>" + style + content + "</w:r></w:p>")
    return "".join(parts)


def make_docx(lesson, rows):
    body = [_docx_paragraph("CIKGULAJU AI — RANCANGAN PENGAJARAN HARIAN", bold=True),
            _docx_paragraph("ENGLISH YEAR 6 | RPT 2027 | LESSON %03d | 60 MINUTES" % lesson, bold=True),
            _docx_paragraph("Class: __________________  Date: ______________  Time: ___________")]
    for key, label in FIELDS:
        value = rows.get(key) or "—"
        body.append(_docx_paragraph(label + ":", bold=True))
        body.append(_docx_paragraph(value))
    body.append("<w:sectPr><w:pgSz w:w='11906' w:h='16838'/><w:pgMar w:top='550' w:right='650' w:bottom='550' w:left='650'/></w:sectPr>")
    document = "<?xml version='1.0' encoding='UTF-8' standalone='yes'?><w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'><w:body>" + "".join(body) + "</w:body></w:document>"
    manifest = "<?xml version='1.0' encoding='UTF-8' standalone='yes'?><Types xmlns='http://schemas.openxmlformats.org/package/2006/content-types'><Default Extension='rels' ContentType='application/vnd.openxmlformats-package.relationships+xml'/><Default Extension='xml' ContentType='application/xml'/><Override PartName='/word/document.xml' ContentType='application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml'/></Types>"
    rels = "<?xml version='1.0' encoding='UTF-8' standalone='yes'?><Relationships xmlns='http://schemas.openxmlformats.org/package/2006/relationships'><Relationship Id='rId1' Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument' Target='word/document.xml'/></Relationships>"
    buf = BytesIO()
    with ZipFile(buf, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", manifest)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("word/document.xml", document)
    buf.seek(0)
    return buf


def create_blueprint():
    bp = Blueprint("web_english_y6_rph_2027", __name__)

    @bp.after_request
    def private_response(response):
        response.headers["Cache-Control"] = "no-store, private"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Vary"] = "Cookie"
        return response

    def authorize():
        account, error = _account()
        if error is not None:
            return error
        if not _has_paid_access(account):
            return jsonify({"error": "RPH Year 6 Web is available to active subscribers and confirmed Rakan Pembangun only; free RPH quota is not connected here"}), 403
        return None

    @bp.get("/api/web/english/year6/rph/<int:lesson>")
    def preview(lesson):
        error = authorize()
        if error is not None:
            return error
        rows = source_rows(lesson)
        if rows is None:
            return jsonify({"error": "Year 6 lesson not available or mapping not verified"}), 404
        return jsonify({"lesson": lesson, "year": 6, "subject": "English",
                        "duration_minutes": 60, "fields": [
                            {"label": label, "value": rows.get(key) or "—"}
                            for key, label in FIELDS],
                        "source": "telegram-year6-2027-rph",
                        "teacher_selection": "Teacher-selected" in rows.get("STANDARD PEMBELAJARAN", ""),
                        "notice": "Review individual textbook and audio references before classroom use."})

    @bp.get("/api/web/english/year6/rph/<int:lesson>.docx")
    def word_download(lesson):
        error = authorize()
        if error is not None:
            return error
        rows = source_rows(lesson)
        if rows is None:
            return jsonify({"error": "Year 6 lesson not available or mapping not verified"}), 404
        return send_file(make_docx(lesson, rows), mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                         as_attachment=True, download_name="CIKGULAJU_ENGLISH_Y6_RPH_%03d_2027.docx" % lesson,
                         conditional=False)

    return bp
