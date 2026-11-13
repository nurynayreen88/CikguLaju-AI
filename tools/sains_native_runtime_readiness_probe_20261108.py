"""Production-safe read-only startup diagnosis for actual Science Telegram RPH.

Does not activate any draft, generate a user download, write to SQLite/Supabase,
consume a generation credit or require Web login. It probes only one existing
Telegram DB PdP per year to distinguish source/Word row readiness from service
liveness; not a blanket 342-RPH academic or document-generation approval.
"""
from __future__ import annotations

import json
import os

from web.telegram_verified_sequence_rph_bridge import (
    _source, _unit_catalog, _pdp_groups, _build_state, _source_text,
    SourceUnavailable,
)
from web.sains_rph_quality_release_gate_20261108 import approved_count

YEARS=(2,3,4,5,6)


def readiness(runtime):
    result={
        "schema":"sains-native-runtime-20261108",
        "subject":"Sains",
        "year_scope":list(YEARS),
        "primary_db_active":bool(getattr(runtime,"CIKGULAJU_DB_V2600_ACTIVE",False)),
        "native_web_bridge_enabled":os.environ.get("CIKGULAJU_WEB_NATIVE_RPH_ENABLED")=="1",
        "latest_342_review_adapter_active":bool(getattr(
            runtime,"CIKGULAJU_SAINS_342_INTERNAL_REVIEW_ACTIVE",False)),
        "academic_individual_approval_count":0,
        "authoring_new_rph_total":342,
        "opening_unit_pdp_counts":{},
        "years":{},
    }
    try:
        result["academic_individual_approval_count"]=approved_count()
    except (OSError,ValueError,KeyError,TypeError) as exc:
        result["academic_registry_error"]=type(exc).__name__
    for year in (1, *YEARS):
        try:
            rows, _ = _source(runtime, year, "SCIENCE")
        except (ValueError, SourceUnavailable):
            continue
        opening = {}
        for row in rows:
            if row.get("_sains_opening_lesson") or row.get("_sains_y3_opening_lesson"):
                unit = row["unit_title"]
                opening.setdefault(unit, set()).add(row["pdp_sequence_code"])
        result["opening_unit_pdp_counts"][str(year)] = {
            unit: len(codes) for unit, codes in opening.items()
        }
    for year in YEARS:
        status={
            "db_sequence_row_count":0,
            "unique_pdp_count":0,
            "sample_source_text_ready":False,
            "sample_word_pdf_row_builder_ready":False,
            "checked_one_existing_source_only":True,
        }
        try:
            rows, units=_source(runtime,year,"SCIENCE")
            status["db_sequence_row_count"]=len(rows)
            codes={str(r.get("pdp_sequence_code") or "").strip()
                   for r in rows if isinstance(r,dict) and r.get("pdp_sequence_code")}
            status["unique_pdp_count"]=len(codes)
            if not rows or not units:
                raise SourceUnavailable("No DB native Science PdP")
            catalog=_unit_catalog(units)
            if not catalog:
                raise SourceUnavailable("No native Science units")
            choice=None
            for unit in catalog:
                groups=_pdp_groups(rows,unit["_unit_code"],unit["_unit_title"])
                if groups:
                    choice=(unit["value"],next(iter(groups)))
                    break
            if choice is None:
                raise SourceUnavailable("No exact native Science PdP code")
            state=_build_state(
                runtime,year,"SCIENCE",choice[0],choice[1],
                {"class":"","date":"","time":"","students":""})
            text=_source_text(runtime,state)
            if not isinstance(text,str) or len(text)<500:
                raise SourceUnavailable("Science lesson has no sufficient source text")
            status["sample_source_text_ready"]=True
            rows_builder=getattr(runtime,"_rph_rows",None)
            if not callable(rows_builder):
                raise SourceUnavailable("Telegram Word/PDF row builder not installed")
            fields=rows_builder(state,text)
            if not isinstance(fields,dict):
                raise SourceUnavailable("Telegram Word/PDF source rows unavailable")
            required=("AKTIVITI UTAMA","STANDARD PEMBELAJARAN")
            if any(not isinstance(fields.get(k),str) or not fields[k].strip()
                   for k in required):
                raise SourceUnavailable("Telegram Word/PDF missing mandatory Science fields")
            status["sample_word_pdf_row_builder_ready"]=True
        except Exception as exc:
            # Existing Telegram/Web remains unaffected if a source is unavailable.
            status["source_error_type"]=type(exc).__name__
        result["years"][str(year)]=status
    result["all_five_years_sample_ready"]=all(
        x["sample_source_text_ready"] and x["sample_word_pdf_row_builder_ready"]
        for x in result["years"].values())
    result["new_342_academically_ready"]=(
        result["academic_individual_approval_count"]==342
        and result["all_five_years_sample_ready"])
    result["web_telegram_real_download_tested"]=False
    return result


def log_readiness(runtime):
    try:
        status=readiness(runtime)
        print("CIKGULAJU_SAINS_NATIVE_READINESS "+
              json.dumps(status,ensure_ascii=False,sort_keys=True),flush=True)
        return status
    except Exception as exc:
        # Never block production startup for a diagnostics-only module.
        print("CIKGULAJU_SAINS_NATIVE_READINESS_DIAGNOSTIC_FAILED "+
              type(exc).__name__,flush=True)
        return None
