"""One-shot, opt-in actual Word/PDF RPH smoke through Telegram's private API.

This is not a teacher-facing endpoint, a curriculum sign-off, or a public
Science release. Calling the existing authenticated private native API with
synthetic teacher details exercises the *real installed Telegram renderer*
without using Web login, Supabase credit accounting or Telegram send_document.
The native API securely deletes its random-name temporary Word/PDF files.
No passwords, bearer token, teacher, or full RPH text are logged.
"""
from __future__ import annotations

from collections import Counter
import io
import json
import os
from zipfile import ZipFile, BadZipFile

ENABLED="CIKGULAJU_SAINS_NATIVE_REAL_DOCS_SMOKE"
TOKEN="CIKGULAJU_AUTHORITATIVE_API_TOKEN"
YEARS=(2,3,4,5,6)
MAX_BYTES=15*1024*1024
MIME={
    "word":"application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pdf":"application/pdf",
}


def _check_doc(fmt,response):
    payload=response.get_data()
    mime=response.headers.get("Content-Type","").split(";",1)[0].strip().lower()
    if response.status_code!=200 or mime!=MIME[fmt]:
        raise ValueError("Invalid native "+fmt+" HTTP/mime: "+str(response.status_code))
    if not 1000<=len(payload)<=MAX_BYTES:
        raise ValueError("Invalid native "+fmt+" file length")
    if "attachment" not in response.headers.get("Content-Disposition",""):
        raise ValueError("No private RPH download header")
    if fmt=="pdf":
        if not payload.startswith(b"%PDF-") or b"%%EOF" not in payload[-1024:]:
            raise ValueError("PDF has invalid format or EOF")
    else:
        if not payload.startswith(b"PK\x03\x04"):
            raise ValueError("Word has invalid PK header")
        try:
            with ZipFile(io.BytesIO(payload)) as zipped:
                if zipped.testzip() is not None or "word/document.xml" not in zipped.namelist():
                    raise ValueError("Word archive missing actual document")
                if not zipped.read("word/document.xml").strip().startswith(b"<?xml"):
                    raise ValueError("Word XML invalid")
        except (BadZipFile,OSError):
            raise ValueError("Corrupt Word archive") from None
    return len(payload)


def check_real_native_api(runtime):
    """Test 5 sample original-DB PdP × actual Word/PDF using Flask test client.

    Internal test client executes the real registered native endpoints; no
    HTTP exposure or dedicated diagnostic user account. Returns only status,
    document sizes and synthetic curriculum IDs. No source bodies or token.
    """
    token=os.environ.get(TOKEN,"")
    if (os.environ.get("CIKGULAJU_WEB_NATIVE_RPH_ENABLED")!="1"
        or not isinstance(token,str) or len(token)<32):
        raise RuntimeError("Telegram private native RPH authentication not configured")
    app=getattr(runtime,"app",None)
    if app is None or not callable(getattr(app,"test_client",None)):
        raise RuntimeError("Flask Telegram native runtime unavailable")
    expected=("telegram_native_sequence_rph.units",
              "telegram_native_sequence_rph.lessons",
              "telegram_native_sequence_rph.availability",
              "telegram_native_sequence_rph.render")
    routes=set(app.view_functions)
    if not set(expected).issubset(routes):
        raise RuntimeError("Native Telegram sequence API not registered")
    client=app.test_client()
    headers={"Authorization":"Bearer "+token}
    result={
        "schema":"native_sains_actual_word_pdf_20261108",
        "mode":"internal_flask_private_api_real_runtime",
        "teacher_identity":"synthetic_only",
        "credits_modified":False,
        "database_modified":False,
        "authoring_342_release_approved":False,
        "five_years_actual_render_passed":False,
        "years":{},
    }
    for year in YEARS:
        status={"year":year,"units_ready":False,"lesson_ready":False,
                "source_available":False,"word_ready":False,"pdf_ready":False}
        stage="units"
        try:
            resp=client.get("/internal/rph/v1/sequence/units",
                  query_string={"year":year,"subject":"SCIENCE"},headers=headers)
            data=resp.get_json(silent=True)
            if (resp.status_code!=200 or not isinstance(data,dict)
                or data.get("source")!="telegram-runtime-v1"
                or not isinstance(data.get("items"),list) or not data["items"]):
                raise ValueError("Native Science unit API returned "+str(resp.status_code))
            status["units_ready"]=True
            selected=None
            for unit in data["items"]:
                if not isinstance(unit,dict) or not isinstance(unit.get("value"),str):
                    continue
                stage="lessons"
                lesson_response=client.get("/internal/rph/v1/sequence/lessons",
                       query_string={"year":year,"subject":"SCIENCE",
                                     "unit":unit["value"]},headers=headers)
                lessons=lesson_response.get_json(silent=True)
                if (lesson_response.status_code==200
                    and isinstance(lessons,dict)
                    and lessons.get("source")=="telegram-runtime-v1"
                    and isinstance(lessons.get("items"),list)
                    and lessons["items"]):
                    selected=unit["value"],lessons["items"][0]["value"]
                    break
            if selected is None:
                raise ValueError("No grouped native Science PdP available")
            unit,code=selected
            if not (isinstance(code,str) and len(code)<101):
                raise ValueError("Invalid native PdP code")
            status["lesson_ready"]=True
            status["sample_pdp"]=code
            stage="availability"
            response=client.get("/internal/rph/v1/sequence/availability",
                 query_string={"year":year,"subject":"SCIENCE",
                               "unit":unit,"lesson":code},headers=headers)
            available=response.get_json(silent=True)
            if response.status_code!=200 or available.get("available") is not True:
                raise ValueError("Native PdP unavailable in active DB")
            status["source_available"]=True
            # Empty teacher metadata, because no real user's account is used.
            body={
                "selection":{"year":year,"subject":"SCIENCE",
                             "unit":unit,"lesson":code},
                "teacher":{"class":"","date":"","time":"","students":""},
            }
            for fmt in ("word","pdf"):
                stage="render_"+fmt
                response=client.post("/internal/rph/v1/sequence/render",
                     json={**body,"format":fmt},headers=headers)
                size=_check_doc(fmt,response)
                status[fmt+"_ready"]=True
                status[fmt+"_size_bytes"]=size
        except Exception as exc:
            # Error type + stage only; RPH text/user info is not logged.
            status["failed_stage"]=stage
            status["failure_type"]=type(exc).__name__
        result["years"][str(year)]=status
    result["five_years_actual_render_passed"]=all(
        x["word_ready"] and x["pdf_ready"] for x in result["years"].values())
    return result


def log_when_enabled(runtime):
    if os.environ.get(ENABLED)!="1":
        return None
    # Do not enable the new 342-RPH draft adapter merely to inspect RPH.
    if bool(getattr(runtime,"CIKGULAJU_SAINS_342_INTERNAL_REVIEW_ACTIVE",False)):
        print("CIKGULAJU_SAINS_NATIVE_REAL_DOCS_SMOKE_BLOCKED draft_adapter_active",flush=True)
        return None
    try:
        result=check_real_native_api(runtime)
        print("CIKGULAJU_SAINS_NATIVE_REAL_DOCS_SMOKE "+
              json.dumps(result,ensure_ascii=False,sort_keys=True),flush=True)
        return result
    except Exception as exc:
        print("CIKGULAJU_SAINS_NATIVE_REAL_DOCS_SMOKE_ERROR "+
              type(exc).__name__,flush=True)
        return None


if __name__=="__main__":
    raise SystemExit("This diagnostic requires the already-running Telegram app, not a new bot")
