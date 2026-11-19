"""Protected internal document generation using the running Telegram RPH engine.

The authenticated Web proxy sends only a previously validated, source-backed
RPH layout. Telegram uses its *existing* create_word_file/create_pdf_file,
including its installed subject-specific lesson adapters. No second bot process,
no mutation of users, subscriptions or quotas, no public direct download.
"""
import hmac
import io
import json
import os
import re
import tempfile
import uuid
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
from zipfile import ZipFile

from flask import Blueprint, Response, jsonify, request
from web.rph_teacher_reflection import clean_reflection, valid_teacher_fields

MIMES = {
    "word": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pdf": "application/pdf",
}
SUBJECTS = {
    "ENGLISH": "English",
    "BM": "Bahasa Melayu",
    "MATH": "Matematik",
    "SCIENCE": "Sains",
    "PI": "Pendidikan Islam",
    "MORAL": "Pendidikan Moral",
    "PJPK": "Pendidikan Jasmani dan Pendidikan Kesihatan",
    "PSV": "Pendidikan Seni Visual",
}
MIN_LENGTH=32
MAX_BODY=100000
MAX_RESULT=15*1024*1024
LAYOUT_STYLE="telegram-native-rph-v1"
HEADINGS={
    "OBJEKTIF PEMBELAJARAN":("OBJEKTIF PEMBELAJARAN","Learning Objectives"),
    "KRITERIA KEJAYAAN":("KRITERIA KEJAYAAN","Success Criteria"),
    "PENGETAHUAN SEDIA ADA":("PENGETAHUAN SEDIA ADA","Prior Knowledge"),
    "BAHAN BANTU MENGAJAR":("BAHAN BANTU MENGAJAR","Teaching and Learning Materials"),
    "EMK / NILAI":("EMK / NILAI","CCE / Values"),
    "KBAT / PAK21":("KBAT / PAK21","HOTS / 21st Century Skills"),
    "PENTAKSIRAN":("PENTAKSIRAN","Assessment"),
    "STANDARD KANDUNGAN":("STANDARD KANDUNGAN",),
    "STANDARD PEMBELAJARAN":("STANDARD PEMBELAJARAN",),
}
ENGLISH_STANDARDS={
    "MAIN CONTENT STANDARD":"Main Content Standard",
    "MAIN LEARNING STANDARD":"Main Learning Standard",
    "COMPLEMENTARY CONTENT STANDARD":"Complementary Content Standard",
    "COMPLEMENTARY LEARNING STANDARD":"Complementary Learning Standard",
}


def _require_text(value, max_len=18000, *, allow_empty=False):
    if not isinstance(value,str) or len(value)>max_len:
        raise ValueError("Invalid string field")
    if not allow_empty and not value.strip():
        raise ValueError("Empty RPH field")
    if any(ord(c)<9 or (13<ord(c)<32) for c in value):
        raise ValueError("Unprintable field")
    return value


def _metadata_dict(layout):
    rows=layout.get("header")
    if not isinstance(rows,list) or not 16<=len(rows)<=22:
        raise ValueError("Invalid RPH metadata")
    meta={}
    for item in rows:
        if not isinstance(item,dict) or set(item)!={"label","value"}:
            raise ValueError("Invalid metadata item")
        label=_require_text(item["label"],80).strip()
        value=_require_text(item["value"],12000,allow_empty=True)
        if label in meta:
            raise ValueError("Duplicate metadata")
        meta[label]=value
    return meta


def _extract(meta,*names):
    for name in names:
        if name in meta and meta[name].strip() not in ("","—"):
            return meta[name].strip()
    return ""


def build_native_input(payload):
    """Map verified Web layout to Telegram RPH parser + trusted session state.

    The source itself is chosen on Web via verified_preview() and paid
    entitlement; this private endpoint only renders, never chooses a source.
    """
    legacy_keys={"subject","component","year","lesson","unit","teacher","layout","format"}
    if not isinstance(payload,dict) or set(payload) - {"source_digest", "source_variant"} != legacy_keys:
        raise ValueError("Unexpected RPH input")
    subject=payload["subject"]
    component=payload["component"]
    if subject=="PJPK":
        if component not in ("PJ","PK"):
            raise ValueError("Missing PJPK component")
    elif component is not None:
        raise ValueError("Unexpected component")
    year=payload["year"]
    lesson=payload["lesson"]
    unit=payload["unit"]
    teacher=payload["teacher"]
    fmt=payload["format"]
    if subject not in SUBJECTS or type(year) is not int or not 1<=year<=6:
        raise ValueError("Invalid subject/year")
    if year == 1:
        from web.english_y1_kssr_rph import PLANS, UNIT
        if subject != "ENGLISH" or type(lesson) is not int or lesson not in PLANS or unit != UNIT:
            raise ValueError("English Year 1 Lesson not released")
    if type(lesson) is not int or not 1<=lesson<=200:
        raise ValueError("Invalid lesson")
    # Web and Telegram deploy independently. A live Web must not render a
    # stale lesson when the Telegram source/mapping was updated.
    source_digest=payload.get("source_digest")
    variant=payload.get("source_variant")
    moral_plan=None
    if "source_variant" in payload:
        from web.moral_rpt_rph_source import VARIANT, load_plan
        if subject != "MORAL" or variant != VARIANT:
            raise ValueError("Invalid Moral source variant")
        moral_plan=load_plan(year,lesson)
        if moral_plan is None or moral_plan["unit"] != unit:
            raise ValueError("Moral RPT session does not match")
    require_parity=os.environ.get("CIKGULAJU_WEB_RPH_SOURCE_PARITY_REQUIRED")=="1"
    if source_digest is not None or require_parity or year == 1 or moral_plan:
        if not isinstance(source_digest,str) or not re.fullmatch(r"[a-f0-9]{64}",source_digest):
            raise ValueError("Missing source identity")
        from web.rph_shared_source_identity import source_fingerprint
        expected=source_fingerprint(year,subject,lesson,component,variant=variant)
        if expected is None or not hmac.compare_digest(expected,source_digest):
            raise ValueError("Web/Telegram RPH source mismatch")
    if not isinstance(unit,str) or not 0<len(unit)<=300:
        raise ValueError("Invalid unit")
    if fmt not in MIMES:
        raise ValueError("Invalid requested format")
    # Legacy clients send class/date/time. New Web adds an optional pupil
    # count; keep old requests valid while validating the new value strictly.
    if not valid_teacher_fields(teacher, legacy=True):
        raise ValueError("Invalid teacher fields")
    cls=_require_text(teacher["class"],40,allow_empty=True).strip()
    dt=_require_text(teacher["date"],10,allow_empty=True).strip()
    tm=_require_text(teacher["time"],40,allow_empty=True).strip()
    students=_require_text(teacher.get("students",""),3,allow_empty=True).strip()
    if students:
        if not re.fullmatch(r"[1-9][0-9]{0,2}",students) or not 1<=int(students)<=200:
            raise ValueError("Invalid number of pupils")
    if cls and not re.fullmatch(r"[\w .\-/()]+",cls):
        raise ValueError("Invalid class")
    if dt:
        if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}",dt):
            raise ValueError("Invalid date")
        day=date.fromisoformat(dt)
        if not 2025<=day.year<=2031:
            raise ValueError("Unsupported date")
    else:
        day=None
    if tm:
        for part in re.split(r"\s*-\s*",tm):
            if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d",part):
                raise ValueError("Invalid time")
    layout=payload["layout"]
    if not isinstance(layout,dict) or layout.get("style")!=LAYOUT_STYLE:
        raise ValueError("Native renderer layout required")
    meta=_metadata_dict(layout)
    phases=layout.get("phases")
    footer=layout.get("footer")
    if not isinstance(phases,list) or len(phases)!=3 or not isinstance(footer,list) or len(footer)!=2:
        raise ValueError("Incomplete Telegram layout")
    for part in phases:
        if not isinstance(part,dict) or set(part)!={"label","activity","notes"}:
            raise ValueError("Invalid phase")
        _require_text(part["activity"],18000,allow_empty=True)
        _require_text(part["label"],100)
        _require_text(part["notes"],2000,allow_empty=True)
    for part in footer:
        if not isinstance(part,dict) or set(part)!={"label","value"}:
            raise ValueError("Invalid reflection")
        _require_text(part["value"],12000,allow_empty=True)
    if phases[1]["activity"].strip() in ("","—"):
        raise ValueError("No lesson-specific main activity")
    if layout.get("activity_header") != (
        ["Phase / Time","Teaching and Learning Activities","Notes"] if subject=="ENGLISH" else
        ["Fasa / Masa","Aktiviti Pengajaran & Pembelajaran","Catatan"]):
        raise ValueError("Phase headings don't match subject")
    labels={
        "OBJEKTIF PEMBELAJARAN":_extract(meta,*HEADINGS["OBJEKTIF PEMBELAJARAN"]),
        "KRITERIA KEJAYAAN":_extract(meta,*HEADINGS["KRITERIA KEJAYAAN"]),
        "PENGETAHUAN SEDIA ADA":_extract(meta,*HEADINGS["PENGETAHUAN SEDIA ADA"]),
        "BAHAN BANTU MENGAJAR":_extract(meta,*HEADINGS["BAHAN BANTU MENGAJAR"]),
        "EMK / NILAI":_extract(meta,*HEADINGS["EMK / NILAI"]),
        "KBAT / PAK21":_extract(meta,*HEADINGS["KBAT / PAK21"]),
        "PENTAKSIRAN":_extract(meta,*HEADINGS["PENTAKSIRAN"]),
    }
    if subject=="ENGLISH":
        labels["STANDARD KANDUNGAN"]=_extract(meta,"Main Content Standard")
        labels["STANDARD PEMBELAJARAN"]=_extract(meta,"Main Learning Standard")
    else:
        labels["STANDARD KANDUNGAN"]=_extract(meta,"Standard Kandungan")
        labels["STANDARD PEMBELAJARAN"]=_extract(meta,"Standard Pembelajaran")
    labels["SET INDUKSI"]=phases[0]["activity"]
    labels["AKTIVITI UTAMA"]=phases[1]["activity"]
    labels["PENUTUP"]=phases[2]["activity"]
    labels["PEMULIHAN / PENGAYAAN"]=footer[0]["value"]
    labels["REFLEKSI"]=footer[1]["value"]
    # This string is consumed by the Telegram RPH parser, not by a second
    # Web document writer. Each heading is generated server-side and closed.
    ai_text="\n".join(name+":\n"+value+"\n" for name,value in labels.items())
    s={
        "task":"rph","subject":("Pendidikan Jasmani" if component=="PJ" else "Pendidikan Kesihatan" if component=="PK" else SUBJECTS[subject]),
        "year":("Year " if subject=="ENGLISH" else "Tahun ")+str(year),
        "year_label":("Year " if subject=="ENGLISH" else "Tahun ")+str(year),
        "topic":_extract(meta,"Topic","Tajuk") or unit,
        "subtopic":"",
        "lesson_no":lesson,"textbook_lesson_no":lesson,"lesson":lesson,
        "rph_class":cls,"rph_date":dt,"rph_time":tm,
        "rph_day":((
            ("Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday")
            if subject=="ENGLISH" else
            ("Isnin","Selasa","Rabu","Khamis","Jumaat","Sabtu","Ahad")
        )[day.weekday()] if day else ""),
        "rph_students":students,
        "rph_teacher_reflection":clean_reflection(teacher.get("reflection","")),
    }
    # These are the exact selection markers set by Telegram callbacks. The
    # PJPK/PSV native row adapters otherwise silently return the older generic
    # document even though a source file exists on both servers.
    if year == 1:
        s["_web_english_y1_kssr_lesson"] = lesson
    if subject=="PJPK":
        from web.pjpk_2027_preview_runtime import _source
        selected=_source(year,component.lower(),lesson)
        if selected is None:
            raise ValueError("PJPK source not available in Telegram")
        s.update({
            "task":"quick_material","quick_material_flow":True,
            "assessment_mode":"formative","rph_mode":"fast_rpt",
            "pdp_no":lesson,"topic":selected["title"],
            "unit":selected["title"],"unit_title":selected["title"],
            "sk_code":selected["sk"][0],"sp_code":selected["sp"][0],
            "selected_sk":selected["sk"][0],"selected_sp":selected["sp"][0],
            "selected_sk_codes":list(selected["sk"]),"selected_sp_codes":list(selected["sp"]),
            "grouped_sk_codes":list(selected["sk"]),"grouped_sp_codes":list(selected["sp"]),
            "quick_content_v2391":selected["title"],
            "_pjpk_2027_preview_selection":{
                "year":year,"subject":component.lower(),"lesson":lesson},
        })
    elif subject=="PSV":
        from web.psv_2027_provisional_runtime import _lesson,SESSION_KEY,SUBJECT
        selected=_lesson(year,lesson)
        if selected is None:
            raise ValueError("PSV source not available in Telegram")
        sk=selected["sk"].split("; ")
        sp=selected["sp"].split("; ")
        s.update({
            "subject":SUBJECT,"task":"quick_material","quick_material_flow":True,
            "assessment_mode":"formative","rph_mode":"fast_rpt",
            "pdp_no":lesson,"topic":selected["title"],
            "unit":selected["title"],"unit_title":selected["title"],
            "sk_code":sk[0],"sp_code":sp[0],
            "selected_sk":sk[0],"selected_sp":sp[0],
            "selected_sk_codes":sk,"selected_sp_codes":sp,
            "grouped_sk_codes":sk,"grouped_sp_codes":sp,
            "quick_content_v2391":selected["title"],
            SESSION_KEY:{"year":year,"number":lesson,"subject":SUBJECT},
        })
    if moral_plan:
        from web.moral_rpt_rph_source import STATE_KEY
        s.update({STATE_KEY: lesson, "topic": moral_plan["title"], "pdp_no":lesson})
    return s,ai_text,fmt


def compact_web_word_notes(document):
    """Resize only Notes in native Telegram RPH Word; preserve all document content."""
    from lxml import etree
    ns='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    w=lambda tag:'{'+ns+'}'+tag
    with ZipFile(io.BytesIO(document)) as archive:
        root=etree.fromstring(archive.read('word/document.xml'))
        body=root.find(w('body'))
        tables=body.findall(w('tbl')) if body is not None else []
        if len(tables)!=3:
            raise ValueError('Expected 3 native RPH tables')
        activity=tables[1]
        # Keep native column widths when the source supplies teaching notes.
        for row in activity.findall(w('tr'))[1:]:
            cells=row.findall(w('tc'))
            if len(cells)==3 and any((t.text or '').strip() for t in cells[2].iter(w('t'))):
                return document
        grid=activity.find(w('tblGrid'))
        columns=grid.findall(w('gridCol')) if grid is not None else []
        if len(columns)!=3:
            raise ValueError('Expected 3 native activity columns')
        widths=(1500,8250,880)
        for col,width in zip(columns,widths):
            col.set(w('w'),str(width))
        for row in activity.findall(w('tr')):
            cells=row.findall(w('tc'))
            if len(cells)!=3:
                raise ValueError('Unexpected merged native RPH columns')
            for cell,width in zip(cells,widths):
                props=cell.find(w('tcPr'))
                if props is None:
                    props=etree.Element(w('tcPr'));cell.insert(0,props)
                tcw=props.find(w('tcW'))
                if tcw is None:
                    tcw=etree.SubElement(props,w('tcW'))
                tcw.set(w('w'),str(width));tcw.set(w('type'),'dxa')
        updated=etree.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
        output=io.BytesIO()
        with ZipFile(output,'w') as dest:
            for item in archive.infolist():
                dest.writestr(item,updated if item.filename=='word/document.xml' else archive.read(item.filename))
    return output.getvalue()

def _authorized():
    if os.environ.get("CIKGULAJU_WEB_NATIVE_RPH_ENABLED")!="1":
        return False,503
    token=os.environ.get("CIKGULAJU_AUTHORITATIVE_API_TOKEN","")
    header=request.headers.get("Authorization","")
    if len(token)<MIN_LENGTH or not hmac.compare_digest(header,"Bearer "+token):
        return False,401
    return True,200


def create_native_rph_blueprint(runtime):
    """Register a separate protected endpoint on existing Telegram Flask app."""
    if not callable(getattr(runtime,"create_word_file",None)) or not callable(getattr(runtime,"create_pdf_file",None)):
        raise TypeError("Native Telegram document engine is not available")
    bp=Blueprint("telegram_native_rph_download",__name__)

    @bp.after_request
    def private_headers(response):
        response.headers["Cache-Control"]="no-store, private"
        response.headers["Vary"]="Authorization"
        response.headers["X-Content-Type-Options"]="nosniff"
        return response

    @bp.post("/internal/rph/v1/english-integrated")
    def english_integrated():
        allowed, status = _authorized()
        if not allowed:
            return jsonify({"error": "Unauthorized renderer"}), status
        from web import english_integrated_rph_2027 as integrated
        if not integrated.enabled():
            return jsonify({"error": "Integrated English review disabled"}), 503
        if not request.is_json or not 0 < (request.content_length or 0) <= 7000:
            return jsonify({"error": "Invalid English RPH request"}), 400
        body = request.get_json(silent=True)
        try:
            if not isinstance(body, dict) or set(body) != {"year", "lesson", "unit", "teacher", "format"}:
                raise ValueError("Invalid English RPH request")
            year, number, unit = (body[k] for k in ("year", "lesson", "unit"))
            if type(year) is not int or not 2 <= year <= 6 or type(number) is not int or not 1 <= number <= 160:
                raise ValueError("Invalid English source")
            unit = _require_text(unit, 300)
            fmt = body["format"]
            if fmt not in ("word", "pdf", "metadata", "pbd"):
                raise ValueError("Invalid format")
            from web.telegram_verified_rpt_rph_bridge import _teacher_metadata
            teacher = body["teacher"]
            cls, raw_date, raw_time, pupils, _ = _teacher_metadata(teacher, "ENGLISH")
            times = re.split(r"\s*-\s*", raw_time)
            if (not raw_date or date.fromisoformat(raw_date).year != 2027
                    or len(times) != 2 or not integrated.one_hour(*times)):
                raise ValueError("Integrated RPH requires a 60-minute slot in 2027")
        except (ValueError, TypeError, KeyError):
            return jsonify({"error": "Invalid English RPH request"}), 400
        try:
            pair = integrated.plan_for_selection(year, number, unit)
            if pair is None:
                return jsonify({"error": "Paired English RPH unavailable"}), 404
            if not integrated.sources_available(year, pair):
                return jsonify({"error": "Audited English Year 5 RPH sources unavailable"}), 503
            if fmt == "metadata":
                return jsonify({"lessons": list(pair)})
            if fmt == "pbd":
                return jsonify(integrated.pbd_context(year, number))
            data = integrated.render(year, number, fmt, {
                "class": cls, "date": raw_date, "time": raw_time, "students": pupils,
                "reflection": clean_reflection(teacher.get("reflection", "")),
            })
            response = Response(data, mimetype=MIMES[fmt])
            response.headers["Content-Disposition"] = (
                f'attachment; filename="{integrated.filename(year, pair, fmt)}"'
            )
            return response
        except (KeyError, OSError, ValueError):
            return jsonify({"error": "Paired English RPH source unavailable"}), 503

    def aligned_dlp(year, subject):
        if type(year) is not int or subject not in ("MATH_DLP", "SCIENCE_DLP"):
            return None
        if year == 5:
            from staging.dlp.year5 import downloads
            return downloads.MATHEMATICS if subject == "MATH_DLP" else downloads.SCIENCE
        if year == 6:
            from staging.dlp.year6 import render_mathematics, render_science
            return render_mathematics if subject == "MATH_DLP" else render_science
        return None

    def dlp_selection(selection):
        from dlp_year2_rph import resolve

        if not isinstance(selection, dict) or set(selection) != {"year", "subject", "unit", "lesson"}:
            raise ValueError("Invalid DLP selection")
        year, subject, unit, lesson = (selection[key] for key in ("year", "subject", "unit", "lesson"))
        if any(not isinstance(value, str) or len(value) > 40 for value in (subject, unit, lesson)):
            raise ValueError("Invalid DLP selection")
        renderer = aligned_dlp(year, subject)
        if renderer is None:
            return resolve(year, subject, unit, lesson)
        try:
            return renderer.resolve_download(unit, lesson)
        except (OSError, ValueError) as exc:
            raise RuntimeError("DLP curriculum source unavailable") from exc

    @bp.get("/internal/rph/v1/dlp/year<int:year>-<subject_slug>/catalogue")
    def aligned_dlp_catalogue(year, subject_slug):
        allowed, status = _authorized()
        if not allowed:
            return jsonify({"error": "Unauthorized renderer"}), status
        if request.args:
            return jsonify({"error": "Invalid DLP catalogue query"}), 400
        subject = {"mathematics": "MATH_DLP", "science": "SCIENCE_DLP"}.get(subject_slug)
        renderer = aligned_dlp(year, subject)
        if renderer is None:
            return jsonify({"error": "DLP catalogue unavailable"}), 404
        try:
            return jsonify({"year": year, "subject": subject, "units": renderer.download_catalogue()})
        except (OSError, ValueError):
            return jsonify({"error": "DLP curriculum source unavailable"}), 503

    @bp.get("/internal/rph/v1/dlp/availability")
    def dlp_availability():
        allowed, status = _authorized()
        if not allowed:
            return jsonify({"error": "Unauthorized renderer"}), status
        try:
            if any(len(values) != 1 for _, values in request.args.lists()):
                raise ValueError("Ambiguous DLP selection")
            selection = request.args.to_dict()
            selection["year"] = int(selection.get("year", ""))
            plan = dlp_selection(selection)
        except ValueError:
            return jsonify({"error": "Invalid DLP selection"}), 400
        except RuntimeError:
            return jsonify({"error": "DLP curriculum source unavailable"}), 503
        if plan is None:
            return jsonify({"available": False}), 404
        return jsonify({"available": True, "formats": ["word", "pdf"]})

    @bp.post("/internal/rph/v1/dlp/render")
    def dlp_render():
        from flask import current_app
        from dlp_year2_rph import filename, render as render_dlp

        allowed, status = _authorized()
        if not allowed:
            return jsonify({"error": "Unauthorized renderer"}), status
        if not request.is_json or not 0 < (request.content_length or 0) <= 7000:
            return jsonify({"error": "Invalid render body"}), 400
        body = request.get_json(silent=True)
        try:
            if not isinstance(body, dict) or set(body) != {"selection", "teacher", "format"}:
                raise ValueError("Invalid render body")
            fmt = body["format"]
            if not isinstance(fmt, str) or fmt not in MIMES:
                raise ValueError("Invalid format")
            plan = dlp_selection(body["selection"])
            teacher = body["teacher"]
            if not valid_teacher_fields(teacher):
                raise ValueError("Invalid teacher fields")
            limits = {"class": 40, "date": 10, "time": 13, "students": 3}
            teacher = {key: _require_text(teacher[key], limit, allow_empty=True)
                       for key, limit in limits.items()} | {
                           "reflection": clean_reflection(teacher.get("reflection", "")),
                       }
            if any(not teacher[key].isprintable() for key in limits if teacher[key]):
                raise ValueError("Invalid teacher fields")
        except ValueError:
            return jsonify({"error": "Invalid DLP render request"}), 400
        except RuntimeError:
            return jsonify({"error": "DLP curriculum source unavailable"}), 503
        if plan is None:
            return jsonify({"error": "DLP lesson unavailable"}), 404
        unit, lesson = plan
        try:
            selection = body["selection"]
            renderer = aligned_dlp(selection["year"], selection["subject"])
            if renderer:
                document = renderer.render_download(lesson, fmt, teacher)
            else:
                document = render_dlp(selection["subject"], unit, lesson, fmt, teacher)
            response = Response(document, mimetype=MIMES[fmt])
            response.headers["Content-Disposition"] = f'attachment; filename="{filename(lesson["id"], fmt)}"'
            return response
        except Exception:
            current_app.logger.exception("DLP document generation failed for %s", lesson["id"])
            return jsonify({"error": "DLP document generation unavailable"}), 503

    @bp.get("/internal/rph/v1/matematik-sjkt-t2/review")
    @bp.get("/internal/rph/v1/matematik-sjkt-t2/review/<int:unit>")
    @bp.route("/internal/rph/v1/matematik-sjkt-t2/review/<int:unit>/<int:pdp>/<fmt>",
              methods=("GET", "POST"))
    def matematik_sjkt_t2_review(unit=None, pdp=None, fmt=None):
        from flask import current_app
        from audits.matematik_sjkt_tahun_2.eksport_rph import teacher_context
        from web.matematik_sjkt_t2_review import (
            FORMATS, RENDER_ERRORS, UNIT_NAMES, options, render, resolve,
        )

        allowed, status = _authorized()
        if not allowed:
            return jsonify({"error": "Unauthorized renderer"}), status
        if request.args:
            return jsonify({"error": "Invalid review selection"}), 400
        if ((unit is not None and not 1 <= unit <= len(UNIT_NAMES))
                or (fmt is not None and fmt not in FORMATS)):
            return jsonify({"error": "Matematik SJKT selection unavailable"}), 404
        teacher = None
        if request.method == "POST":
            if not request.is_json or not 0 < (request.content_length or 0) <= 7000:
                return jsonify({"error": "Butiran guru tidak sah"}), 400
            teacher = request.get_json(silent=True)
            try:
                if teacher is None:
                    raise ValueError("Missing teacher fields")
                teacher_context(teacher)
            except ValueError:
                return jsonify({"error": "Butiran guru tidak sah"}), 400
        try:
            if pdp is None:
                return jsonify(options(unit))
            if resolve(unit, pdp) is None:
                return jsonify({"error": "Matematik SJKT PdP unavailable"}), 404
            name, document = render(unit, pdp, FORMATS[fmt], teacher)
            response = Response(document, mimetype=MIMES[fmt])
            response.headers["Content-Disposition"] = f'attachment; filename="{name}"'
            return response
        except RENDER_ERRORS:
            current_app.logger.exception("Matematik SJKT review source unavailable")
            return jsonify({"error": "Matematik SJKT review source unavailable"}), 503

    @bp.get("/internal/rph/v1/matematik-sjkt-t2/options")
    def matematik_sjkt_options():
        from flask import current_app
        from web import matematik_sjkt_t2_release as sjkt
        from web.matematik_sjkt_t2_review import RENDER_ERRORS

        allowed, status = _authorized()
        if not allowed:
            return jsonify({"error": "Unauthorized renderer"}), status
        if not sjkt.enabled():
            return jsonify({"error": "Matematik SJKT unavailable"}), 404
        keys = set(request.args)
        if (keys not in ({"year"}, {"year", "unit"}, {"year", "unit", "pdp"})
                or any(len(values) != 1 for _, values in request.args.lists())
                or any(not re.fullmatch(r"[1-9][0-9]?", value) for value in request.args.values())):
            return jsonify({"error": "Invalid Matematik SJKT selection"}), 400
        unit = int(request.args["unit"]) if "unit" in keys else None
        if request.args["year"] != str(sjkt.YEAR) or unit is not None and not 1 <= unit <= len(sjkt.UNIT_NAMES):
            return jsonify({"error": "Matematik SJKT unavailable"}), 404
        try:
            if "pdp" in keys:
                available = sjkt.resolve(unit, int(request.args["pdp"])) is not None
                return jsonify({"available": available}), 200 if available else 404
            if unit is None:
                return jsonify([{"value": str(number), "label": f"Unit {number} · {label}"}
                                for number, label in sjkt.units()])
            return jsonify([{
                "value": str(row["pdp"]), "label": f"PdP {row['pdp']:03} · {row['topic']}",
                "lesson_no": row["pdp"],
                "textbook_ref": f"BT {row['buku_teks']} · BA {row['buku_aktiviti']}",
            } for row in sjkt.lessons() if row["unit_number"] == unit])
        except RENDER_ERRORS:
            current_app.logger.exception("Matematik SJKT catalogue unavailable")
            return jsonify({"error": "Matematik SJKT unavailable"}), 503

    @bp.post("/internal/rph/v1/matematik-sjkt-t2/render")
    def matematik_sjkt_render():
        from flask import current_app
        from audits.matematik_sjkt_tahun_2.eksport_rph import teacher_context
        from web import matematik_sjkt_t2_release as sjkt
        from web.matematik_sjkt_t2_review import RENDER_ERRORS

        allowed, status = _authorized()
        if not allowed:
            return jsonify({"error": "Unauthorized renderer"}), status
        if not sjkt.enabled():
            return jsonify({"error": "Matematik SJKT unavailable"}), 404
        body = request.get_json(silent=True) if 0 < (request.content_length or 0) <= 7000 else None
        if (not isinstance(body, dict) or set(body) != {"year", "unit", "pdp", "format", "teacher"}
                or any(type(body[key]) is not int for key in ("year", "unit", "pdp"))
                or not isinstance(body["format"], str) or body["format"] not in MIMES
                or not isinstance(body["teacher"], dict)):
            return jsonify({"error": "Invalid Matematik SJKT selection"}), 400
        try:
            teacher_context(body["teacher"])
        except ValueError:
            return jsonify({"error": "Invalid teacher fields"}), 400
        if body["year"] != sjkt.YEAR:
            return jsonify({"error": "Matematik SJKT unavailable"}), 404
        try:
            row = sjkt.resolve(body["unit"], body["pdp"])
            if row is None:
                return jsonify({"error": "Matematik SJKT PdP unavailable"}), 404
            fmt = body["format"]
            name, document = sjkt.render(row, fmt, body["teacher"])
            response = Response(document, mimetype=MIMES[fmt])
            response.headers["Content-Disposition"] = f'attachment; filename="{name}"'
            return response
        except RENDER_ERRORS:
            current_app.logger.exception("Matematik SJKT RPH unavailable")
            return jsonify({"error": "Matematik SJKT RPH unavailable"}), 503

    def _matematik_sjkc_source(year):
        from staging.matematik_sjkc.tahun_2 import rph as year_two
        from staging.matematik_sjkc.tahun_3 import rph as year_three

        return {"2": year_two, "3": year_three}.get(str(year))

    @bp.get("/internal/rph/v1/matematik-sjkc/options")
    def matematik_sjkc_options():
        allowed, status = _authorized()
        if not allowed:
            return jsonify({"error": "Unauthorized renderer"}), status
        keys = set(request.args)
        if (keys not in ({"year"}, {"year", "unit"}, {"year", "unit", "pdp"})
                or any(len(values) != 1 for _, values in request.args.lists())):
            return jsonify({"error": "Invalid Matematik SJKC selection"}), 400
        source = _matematik_sjkc_source(request.args["year"])
        if source is None or not source.enabled():
            return jsonify({"error": "Matematik SJKC unavailable"}), 404
        if any(not re.fullmatch(r"[1-9][0-9]?", request.args[key]) for key in keys - {"year"}):
            return jsonify({"error": "Invalid Matematik SJKC selection"}), 400
        unit = int(request.args["unit"]) if "unit" in keys else None
        pdp = int(request.args["pdp"]) if "pdp" in keys else None
        try:
            unit_rows = source.units()
        except (OSError, ValueError, KeyError, TypeError):
            from flask import current_app

            current_app.logger.exception("Matematik SJKC RPH catalog failed")
            return jsonify({"error": "Matematik SJKC unavailable"}), 503
        if (unit is not None and not 1 <= unit <= len(unit_rows)
                or pdp is not None and not 1 <= pdp <= source.PDP_COUNT):
            return jsonify({"error": "Matematik SJKC lesson unavailable"}), 404
        if pdp is not None:
            return (jsonify({"available": True}) if source.resolve(unit, pdp) else
                    (jsonify({"available": False}), 404))
        if unit is None:
            return jsonify([{"value": str(number), "label": f"Unit {number} · {title}"}
                            for number, title in unit_rows])
        return jsonify([{"value": str(row["pdp"]),
                         "label": f"PdP {row['pdp']:03} · {row['topic']}",
                         "lesson_no": row["pdp"],
                         "textbook_ref": f"BT J{row['textbook_volume']} m.s. {row['textbook_pages']}"}
                        for row in source.lessons() if row["unit_number"] == unit])

    @bp.post("/internal/rph/v1/matematik-sjkc/render")
    def matematik_sjkc_render():
        return _matematik_sjkc_document(release=True)

    @bp.post("/internal/rph/v1/matematik-sjkc/preview")
    def matematik_sjkc_preview():
        return _matematik_sjkc_document()

    def _matematik_sjkc_document(*, release=False):
        from flask import current_app
        from pypdf.errors import PdfReadError
        from zipfile import BadZipFile

        allowed, status = _authorized()
        if not allowed:
            return jsonify({"error": "Unauthorized renderer"}), status
        keys = {"year", "unit", "pdp", "format"}
        if release:
            keys.add("teacher")
        if not request.is_json or not 0 < (request.content_length or 0) <= 7000:
            return jsonify({"error": "Invalid render body"}), 400
        body = request.get_json(silent=True)
        if (not isinstance(body, dict) or set(body) != keys or
                any(type(body[key]) is not int for key in ("year", "unit", "pdp")) or
                not isinstance(body["format"], str) or body["format"] not in MIMES):
            return jsonify({"error": "Invalid Matematik SJKC selection"}), 400
        source = _matematik_sjkc_source(body["year"])
        if source is None or (release and not source.enabled()) or (not release and source.YEAR != 3):
            return jsonify({"error": "Matematik SJKC lesson unavailable"}), 404
        teacher = None
        if release:
            try:
                teacher = body["teacher"]
                if not valid_teacher_fields(teacher):
                    raise ValueError("Invalid teacher fields")
                limits = {"class": 40, "date": 10, "time": 13, "students": 3}
                teacher = {key: _require_text(teacher[key], limit, allow_empty=True)
                           for key, limit in limits.items()} | {
                               "reflection": clean_reflection(teacher.get("reflection", "")),
                           }
                if any(not teacher[key].isprintable() for key in limits if teacher[key]):
                    raise ValueError("Invalid teacher fields")
            except ValueError:
                return jsonify({"error": "Invalid teacher fields"}), 400
        try:
            lesson = source.resolve(body["unit"], body["pdp"])
            if lesson is None:
                return jsonify({"error": "Matematik SJKC lesson unavailable"}), 404
            name, document = source.render(lesson, body["format"], teacher)
            response = Response(document, mimetype=MIMES[body["format"]])
            response.headers["Content-Disposition"] = f'attachment; filename="{name}"'
            return response
        except (OSError, ValueError, KeyError, BadZipFile, PdfReadError):
            current_app.logger.exception("Matematik SJKC RPH generation failed")
            return jsonify({"error": "Matematik SJKC RPH unavailable"}), 503

    @bp.post("/internal/rph/v1/render")
    def render():
        allowed,status=_authorized()
        if not allowed:
            return jsonify({"error":"Unauthorized renderer"}),status
        if not request.is_json or request.content_length is None or request.content_length>MAX_BODY:
            return jsonify({"error":"Invalid render body"}),400
        body=request.get_json(silent=True)
        try:
            state,rph_text,fmt=build_native_input(body)
        except (ValueError,TypeError,KeyError):
            return jsonify({"error":"Invalid source-backed RPH"}),400
        # A source hash alone is not enough if the native Telegram overlay is
        # disabled. Refuse a Web-only fallback to generic lesson content.
        if (body["subject"]=="PJPK"
                and not getattr(runtime,"CIKGULAJU_PJPK_2027_PREVIEW_INSTALLED",False)):
            return jsonify({"error":"Telegram PJPK RPH source unavailable"}),503
        if (body["subject"]=="MORAL"
                and not getattr(runtime,"CIKGULAJU_MORAL_80_ACTIVE",False)):
            return jsonify({"error":"Telegram Moral RPH source unavailable"}),503
        if (body["subject"]=="PSV"
                and not getattr(runtime,"PSV_2027_PROVISIONAL_TELEGRAM_ACTIVE",False)):
            return jsonify({"error":"Telegram PSV RPH source unavailable"}),503
        if body["subject"]=="ENGLISH" and body["year"]==5:
            from web.english_y5_standalone_runtime import (
                CHOICE_LESSONS, approved_for_telegram, verified_draft_for_web,
            )
            number = body["lesson"]
            if approved_for_telegram(number):
                available = getattr(runtime, "CIKGULAJU_ENGLISH_Y5_DRAFT_RPH_ACTIVE", False)
            elif number in CHOICE_LESSONS:
                from web.english_y5_teacher_choice_runtime import load_proposal
                available = (getattr(runtime, "CIKGULAJU_ENGLISH_Y5_CHOICE_PROPOSALS_ACTIVE", False)
                             and load_proposal(number) is not None)
            else:
                available = (getattr(runtime, "CIKGULAJU_ENGLISH_Y5_FIXED_DRAFT_PREVIEW_ACTIVE", False)
                             and verified_draft_for_web(number))
            if not available:
                return jsonify({"error":"English Year 5 RPH not approved in Telegram"}),503
        if body["year"] == 1 and not getattr(runtime, "ENGLISH_Y1_KSSR_WEB_ACTIVE", False):
            return jsonify({"error": "English Year 1 renderer unavailable"}), 503
        unique="web"+uuid.uuid4().hex
        output=None
        try:
            if fmt=="word":
                output=runtime.create_word_file(state,rph_text,unique)
            else:
                output=runtime.create_pdf_file(state,rph_text,unique)
            path=Path(output).resolve(strict=True)
            temp=Path(tempfile.gettempdir()).resolve()
            if path.parent!=temp or not path.name.startswith(unique+"_"):
                raise ValueError("Unexpected renderer output path")
            if not path.is_file() or not 1000<=path.stat().st_size<=MAX_RESULT:
                raise ValueError("Renderer output length invalid")
            data=path.read_bytes()
            if fmt=="word":
                data=compact_web_word_notes(data)
            if fmt=="pdf":
                if not data.startswith(b"%PDF-"):
                    raise ValueError("Invalid PDF")
            else:
                if not data.startswith(b"PK\x03\x04"):
                    raise ValueError("Invalid Word")
                with ZipFile(io.BytesIO(data)) as archive:
                    if archive.testzip() or "word/document.xml" not in archive.namelist():
                        raise ValueError("Invalid Word payload")
            response=Response(data,mimetype=MIMES[fmt])
            response.headers["Content-Disposition"]='attachment; filename="CikguLaju_RPH.'+("docx" if fmt=="word" else "pdf")+'"'
            return response
        except Exception:
            return jsonify({"error":"Native Telegram RPH unavailable"}),503
        finally:
            # Document file names use a random prefix, never a user's ID.
            # Do not remove anything outside the temporary directory.
            if isinstance(output,(str,os.PathLike)):
                try:
                    path=Path(output).resolve()
                    if path.parent==Path(tempfile.gettempdir()).resolve() and path.name.startswith(unique+"_"):
                        path.unlink(missing_ok=True)
                except (OSError,ValueError):
                    pass

    return bp
