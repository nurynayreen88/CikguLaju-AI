"""CikguLaju 2027 Web: 12-subject, 56-PDF authenticated download catalog.

The 56 owner-approved-to-show *DRAF* PDFs are shipped as fixed local files
under rpt_2027/web_2027_pdfs/ by the source-checked GitHub release workflow.
No cloud redirects, unverified fallback to other subjects/years, quota debits
or user/database writes. An existing per-subject RPT PDF remains a safe
compatibility fallback until the complete new catalog is deployed.
"""
from __future__ import annotations
import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path
from flask import Blueprint, jsonify, send_file, request
from web.english_rpt_2027_http import _account, _has_paid_access

ROOT = Path(__file__).resolve().parents[1] / "rpt_2027"
YEARS = tuple(range(2,7))
V2 = "web_2027_pdfs"
# (Label, allowed years, legacy folder, legacy exact filename, legacy status)
SUBJECTS = {
    "english": ("English (SK)", YEARS, "english", "RPT_ENGLISH_TAHUN_%d_2027_UNTUK_GURU.pdf", "TERSEDIA"),
    "bahasa_melayu": ("Bahasa Melayu", YEARS, "bahasa_melayu", "RPT_Bahasa_Melayu_Tahun_%d_2027_DRAF.pdf", "DRAF"),
    "matematik": ("Matematik", YEARS, "matematik", "RPT_Matematik_Tahun_%d_2027_v28_SEMENTARA.pdf", "SEMENTARA"),
    "sains": ("Sains", YEARS, None, None, "SEPARA DRAF"),
    "pendidikan_islam": ("Pendidikan Islam", YEARS, "pendidikan_islam", "RPT_Pendidikan_Islam_Tahun_%d_2027_CikguLaju.pdf", "DRAF"),
    "pjpk": ("PJPK", YEARS, "pjpk", "RPT_PJPK_Tahun_%d_2027_DRAF.pdf", "DRAF"),
    "pendidikan_moral": ("Pendidikan Moral", YEARS, "pendidikan_moral", "RPT_Pendidikan_Moral_Tahun_%d_2027_DRAF_WEB.pdf", "DRAF"),
    "psv": ("Pendidikan Seni Visual", YEARS, "psv", "RPT_PSV_Tahun_%d_2027_DRAF_WEB.pdf", "DRAF"),
    "bahasa_arab": ("Bahasa Arab", YEARS, None, None, "DRAF"),
    "muzik": ("Pendidikan Muzik", YEARS, None, None, "DRAF"),
    "rbt": ("Reka Bentuk dan Teknologi", (4,5,6), None, None, "DRAF"),
    "sejarah": ("Sejarah", (4,5,6), None, None, "DRAF"),
}
assert sum(len(v[1]) for v in SUBJECTS.values())==56
# Years that really have Year 1 KP2027 curriculum; never show Year 1
# for upper-primary-only RBT and Sejarah.
YEAR1_KP2027_CODES=frozenset(set(SUBJECTS)-{"rbt","sejarah"})
assert len(YEAR1_KP2027_CODES)==10
YEAR1_PREVIEW_STATUS="KP2027 — AKAN DATANG"
NOTES={
    "sains":"SEPARA DRAF: SK/SP dan RPH belum selesai audit penuh.",
    "bahasa_arab":"DRAF SEMAKAN: 290/298 PdP ada calon ayat SP daripada DSKP; 8 PdP kekal kod SP sahaja. Pernyataan SK penuh dan ketepatan padanan PdP belum disahkan; bukan FINAL READY.",
    "rbt":"DRAF: agihan minggu PdP perlu disesuaikan dengan jadual sekolah.",
    "sejarah":"DRAF: semak agihan PdP mengikut RPT sekolah.",
    "pendidikan_islam":"DRAF: beberapa sesi tasmi dan PdP pilihan belum diluluskan.",
}
DEFAULT_NOTE="DRAF 2027: semak SK/SP, tarikh, hari PdP dan kesesuaian sekolah sebelum guna."

def expected_pairs():
    return {f"{code}:{year}" for code,spec in SUBJECTS.items() for year in spec[1]}

def _release_manifest(root=ROOT):
    """Return only an internally complete, non-releasing set of 56 exact hashes."""
    path=Path(root)/V2/"manifest.json"
    if path.is_symlink() or not path.is_file():
        return {}
    try:
        source=json.loads(path.read_text("utf-8"))
        entries=source.get("files")
        if (source.get("version")!=1 or source.get("year")!=2027
            or source.get("status")!="DRAF_USER_VISIBLE_NOT_ACADEMIC_FINAL"
            or source.get("count")!=56 or not isinstance(entries,dict)
            or set(entries)!=expected_pairs()):
            return {}
        for key,value in entries.items():
            code,year_s=key.split(":")
            expected=f"{code}/tahun_{year_s}.pdf"
            if (not isinstance(value,dict) or value.get("path")!=expected
                or not re.fullmatch(r"[a-f0-9]{64}",str(value.get("sha256","")))
                or type(value.get("bytes")) is not int
                or not 8_000<=value["bytes"]<=25*1024*1024
                or type(value.get("pages")) is not int or not 2<=value["pages"]<=300
                or value.get("status")!="DRAF"):
                return {}
        return entries
    except (ValueError,KeyError,TypeError,UnicodeError,OSError):
        return {}

def _staged_file(subject,year,*,root=ROOT):
    entry=_release_manifest(root).get(f"{subject}:{year}")
    if not entry:
        return None
    root=Path(root)/V2
    path=root/entry["path"]
    if not path.is_file() or path.is_symlink():
        return None
    try:
        if path.stat().st_size!=entry["bytes"]:
            return None
        with path.open("rb") as stream:
            if stream.read(5)!=b"%PDF-":
                return None
            h=hashlib.sha256()
            h.update(b"%PDF-")
            for block in iter(lambda:stream.read(1024*1024),b""):
                h.update(block)
            if h.hexdigest()!=entry["sha256"]:
                return None
        return path
    except OSError:
        return None

def _legacy_file(subject,year,*,root=ROOT):
    spec=SUBJECTS.get(subject)
    if not spec or year not in spec[1] or not spec[2]:
        return None
    path=Path(root)/spec[2]/(spec[3]%year)
    try:
        if (path.is_symlink() or not path.is_file()
            or path.stat().st_size<8_000
            or path.open("rb").read(5)!=b"%PDF-"):
            return None
    except OSError:
        return None
    return path

def pdf_path(subject,year,*,root=ROOT):
    """Exact intended path, including legacy path before its PDF is installed."""
    if type(year) is not int or subject not in SUBJECTS or year not in SUBJECTS[subject][1]:
        raise ValueError("Unsupported RPT selection")
    staged=_staged_file(subject,year,root=root)
    if staged is not None:
        return staged
    spec=SUBJECTS[subject]
    if spec[2]:
        return Path(root)/spec[2]/(spec[3]%year)
    return None

def pdf_ready(subject,year,*,root=ROOT):
    try:
        return (_staged_file(subject,year,root=root) is not None
                or _legacy_file(subject,year,root=root) is not None)
    except ValueError:
        return False

def catalog_data(*,root=ROOT, allowed=True, personalization_allowed=False):
    subjects=[]
    available=0
    for code,(label,years,folder,legacy_name,status) in SUBJECTS.items():
        entries=[]
        display_years=((1,)+years) if code in YEAR1_KP2027_CODES else years
        for year in display_years:
            # Tahun 1 follows the KP2027 curriculum, a separate source from
            # the old KSSR/2017 PDF. Explicit non-downloadable placeholder.
            if year==1:
                entries.append({
                    "year":1,
                    "pdf_ready":False,
                    "status":YEAR1_PREVIEW_STATUS,
                    "download_enabled":False,
                    "note":"RPT Tahun 1 KP2027 masih disediakan. PDF belum diterbitkan.",
                    "is_draft":True,
                    "coming_soon":True,
                })
                continue
            current=_staged_file(code,year,root=root)
            legacy=_legacy_file(code,year,root=root) if current is None else None
            ready=current is not None or legacy is not None
            if ready:
                available+=1
            entry_status=status if current is None else ("SEPARA DRAF" if code=="sains" else "DRAF")
            entries.append({
                "year":year,
                "pdf_ready":ready,
                "status":entry_status if ready else "PDF BELUM DIPASANG",
                "download_enabled":bool(ready and allowed),
                "note":NOTES.get(code,DEFAULT_NOTE),
                "is_draft":current is not None or entry_status!="TERSEDIA",
            })
        subjects.append({"code":code,"label":label,"years":entries})
    return {
        "year":2027,
        "format":"pdf",
        "allowed":bool(allowed),
        "personalization_allowed":bool(personalization_allowed),
        "subjects":subjects,
        "total_rpt":56,
        "total_display_choices":66,
        "year1_coming_soon":10,
        "available_rpt":available,
        "note":"Tahun 1 KP2027 belum boleh dimuat turun. RPT Tahun 2–6 boleh dimuat turun oleh semua pengguna log masuk; nama dan logo hanya dicetak untuk akses berbayar yang masih aktif.",
    }

def create_all_rpt_blueprint(*,root=ROOT):
    bp=Blueprint("all_rpt_2027_pdf",__name__)
    @bp.after_request
    def private_cache(response):
        response.headers["Cache-Control"]="no-store, private"
        response.headers["X-Content-Type-Options"]="nosniff"
        response.headers["Vary"]="Cookie"
        return response

    @bp.get("/api/rpt/2027/catalog")
    def catalog():
        account,error=_account()
        if error is not None:
            return error
        return jsonify(catalog_data(root=root,allowed=True,
                                    personalization_allowed=_has_paid_access(account)))

    @bp.get("/api/rpt/2027/all/<subject>/<int:year>.pdf")
    def download(subject,year):
        account,error=_account()
        if error is not None:
            return error
        if subject not in SUBJECTS or year not in SUBJECTS[subject][1]:
            return jsonify({"error":"Pilihan RPT tidak sah"}),404
        staged=_staged_file(subject,year,root=root)
        path=staged or _legacy_file(subject,year,root=root)
        if path is None:
            return jsonify({"error":"PDF RPT ini belum dipasang pada pelayan. Cuba lagi kemudian."}),503
        paid_cover=_has_paid_access(account)
        # The staged 56-source set differs from the Telegram local originals;
        # do not call its SHA-locked personalization API with an unknown hash.
        # Download the exact validated DRAF; teacher identity stays private.
        if staged is not None or not paid_cover:
            # Free and expired users receive the validated source PDF, never
            # any server-side school identity. Profile data remains stored.
            document=path
        else:
            from web.rpt_school_cover import for_download
            from web.teacher_profile_store import ProfileUnavailable
            try:
                document=for_download(account,path,subject,year)
            except ProfileUnavailable:
                return jsonify({"error":"RPT dengan identiti sekolah belum dapat disediakan."}),503
        response=send_file(document,mimetype="application/pdf",as_attachment=True,
                           download_name=f"CIKGULAJU_RPT_{subject.upper()}_TAHUN_{year}_2027_DRAF.pdf",
                           conditional=False)
        response.headers["X-RPT-Personalization-Allowed"]="1" if paid_cover else "0"
        if staged is not None:
            # Exact PDF hash is from the prevalidated 56-source manifest.
            # Browser must match it to the audited original-cover layout;
            # a future PDF with a changed template cannot be stamped blindly.
            response.headers["X-RPT-Source-SHA256"]=(
                _release_manifest(root)[f"{subject}:{year}"]["sha256"])
        return response
    return bp
