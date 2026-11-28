"""Read-only curriculum audit of active SK Science years 2–4.
No account, teacher, credential, user DB, document rendering or credit data.
Never infer a missing duration or claim that a legacy sequence is RPT 2027.
"""
import json
import re
from web.telegram_verified_sequence_rph_bridge import (
    _source, _unit_catalog, _available_groups, _resolve,
)
YEARS=(2,3,4)

def snapshot(runtime,year):
    if type(year) is not int or year not in YEARS:
        raise ValueError("Unsupported Science source year")
    rows,units=_source(runtime,year,"SCIENCE")
    results=[]
    seen=set()
    for unit in _unit_catalog(units):
        for cid,group in _available_groups(rows,unit,year,"SCIENCE").items():
            _, selected,mapped=_resolve(runtime,year,"SCIENCE",unit["value"],cid)
            if cid in seen:
                raise ValueError("Duplicate Science identity")
            seen.add(cid)
            titles={str(x.get("pdp_title") or "").strip() for x in selected}
            if len(titles)!=1 or not next(iter(titles)):
                raise ValueError("Ambiguous source title")
            # Only explicitly curriculum-owned fields are returned.
            standards=[{k:str(x.get(k) or "").strip() for k in
                        ("sk_code","sk_text","sp_code","sp_text")} for x in mapped]
            minutes={x.get("dpk_minutes") for x in selected
                     if type(x.get("dpk_minutes")) is int and x["dpk_minutes"] in (30,60)}
            refs=sorted({str(x.get("textbook_ref") or "").strip() for x in selected
                         if x.get("textbook_ref")})
            opening=all(x.get("_sains_opening_lesson") or x.get("_sains_y3_opening_lesson") for x in selected)
            results.append(dict(year=year,unit=unit["value"],unit_title=unit["_unit_title"],
                lesson_id=cid,title=next(iter(titles)),standards=standards,
                source_sequence_no=selected[0].get("source_sequence_no"),
                textbook_refs=refs,minutes=next(iter(minutes)) if len(minutes)==1 else None,
                opening=opening,complete=all(x["sk_code"] and x["sk_text"] and x["sp_code"] and x["sp_text"] for x in standards)))
    return results

def log_read_only(runtime):
    for y in YEARS:
        try:
            rows=snapshot(runtime,y)
            print("CIKGULAJU_SCIENCE_5P_NATIVE_COUNT "+json.dumps(
                {"year":y,"count":len(rows),"opening":sum(x["opening"] for x in rows)},
                ensure_ascii=False),flush=True)
            for i in range(0,len(rows),5):
                print("CIKGULAJU_SCIENCE_5P_NATIVE_IDENTITIES "+json.dumps(
                    {"year":y,"start":i,"total":len(rows),"records":rows[i:i+5]},
                    ensure_ascii=False,separators=(",",":")),flush=True)
        except Exception as exc:
            print("CIKGULAJU_SCIENCE_5P_NATIVE_AUDIT_UNAVAILABLE",y,type(exc).__name__,flush=True)
