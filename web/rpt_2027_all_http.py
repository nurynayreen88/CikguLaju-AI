"""Authenticated, read-only RPT 2027 catalog for all primary subjects.

Each year is backed by an exact local PDF only. Never infer availability from
another year's RPT, another subject, CSV/HTML drafts or an unverified path.
Files are copied from the Telegram repository to Web staging by Git blob SHA.
The login, subscription and trial balances remain managed by the existing
Supabase account source; no writes or credit deductions occur here.
"""
from pathlib import Path
from flask import Blueprint, jsonify, send_file

from web.english_rpt_2027_http import _account, _has_paid_access

ROOT = Path(__file__).resolve().parents[1] / "rpt_2027"
YEARS = tuple(range(2, 7))
# Label, relative folder, exact PDF filename template, published status.
SUBJECTS = {
    "english": ("English", "english", "RPT_ENGLISH_TAHUN_%d_2027_UNTUK_GURU.pdf", "TERSEDIA"),
    "bahasa_melayu": ("Bahasa Melayu", "bahasa_melayu", "RPT_Bahasa_Melayu_Tahun_%d_2027_DRAF.pdf", "DRAF"),
    "matematik": ("Matematik", "matematik", "RPT_Matematik_Tahun_%d_2027_v28_SEMENTARA.pdf", "SEMENTARA"),
    "sains": ("Sains", None, None, "BELUM TERSEDIA"),
    "pendidikan_islam": ("Pendidikan Islam", "pendidikan_islam", "RPT_Pendidikan_Islam_Tahun_%d_2027_CikguLaju.pdf", "TERSEDIA"),
    "pjpk": ("Pendidikan Jasmani dan Pendidikan Kesihatan (PJPK)", "pjpk", "RPT_PJPK_Tahun_%d_2027_DRAF.pdf", "DRAF"),
    "pendidikan_moral": ("Pendidikan Moral", "pendidikan_moral", "RPT_Pendidikan_Moral_Tahun_%d_2027_DRAF_WEB.pdf", "DRAF"),
    "psv": ("Pendidikan Seni Visual (PSV)", "psv", "RPT_PSV_Tahun_%d_2027_DRAF_WEB.pdf", "DRAF"),
}


def pdf_path(subject, year, *, root=ROOT):
    if type(year) is not int or year not in YEARS or subject not in SUBJECTS:
        raise ValueError("Unsupported RPT selection")
    _label, folder, template, _status = SUBJECTS[subject]
    if not folder or not template:
        return None
    return Path(root) / folder / (template % year)


def pdf_ready(subject, year, *, root=ROOT):
    try:
        path = pdf_path(subject, year, root=root)
        if path is None or path.is_symlink() or not path.is_file() or path.stat().st_size < 8_000:
            return False
        with path.open("rb") as file:
            return file.read(5) == b"%PDF-"
    except (ValueError, OSError):
        return False


def create_all_rpt_blueprint(*, root=ROOT):
    bp = Blueprint("all_rpt_2027_pdf", __name__)

    @bp.after_request
    def private_cache(response):
        response.headers["Cache-Control"] = "no-store, private"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @bp.get("/api/rpt/2027/catalog")
    def catalog():
        account, error = _account()
        if error is not None:
            return error
        allowed = _has_paid_access(account)
        subjects = []
        for code, (label, _folder, _template, status) in SUBJECTS.items():
            entries = []
            for year in YEARS:
                ready = pdf_ready(code, year, root=root)
                entries.append({
                    "year": year,
                    "pdf_ready": ready,
                    "status": status if ready else "PDF BELUM TERSEDIA",
                    "download_enabled": bool(allowed and ready),
                })
            subjects.append({"code": code, "label": label, "years": entries})
        return jsonify({
            "year": 2027,
            "format": "pdf",
            "allowed": allowed,
            "subjects": subjects,
            "note": "Akses RPT khusus untuk Rakan Pembangun atau langganan aktif. DRAF/SEMENTARA bukan FINAL READY.",
        })

    @bp.get("/api/rpt/2027/all/<subject>/<int:year>.pdf")
    def download(subject, year):
        account, error = _account()
        if error is not None:
            return error
        if subject not in SUBJECTS or year not in YEARS:
            return jsonify({"error": "Pilihan RPT tidak sah"}), 404
        if not _has_paid_access(account):
            return jsonify({"error": "Akses RPT memerlukan Rakan Pembangun atau langganan aktif"}), 403
        if not pdf_ready(subject, year, root=root):
            return jsonify({"error": "PDF RPT subjek/tahun ini belum tersedia dan belum disahkan"}), 503
        path = pdf_path(subject, year, root=root)
        from web.rpt_school_cover import for_download
        from web.teacher_profile_store import ProfileUnavailable
        try:
            document = for_download(account, path, subject, year)
        except ProfileUnavailable:
            return jsonify({"error": "RPT dengan identiti sekolah belum dapat disediakan. Sila cuba semula."}), 503
        return send_file(document, mimetype="application/pdf", as_attachment=True,
                         download_name=path.name, conditional=False)

    return bp
