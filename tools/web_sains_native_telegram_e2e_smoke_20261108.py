"""One-shot production Web→Telegram Science PDF/Word network smoke.

No teacher account or Web download URL is invoked. The existing authenticated
server-to-server Web Science native client requests exact PdP/Word/PDF from
Telegram with synthetic empty teacher data, bypassing browser entitlement but
NOT the native source identity/authentication checks. There are no user-credit
or payment writes, and the result includes neither token nor document bytes.
All new 342 authored drafts remain on academic HOLD.
"""
from __future__ import annotations

import json
import os
from zipfile import ZipFile
from io import BytesIO

from web import native_telegram_sequence_rph_client as native

FLAG="CIKGULAJU_SAINS_WEB_REAL_DOWNLOAD_SMOKE"
YEARS=(2,3,4,5,6)
LIMIT_BYTES=15*1024*1024


def _selected(year):
    units=native.list_native_units(year,"SCIENCE")
    if not isinstance(units,list) or not units:
        raise ValueError("No official native Sains units")
    for unit in units:
        if not isinstance(unit,dict) or not isinstance(unit.get("value"),str):
            continue
        lessons=native.list_native_lessons(year,"SCIENCE",unit["value"])
        if not isinstance(lessons,list) or not lessons:
            continue
        first=lessons[0]
        if not isinstance(first,dict) or not isinstance(first.get("value"),str):
            continue
        return unit["value"],first["value"]
    raise ValueError("No original DB Science PdP in native units")


def probe():
    report={
        "schema":"web_sains_telegram_real_word_pdf_20261108",
        "route":"web_native_client_to_live_telegram_https",
        "account_or_credit_required":False,
        "account_or_credit_changed":False,
        "authoring_342_release_approved":False,
        "real_network_word_pdf_all_five_years":False,
        "years":{},
    }
    for year in YEARS:
        result={"year":year,"units_ready":False,"lesson_ready":False,
                "native_available":False,"word_ready":False,"pdf_ready":False}
        stage="catalog"
        try:
            unit,pdp=_selected(year)
            result["units_ready"]=True
            result["lesson_ready"]=True
            result["sample_pdp"]=pdp
            stage="availability"
            if native.verified_native_sequence_available(year,"SCIENCE",unit,pdp) is not True:
                raise ValueError("Native Telegram Science PdP not available")
            result["native_available"]=True
            selection={
                "year":year,"subject":"SCIENCE","unit":unit,"lesson":pdp,
                "source":"telegram-native-pdp-sequence",
                "teacher":{"class":"","date":"","time":"","students":""},
            }
            for fmt in ("word","pdf"):
                stage="download_"+fmt
                document=native.request_native_sequence_rph(selection,fmt)
                if not isinstance(document,BytesIO):
                    raise ValueError("Native Web document is not a byte stream")
                data=document.getvalue()
                if not 1000<=len(data)<=LIMIT_BYTES:
                    raise ValueError("Invalid native Web document bytes")
                if fmt=="pdf":
                    if not data.startswith(b"%PDF-") or b"%%EOF" not in data[-1024:]:
                        raise ValueError("Invalid native Web PDF payload")
                else:
                    with ZipFile(BytesIO(data)) as doc:
                        if doc.testzip() or "word/document.xml" not in doc.namelist():
                            raise ValueError("Native Web Word document corrupt")
                result[fmt+"_ready"]=True
                result[fmt+"_size_bytes"]=len(data)
        except Exception as exc:
            # No exception body: URL paths or auth details must not leak.
            result["failed_stage"]=stage
            result["failure_type"]=type(exc).__name__
        report["years"][str(year)]=result
    report["real_network_word_pdf_all_five_years"]=all(
        row["word_ready"] and row["pdf_ready"]
        for row in report["years"].values())
    return report


def log_when_enabled():
    if os.environ.get(FLAG)!="1":
        return None
    try:
        result=probe()
        print("CIKGULAJU_SAINS_WEB_REAL_DOWNLOAD_SMOKE "+
              json.dumps(result,ensure_ascii=False,sort_keys=True),flush=True)
        return result
    except Exception as exc:
        print("CIKGULAJU_SAINS_WEB_REAL_DOWNLOAD_SMOKE_ERROR "+
              type(exc).__name__,flush=True)
        return None
