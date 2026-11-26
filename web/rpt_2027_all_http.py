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
import hmac
import os
import re
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from flask import Blueprint, jsonify, send_file, request
from primary_language_subjects import PRIMARY_LANGUAGE_SUBJECTS
from web import native_telegram_ppki_client as ppki
from web import kp2027_year1_rpt_bundle as kp_rpt
from web import kp2027_year1_rpt_combined as kp_ab
from web import rpt_2027_kssr_bm_word as bm_word
from web import rpt_kssr_bm_private_storage as private_bm_word
from web import rpt_native_word_batch as native_word
from web import rpt_compact_pdf as compact_pdf
from web.english_rpt_2027_http import _account, _has_paid_access, integrated_pdf_path
from rpt_2027.dlp.documents import PUBLISHED_YEARS, SUBJECTS as DLP_SUBJECTS, document_path
from rpt_2027.matematik import sk_documents as matematik_sk
from rpt_2027.sains import sk_documents as sains_sk

from rpt_2027.sjkc.bahasa_cina import documents as bahasa_cina_sjkc
from rpt_2027.sjkc.bahasa_melayu import documents as bahasa_melayu_sjk
from rpt_2027.sjkc.sains import documents as sains_sjkc
from rpt_2027.sjkc.matematik import documents as matematik_sjkc
from rpt_2027.sjkt.matematik import documents as matematik_sjkt

ROOT = Path(__file__).resolve().parents[1] / "rpt_2027"
YEARS = tuple(range(2,7))
MATH_DPK_CODE = "matematik_dpk"
V2 = "web_2027_pdfs"
SJK_RPTS = {
    "bahasa-cina": bahasa_cina_sjkc,
    "bahasa-melayu": bahasa_melayu_sjk,
    "sains": sains_sjkc,
    "matematik": matematik_sjkc,
}
SCHOOL_RPTS = {"sjkc": SJK_RPTS, "sjkt": {"matematik": matematik_sjkt}}
SCHOOL_ROUTE_BY_CODE = {
    definition.CODE: (school, slug)
    for school, definitions in SCHOOL_RPTS.items()
    for slug, definition in definitions.items()
}
# (Label, allowed years, legacy folder, legacy exact filename, legacy status)
SUBJECTS = {
    "english": ("English (SK)", YEARS, "english", "RPT_ENGLISH_TAHUN_%d_2027_UNTUK_GURU.pdf", "TERSEDIA"),
    "bahasa_melayu": ("Bahasa Melayu", YEARS, "bahasa_melayu", "RPT_Bahasa_Melayu_Tahun_%d_2027_DRAF.pdf", "DRAF"),
    "matematik": ("Matematik SK", YEARS, "matematik", "RPT_Matematik_Tahun_%d_2027_v28_SEMENTARA.pdf", "SEMENTARA"),
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

def _integrated_english_file(subject, year, root):
    if subject != "english":
        return None, None
    path = integrated_pdf_path(Path(root) / "english", year)
    if path is None:
        return None, None
    try:
        layout = json.loads((Path(root) / V2 / "original_cover_layout_verified.json").read_text("utf-8"))
        expected = layout["english_integrated"]["source_sha256_by_subject_year"][f"english:{year}"]
        if path.is_symlink() or not 8000 <= path.stat().st_size <= 1_000_000:
            return path, None
        content = path.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        if content.startswith(b"%PDF-") and hmac.compare_digest(digest, expected):
            return path, digest
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return path, None


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
    if subject == "matematik" and year in matematik_sk.DIGESTS:
        return Path(root) / "matematik" / (matematik_sk.FILE_TEMPLATE % year)
    staged=_approved_sk_science_file(subject, year, root) or _staged_file(subject,year,root=root)
    if staged is not None:
        return staged
    spec=SUBJECTS[subject]
    if spec[2]:
        return Path(root)/spec[2]/(spec[3]%year)
    return None

def pdf_ready(subject,year,*,root=ROOT):
    try:
        if subject == "matematik" and year in matematik_sk.DIGESTS:
            return matematik_sk.document_path(year, root=Path(root) / "matematik") is not None
        return (_approved_sk_science_file(subject, year, root) is not None
                or _staged_file(subject,year,root=root) is not None
                or _legacy_file(subject,year,root=root) is not None)
    except ValueError:
        return False


def _approved_sk_science_file(subject, year, root):
    if subject == "sains":
        return sains_sk.document_path(year, root=Path(root) / "sains")
    return None

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
            integrated, digest = _integrated_english_file(code, year, root)
            if integrated is not None:
                ready = digest is not None
                available += int(ready)
                word_ready=bool(personalization_allowed and native_word.eligible_integrated_english(year,integrated,digest,root=root))
                entries.append({
                    "year": year, "year_label": f"Year {year}", "pdf_ready": ready,
                    "docx_ready":word_ready,"word_paid_only":True,
                    "docx_url":f"/api/rpt/2027/all/{code}/{year}.docx" if word_ready else None,
                    "status": "SEMAKAN GURU" if ready else "PDF BELUM DIPASANG",
                    "download_enabled": bool(ready and allowed), "is_draft": True,
                    "note": "Kumpulan A dan B. 160 rujukan SOW dalam 142 sesi hingga akhir Oktober.",
                })
                continue
            approved = _approved_sk_science_file(code, year, root)
            if approved is not None:
                available += 1
                approved_word=bool(personalization_allowed and native_word.eligible_approved_science(year,approved,root=root))
                entries.append({"year": year, "pdf_ready": True, "status": "TERSEDIA",
                                "download_enabled": bool(allowed), "is_draft": False,
                                "docx_ready":approved_word,"word_paid_only":True,
                                "docx_url":f"/api/rpt/2027/all/{code}/{year}.docx" if approved_word else None,
                                "note": f"Kumpulan A dan B. {sains_sk.PDP_COUNTS[year]} PdP dalam 64 jam."})
                continue
            if code == "matematik" and year in matematik_sk.DIGESTS:
                ready = pdf_ready(code, year, root=root)
                available += int(ready)
                source=matematik_sk.document_path(year,root=Path(root)/"matematik")
                approved_word=bool(personalization_allowed and native_word.eligible_approved_math(year,source,root=root))
                entries.append({"year": year, "pdf_ready": ready,
                                "status": "TERSEDIA" if ready else "PDF BELUM DIPASANG",
                                "download_enabled": bool(ready and allowed), "is_draft": False,
                                "docx_ready":approved_word,"word_paid_only":True,
                                "docx_url":f"/api/rpt/2027/all/{code}/{year}.docx" if approved_word else None,
                                "note": "Kumpulan A dan B. 117 Lesson dalam 96 jam hingga Minggu 38."})
                continue
            current=_staged_file(code,year,root=root)
            legacy=_legacy_file(code,year,root=root) if current is None else None
            ready=current is not None or legacy is not None
            if ready:
                available+=1
            entry_status=status if current is None else ("SEPARA DRAF" if code=="sains" else "DRAF")
            word = (
                (private_bm_word.verified_manifest_entry(year,root=root)
                 if os.environ.get("CIKGULAJU_KSSR_BM_WORD_PRIVATE")=="1"
                 else bm_word.word_document(year,root=root))
                if code=="bahasa_melayu" and personalization_allowed and ready else None)
            batch_word = bool(personalization_allowed and native_word.eligible(code,year,current,root=root))
            entries.append({
                "year":year,
                "pdf_ready":ready,
                "status":entry_status if ready else "PDF BELUM DIPASANG",
                "download_enabled":bool(ready and allowed),
                "docx_ready":bool(word or batch_word),
                "docx_url":f"/api/rpt/2027/all/{code}/{year}.docx" if word or batch_word else None,
                "word_paid_only":code=="bahasa_melayu" or batch_word,
                "note":NOTES.get(code,DEFAULT_NOTE),
                "is_draft":current is not None or entry_status!="TERSEDIA",
            })
        subjects.append({"code":code,"label":label,"years":entries})
    dlp_count = 0
    for code, label in DLP_SUBJECTS.items():
        entries = [
            {
                "year": year,
                "pdf_ready": True,
                "status": "TERSEDIA",
                "download_enabled": bool(allowed),
                "note": f"Year {year} SK · Group A and Group B",
                "docx_ready":bool(personalization_allowed and native_word.eligible_dlp(code,year,root=root)),
                "word_paid_only":True,
                "docx_url":f"/api/rpt/2027/all/{code}/{year}.docx" if personalization_allowed and native_word.eligible_dlp(code,year,root=root) else None,
                "is_draft": False,
                "year_label": f"Year {year}",
            }
            for year in PUBLISHED_YEARS
            if document_path(code, year, root=Path(root) / "dlp") is not None
        ]
        if entries:
            subjects.append({"code": code, "label": f"{label} (DLP)", "years": entries})
            dlp_count += len(entries)
    sjk_count = 0
    for school, definitions in SCHOOL_RPTS.items():
        for slug, definition in definitions.items():
            folder = Path(root) / school / slug.replace("-", "_")
            entries = []
            for year in definition.YEARS:
                if definition.document_path(year, root=folder) is None:
                    continue
                ready = bool(allowed and personalization_allowed)
                word_ready = bool(ready and definition.document_path(year, "docx", root=folder))
                entries.append({
                    "year": year,
                    "pdf_ready": True,
                    "status": "TERSEDIA" if ready else "Akses berbayar",
                    "download_enabled": ready,
                    "docx_ready": word_ready,
                    "docx_url": f"/api/rpt/2027/{school}/{slug}/{year}.docx" if word_ready else None,
                    "note": "Tarikh Kumpulan A dan B dalam satu RPT.",
                    "is_draft": False,
                })
            if entries:
                subjects.append({"code": definition.CODE, "label": definition.LABEL, "years": entries})
                sjk_count += len(entries)
    for code, label in PRIMARY_LANGUAGE_SUBJECTS.items():
        subjects.append({
            "code": code,
            "label": label,
            "years": [{
                "year": year,
                "pdf_ready": False,
                "status": "Dalam Penyediaan",
                "download_enabled": False,
                "note": "RPT KSSR untuk sekolah rendah sedang disediakan.",
                "is_draft": True,
                "coming_soon": True,
            } for year in YEARS],
        })
    dpk_entries = [
        {"year": year, "pdf_ready": True, "status": "TERSEDIA",
         "download_enabled": bool(allowed), "is_draft": False,
         "note": "Kumpulan A dan B. 117 Lesson dalam 96 jam."}
        for year in matematik_sk.DPK_DIGESTS
        if matematik_sk.document_path(year, root=Path(root) / "matematik", dpk=True)
    ]
    if dpk_entries:
        subjects.append({"code": MATH_DPK_CODE, "label": "Matematik SK (DPK Edisi 3)",
                         "years": dpk_entries})
    return {
        "year":2027,
        "format":"pdf",
        "allowed":bool(allowed),
        "personalization_allowed":bool(personalization_allowed),
        "subjects":subjects,
        "total_rpt":56+dlp_count+sjk_count+len(dpk_entries),
        "total_display_choices":sum(len(item["years"]) for item in subjects),
        "year1_coming_soon":10,
        "available_rpt":available+dlp_count+sjk_count+len(dpk_entries),
        "note":"RPT PDF mengikut akses sedia ada. RPT Word hanya untuk Rakan Pembangun dan langganan aktif apabila fail Word disahkan tersedia.",
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
        paid = _has_paid_access(account)
        data = catalog_data(root=root, allowed=True, personalization_allowed=paid)
        # Extend only the live Web response; retain historical 56-source
        # catalog_data counts and KSSR regression fixtures exactly as before.
        # KP2027 archive status is distinct from 56 legacy RPT PDFs.
        if kp_ab.ready():
            data["kp2027_rpt_available"] = [{
                "code": code, "label": label, "year": 1,
                "pdf_ready": True, "docx_ready": True,
                "docx_download_enabled": bool(paid), "word_paid_only": True,
                "download_enabled": True, "kp2027_combined": True, "kp2027_groups": ["A","B"],
                "status": "RPT SEMAKAN PELAKSANAAN",
                "note": ("Satu RPT bagi setiap subjek mengandungi tarikh Kumpulan A dan B. "
                         "Tarikh, cuti, jadual sekolah dan padanan RPH perlu disahkan."),
                "is_draft": True,
            } for code,label in (
                ("matematik","Matematik"),
                ("bahasa_melayu","Bahasa Melayu SK"),
                ("alam_dan_manusia","Alam dan Manusia"),
            )]
        ppki_years = []
        manipulative_years = []
        for ppki_year in ppki.YEARS:
            try:
                ppki_source = ppki.catalog() if ppki_year == ppki.YEAR else ppki.catalog(ppki_year)
            except ppki.NativeRPHUnavailable:
                continue
            by_unit = ppki_source["lessons_by_unit"]
            unit_numbers = ppki_source["unit_numbers"]
            edition = f"Unit {unit_numbers[0]}"
            if len(unit_numbers) > 1:
                edition += f"–{unit_numbers[-1]}"
            count = sum(len(lessons) for lessons in by_unit.values())
            ppki_years.append({
                "year": ppki_year, "status": f"AGIHAN {edition.upper()}", "pdf_ready": True,
                "download_enabled": paid, "is_draft": False,
                "note": f"Pengurusan Diri · Agihan {count} PdP {edition}. Guru menetapkan tarikh PdP mengikut jadual kelas.",
            })
            for key in ("total_rpt", "available_rpt", "total_display_choices"):
                data[key] += 1
            manipulative = ppki_source["units_by_component"].get(ppki.MANIPULATIVE_COMPONENT, [])
            if len(manipulative) == 3:
                km_count = sum(len(ppki_source["rph_lessons_by_unit"][unit["value"]]) for unit in manipulative)
                manipulative_years.append({
                    "year": ppki_year, "status": "AGIHAN UNIT 1–3", "pdf_ready": True,
                    "download_enabled": paid, "is_draft": False,
                    "note": f"Agihan {km_count} PdP Unit 1–3. Guru menetapkan tarikh PdP mengikut jadual kelas.",
                })
                for key in ("total_rpt", "available_rpt", "total_display_choices"):
                    data[key] += 1
        if manipulative_years:
            data["subjects"].append({
                "code": ppki.RPT_MANIPULATIVE_CODE, "label": "Kemahiran Manipulatif", "years": manipulative_years,
            })
        if ppki_years:
            data["subjects"].append({"code": ppki.RPT_CODE, "label": "Pengurusan Kehidupan", "years": ppki_years})
        return jsonify(data)

    @bp.get("/api/rpt/2027/kp2027/tahun-1/gabungan/<subject>.<fmt>")
    def download_kp2027_year1_gabungan(subject,fmt):
        account,error=_account()
        if error is not None:
            return error
        if subject not in kp_ab.SUBJECTS or fmt not in kp_ab.FORMATS:
            return jsonify({"error":"Pilihan RPT KP2027 tidak sah."}),404
        paid_cover=_has_paid_access(account)
        # Word contains editable material; trial credits and free PDF access
        # must never authorize Word, even when its URL is typed directly.
        if fmt=="docx" and not paid_cover:
            return jsonify({"error":"RPT Word hanya untuk Rakan Pembangun dan pengguna berbayar aktif."}),403
        try:
            content,filename,digest=kp_ab.document(subject,fmt)
        except kp_ab.BundleUnavailable:
            return jsonify({"error":"RPT KP2027 gabungan belum disahkan pada pelayan."}),503
        mimetype=("application/pdf" if fmt=="pdf" else
                  "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        personalized=False
        if paid_cover:
            from web.kp2027_year1_rpt_personalize import for_download as personalize_rpt
            from web.teacher_profile_store import ProfileUnavailable, ProfileValidation
            try:
                content,personalized=personalize_rpt(account,subject,fmt,content)
            except (ProfileUnavailable,ProfileValidation):
                return jsonify({"error":"RPT dengan identiti sekolah belum dapat disediakan. Sila semak Profil Saya dan cuba lagi."}),503
        response=send_file(BytesIO(content),mimetype=mimetype,as_attachment=True,
                           download_name=filename,conditional=False)
        response.headers["X-RPT-Source-SHA256"]=digest
        response.headers["X-RPT-Output-SHA256"]=hashlib.sha256(content).hexdigest()
        response.headers["X-RPT-Personalization-Allowed"]="1" if paid_cover else "0"
        response.headers["X-RPT-Personalization-Applied"]="1" if personalized else "0"
        response.headers["X-RPT-Curriculum"]="KP2027-Year1"
        response.headers["X-RPT-QA-Status"]="SEMAKAN-PELAKSANAAN"
        response.headers["X-RPT-Groups"]="A,B"
        return response

    @bp.get("/api/rpt/2027/kp2027/tahun-1/<subject>/<group>.<fmt>")
    def download_kp2027_year1(subject, group, fmt):
        account, error = _account()
        if error is not None:
            return error
        if subject not in kp_rpt.SUBJECTS or group not in kp_rpt.GROUPS or fmt not in kp_rpt.FORMATS:
            return jsonify({"error": "Pilihan RPT KP2027 tidak sah."}), 404
        if fmt == "docx" and not _has_paid_access(account):
            return jsonify({"error":"RPT Word hanya untuk Rakan Pembangun dan pengguna berbayar aktif."}),403
        try:
            payload, filename, digest = kp_rpt.document(subject, group, fmt)
        except kp_rpt.BundleUnavailable:
            return jsonify({"error": "RPT KP2027 belum disahkan pada pelayan."}), 503
        mime = ("application/pdf" if fmt == "pdf" else
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        response = send_file(BytesIO(payload), mimetype=mime, as_attachment=True,
                             download_name=filename, conditional=False)
        response.headers["X-RPT-Source-SHA256"] = digest
        response.headers["X-RPT-Personalization-Allowed"] = "0"
        response.headers["X-RPT-Curriculum"] = "KP2027-Year1"
        response.headers["X-RPT-QA-Status"] = "SEMAKAN-PELAKSANAAN"
        return response

    @bp.get("/api/rpt/2027/sjkc/<slug>/<int:year>.<fmt>", defaults={"school": "sjkc"})
    @bp.get("/api/rpt/2027/sjkt/<slug>/<int:year>.<fmt>", defaults={"school": "sjkt"})
    def download_sjk(slug, year, fmt, school):
        account, error = _account()
        if error is not None:
            return error
        definition = SCHOOL_RPTS[school].get(slug)
        if definition is None:
            return jsonify({"error": "Pilihan RPT SJK tidak tersedia."}), 404
        if not _has_paid_access(account):
            return jsonify({"error": f"RPT {definition.LABEL} memerlukan akses berbayar aktif."}), 403
        path = definition.document_path(year, fmt, root=Path(root) / school / slug.replace("-", "_"))
        if path is None:
            return jsonify({"error": f"Pilihan RPT {definition.LABEL} tidak tersedia."}), 404
        mime = ("application/pdf" if fmt == "pdf" else
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        response = send_file(path, mimetype=mime, as_attachment=True, conditional=False)
        if fmt == "pdf":
            response.headers["X-RPT-Source-SHA256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            response.headers["X-RPT-Personalization-Allowed"] = "1"
        return response

    @bp.get("/api/rpt/2027/all/<subject>/<int:year>.docx")
    def download_kssr_word(subject,year):
        account,error=_account()
        if error is not None:
            return error
        approved_science=subject=="sains" and year in native_word.APPROVED_SCIENCE_PINS
        approved_math=subject=="matematik" and year in matematik_sk.DIGESTS
        integrated_english,english_digest=_integrated_english_file(subject,year,root)
        english_word=subject=="english" and integrated_english is not None
        dlp_word=subject in DLP_SUBJECTS and year in PUBLISHED_YEARS
        if native_word.enabled() and (f"{subject}:{year}" in native_word.PINS or approved_science or approved_math or english_word or dlp_word):
            if not _has_paid_access(account):
                return jsonify({"error":"RPT Word hanya untuk Rakan Pembangun dan pengguna berbayar aktif."}),403
            source=_approved_sk_science_file(subject,year,root) if approved_science else _staged_file(subject,year,root=root)
            if approved_math:
                source=matematik_sk.document_path(year,root=Path(root)/"matematik")
            if not (approved_science or approved_math) and ((subject=="matematik" and year in matematik_sk.DIGESTS) or _approved_sk_science_file(subject,year,root) is not None):
                return jsonify({"error":"Versi RPT Word belum sepadan dengan PDF terkini."}),503
            from web_v1_telegram_auth_routes import _config
            try:
                if approved_science:
                    blob,digest=native_word.approved_science_document(year,source,account,_config(),root=root)
                elif approved_math:
                    blob,digest=native_word.approved_math_document(year,source,account,_config(),root=root)
                elif english_word:
                    blob,digest=native_word.integrated_english_document(year,integrated_english,english_digest,account,_config(),root=root)
                elif dlp_word:
                    blob,digest=native_word.dlp_document(subject,year,account,_config(),root=root)
                else:
                    blob,digest=native_word.document(subject,year,source,account,_config(),root=root)
            except Exception:
                return jsonify({"error":"RPT Word belum dapat disediakan. Sila cuba semula."}),503
            response=send_file(BytesIO(blob),as_attachment=True,conditional=False,
                mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                download_name=f"CIKGULAJU_RPT_{subject.upper()}_SK_TAHUN_{year}_2027_WORD.docx")
            response.headers["X-RPT-Source-SHA256"]=digest
            response.headers["X-RPT-Word-Access"]="paid-founder-only"
            response.headers["X-RPT-Academic-Status"]="TERSEDIA" if (approved_science or approved_math or dlp_word) else "DRAF_SEMAKAN"
            return response
        if subject!="bahasa_melayu" or year not in bm_word.YEARS:
            return jsonify({"error":"RPT Word KSSR belum tersedia bagi pilihan ini."}),404
        # Backend gate also applies to users copying the URL, not just menu.
        if not _has_paid_access(account):
            return jsonify({"error":"RPT Word hanya untuk Rakan Pembangun dan pengguna berbayar aktif."}),403
        if os.environ.get("CIKGULAJU_KSSR_BM_WORD_PRIVATE")=="1":
            # Server-only Supabase read, after the existing paid access gate.
            # Never redirect the browser to a Storage URL or share service keys.
            from web_v1_telegram_auth_routes import _config
            try:
                blob,digest=private_bm_word.fetch_document(year,_config(),root=root)
            except private_bm_word.PrivateWordUnavailable:
                return jsonify({"error":"RPT Word peribadi belum tersedia. Sila cuba semula."}),503
            document=BytesIO(blob)
        else:
            source=bm_word.word_document(year,root=root)
            if source is None:
                return jsonify({"error":"RPT Word yang disahkan belum tersedia."}),503
            document,digest=source
        response=send_file(
            document,as_attachment=True,conditional=False,
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            download_name=f"CIKGULAJU_RPT_BAHASA_MELAYU_SK_TAHUN_{year}_2027_WORD.docx")
        response.headers["X-RPT-Source-SHA256"]=digest
        response.headers["X-RPT-Word-Access"]="paid-founder-only"
        response.headers["X-RPT-Academic-Status"]="DRAF_SEMAKAN"
        return response

    @bp.get("/api/rpt/2027/all/<subject>/<int:year>.pdf")
    def download(subject,year):
        if subject in SCHOOL_ROUTE_BY_CODE:
            school, slug = SCHOOL_ROUTE_BY_CODE[subject]
            return download_sjk(slug, year, "pdf", school)
        account,error=_account()
        if error is not None:
            return error
        if subject in {ppki.RPT_CODE, ppki.RPT_MANIPULATIVE_CODE}:
            if year not in ppki.YEARS:
                return jsonify({"error": "Pilihan RPT PPKI tidak tersedia."}), 404
            if not _has_paid_access(account):
                return jsonify({"error": "RPT PPKI memerlukan akses berbayar aktif."}), 403
            try:
                source = ppki.catalog() if year == ppki.YEAR else ppki.catalog(year)
                if subject == ppki.RPT_MANIPULATIVE_CODE:
                    units = source["units_by_component"].get(ppki.MANIPULATIVE_COMPONENT, [])
                    if len(units) != len(ppki.MANIPULATIVE_UNIT_LESSONS):
                        return jsonify({"error": "Pilihan RPT PPKI tidak tersedia."}), 404
                    document = ppki.request_rpt(manipulative=True, year=year)
                    filename = {
                        ppki.YEAR: ppki.RPT_MANIPULATIVE_FILENAME,
                        3: ppki.RPT_MANIPULATIVE_YEAR3_FILENAME,
                        4: ppki.RPT_MANIPULATIVE_YEAR4_FILENAME,
                        5: ppki.RPT_MANIPULATIVE_YEAR5_FILENAME,
                        6: ppki.RPT_MANIPULATIVE_YEAR6_FILENAME,
                    }[year]
                else:
                    unit_numbers = source["unit_numbers"]
                    if year == ppki.YEAR:
                        document = ppki.request_rpt(combined=len(unit_numbers) > 1)
                    else:
                        document = ppki.request_rpt(year=year)
                    filename = (f"CIKGULAJU_RPT_PPKI_PENGURUSAN_KEHIDUPAN_TAHUN_{year}_UNIT_"
                                + "_".join(str(unit) for unit in unit_numbers) + "_2027.pdf")
            except ppki.NativeRPHUnavailable:
                return jsonify({"error": "PDF RPT PPKI belum dapat dihubungi."}), 503
            response = send_file(document, mimetype="application/pdf", as_attachment=True, conditional=False,
                                 download_name=filename)
            response.headers["X-RPT-Source-SHA256"] = hashlib.sha256(document.getvalue()).hexdigest()
            response.headers["X-RPT-Personalization-Allowed"] = "0"
            return response
        math_dpk = subject == MATH_DPK_CODE and year in matematik_sk.DPK_DIGESTS
        math_sk = subject == "matematik" and year in matematik_sk.DIGESTS
        approved_sains = _approved_sk_science_file(subject, year, root)
        if math_dpk or math_sk or subject in DLP_SUBJECTS or approved_sains is not None:
            if math_dpk or math_sk:
                path = matematik_sk.document_path(year, root=Path(root) / "matematik", dpk=math_dpk)
                if path is None:
                    return jsonify({"error": "PDF RPT Matematik SK belum dapat disahkan."}), 503
            else:
                path = approved_sains or document_path(subject, year, root=Path(root)/"dlp")
            if path is None:
                return jsonify({"error":"Pilihan RPT DLP tidak tersedia"}),404
            content=path.read_bytes()
            digest=hashlib.sha256(content).hexdigest()
            compact=compact_pdf.read_approved(subject,year,content,root=root) if math_sk or approved_sains is not None else None
            revised_dlp=None
            if subject in DLP_SUBJECTS:
                revised_dlp=compact_pdf.read_full_standards_dlp(subject,year,content,root=root)
                compact=revised_dlp or compact_pdf.read_dlp(subject,year,content,root=root)
            if compact is not None:
                content,digest=compact
            flexible=bool(revised_dlp and os.environ.get("CIKGULAJU_DLP_FLEXIBLE_TIME")=="1")
            if flexible:
                from web.rpt_dlp_flexible_time import pdf_without_fixed_minutes
                content=pdf_without_fixed_minutes(content)
            response = send_file(BytesIO(content), mimetype="application/pdf", as_attachment=True,
                                 download_name=path.name, conditional=False)
            response.headers["X-RPT-Source-SHA256"] = digest
            if flexible:
                response.headers["X-RPT-Output-SHA256"]=hashlib.sha256(content).hexdigest()
                response.headers["X-RPT-Layout-Transform"]="dlp-flexible-time-v1"
            response.headers["X-RPT-Personalization-Allowed"] = "1" if _has_paid_access(account) else "0"
            return response
        if subject not in SUBJECTS or year not in SUBJECTS[subject][1]:
            return jsonify({"error":"Pilihan RPT tidak sah"}),404
        integrated, digest = _integrated_english_file(subject, year, root)
        if integrated is not None:
            if digest is None:
                return jsonify({"error": "PDF RPT English bersepadu belum dapat disahkan."}), 503
            content=integrated.read_bytes()
            compact=compact_pdf.read_language(subject,year,content,root=root)
            if compact is not None:
                content,digest=compact
            response = send_file(BytesIO(content), mimetype="application/pdf", as_attachment=True,
                                 download_name=integrated.name, conditional=False)
            response.headers["X-RPT-Source-SHA256"] = digest
            response.headers["X-RPT-Personalization-Allowed"] = "1" if _has_paid_access(account) else "0"
            return response
        staged=_staged_file(subject,year,root=root)
        path=staged or _legacy_file(subject,year,root=root)
        if path is None:
            return jsonify({"error":"PDF RPT ini belum dipasang pada pelayan. Cuba lagi kemudian."}),503
        paid_cover=_has_paid_access(account)
        # Always return the immutable source bytes and their exact digest.
        # The legacy Telegram cover service PREPENDS a page; that is incompatible
        # with the approved single existing cover and the browser's SHA guard.
        content=path.read_bytes()
        if not 8_000<=len(content)<=25*1024*1024 or not content.startswith(b"%PDF-"):
            return jsonify({"error":"Fail RPT asal tidak sah."}),503
        digest=hashlib.sha256(content).hexdigest()
        if staged is not None and digest!=_release_manifest(root)[f"{subject}:{year}"]["sha256"]:
            return jsonify({"error":"Versi RPT tidak sepadan."}),503
        cover_reviewed = True
        if paid_cover and staged is None:
            # Compatibility downloads may be personalized only when their exact
            # bytes match an existing reviewed original-cover layout.
            try:
                layout=json.loads((Path(root)/V2/"original_cover_layout_verified.json").read_text("utf8"))
                key=f"{subject}:{year}"
                candidates=[layout,layout.get("english_integrated",{}),
                            layout.get("aligned_rpt_covers",{}).get(key,{}),
                            layout.get("science_year6_covers",{}).get(key,{})]
                reviewed=any(x.get("source_sha256_by_subject_year",{}).get(key)==digest
                             for x in candidates)
            except (OSError,ValueError,TypeError,AttributeError):
                reviewed=False
            cover_reviewed = reviewed
        # Keep a valid, exact legacy PDF downloadable even when the original
        # cover has not been reviewed. Entitlement is unchanged; the browser
        # must not fetch private profile data or stamp an unreviewed cover.
        compact=compact_pdf.read(subject,year,content,root=root) if staged is not None else None
        if compact is None and staged is not None and subject=="bahasa_melayu":
            compact=compact_pdf.read_language(subject,year,content,root=root)
        if compact is None and staged is not None and subject in ("pendidikan_islam","bahasa_arab"):
            compact=compact_pdf.read_rtl(subject,year,content,root=root)
        if compact is not None:
            content,digest=compact
        response=send_file(BytesIO(content),mimetype="application/pdf",as_attachment=True,
                           download_name=f"CIKGULAJU_RPT_{subject.upper()}_TAHUN_{year}_2027_DRAF.pdf",
                           conditional=False)
        response.headers["X-RPT-Personalization-Allowed"]="1" if paid_cover else "0"
        response.headers["X-RPT-Source-SHA256"]=digest
        if paid_cover and not cover_reviewed:
            response.headers["X-RPT-Cover-Status"]="unverified"
        return response
    return bp
