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
    if not isinstance(payload,dict) or set(payload) not in (
            legacy_keys, legacy_keys | {"source_digest"}):
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
    if subject not in SUBJECTS or type(year) is not int or not 2<=year<=6:
        raise ValueError("Invalid subject/year")
    if type(lesson) is not int or not 1<=lesson<=200:
        raise ValueError("Invalid lesson")
    # Web and Telegram deploy independently. A live Web must not render a
    # stale lesson when the Telegram source/mapping was updated.
    source_digest=payload.get("source_digest")
    require_parity=os.environ.get("CIKGULAJU_WEB_RPH_SOURCE_PARITY_REQUIRED")=="1"
    if source_digest is not None or require_parity:
        if not isinstance(source_digest,str) or not re.fullmatch(r"[a-f0-9]{64}",source_digest):
            raise ValueError("Missing source identity")
        from web.rph_shared_source_identity import source_fingerprint
        expected=source_fingerprint(year,subject,lesson,component)
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
            from web.english_y5_standalone_runtime import approved_for_telegram
            if not (getattr(runtime,"CIKGULAJU_ENGLISH_Y5_DRAFT_RPH_ACTIVE",False)
                    and approved_for_telegram(body["lesson"])):
                return jsonify({"error":"English Year 5 RPH not approved in Telegram"}),503
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
