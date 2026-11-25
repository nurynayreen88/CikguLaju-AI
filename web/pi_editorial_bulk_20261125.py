"""Bulk PI activity candidate adapter, guarded by exact source identity.
No change to existing database, standards, billing, or templates.
Academic source holds remain on the original runtime content.
"""
from pathlib import Path
from functools import wraps
import json
import os
import re
import unicodedata
from web.rph_pi_jawi_numerals_20261124 import is_active_pi_rph, jawi_display_digits

ROOT=Path(__file__).resolve().parent.parent/"staging"/"pendidikan_islam"
DIGITS=str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹","01234567890123456789")
def norm(value):
    return " ".join(unicodedata.normalize("NFC",str(value or "")).translate(DIGITS).split())

def load_catalog():
    items={}
    for path in sorted(ROOT.glob("active_activity_editorial_batch*_20261125.json")):
        for item in json.loads(path.read_text(encoding="utf8"))["records"]:
            if item["id"] in items:
                raise ValueError("duplicate PI record")
            items[item["id"]]=item
    corrections=json.loads((ROOT/"active_activity_objective_corrections_20261125.json").read_text(encoding="utf8"))["records"]
    for item in corrections:
        items[item["id"]]={**item,"objective":item["original_objective"],"source_note":item["original_source_note"]}
    if len(items)!=698:
        raise ValueError("incomplete PI catalog")
    holds={i["id"] for i in json.loads((ROOT/"active_activity_source_holds_20261125.json").read_text(encoding="utf8"))["records"]}
    holds.update(i["id"] for i in corrections)
    holds.update((1276,1277,1279,1280))
    # Second wave: explicit source-backed corrections; ambiguous sequence and SK changes stay held.
    holds.difference_update((1641,1735,1940,1944,1948,1952,1956,1387,1391,1473,1727,1731,1475,1479,1495,1543,1547,1611,1615,1747,1811,1619))
    # Four remaining Year 2 lessons, original DSKP pp27/45 and textbook pp37/38/56/59.
    holds.difference_update((1276,1277,1279,1280))
    # Final source-verified wave (7); retain two T6 ambiguous recitation ranges.
    holds.difference_update((1445,1533,1669,1599,1627,1751,1815))
    lookup={}
    for item in items.values():
        if item["id"] in holds:
            continue
        if len(item["activities"])!=3 or not all("موريد" in body for title,body in item["activities"]):
            raise ValueError("incomplete activity candidate")
        key=(item["year"],item["pdp"],norm(item["source_note"]),norm(item["objective"]))
        if key in lookup:
            raise ValueError("ambiguous PI candidate")
        lookup[key]=item
    return lookup

def apply(state,rows,catalog):
    if not is_active_pi_rph(state) or not isinstance(rows,dict):
        return rows
    year=re.fullmatch(r"Tahun ([2-6])",norm(state.get("year") or state.get("year_label")))
    if not year:
        return rows
    # Lesson sequence is stable; internal native IDs can be remapped.
    pdp=norm(state.get("pdp_no") or state.get("lesson_no") or state.get("lesson"))
    if not pdp.isdecimal():
        return rows
    notes={norm(state.get("rpt_activity_note"))}
    for name in ("_quick_selected_rpt_row_v2388","quick_rpt_row"):
        master=state.get(name)
        if isinstance(master,dict):
            notes.add(norm(master.get("activity_note")))
            notes.add(norm(master.get("_pi_original_rpt_activity_note_20261125")))
    objective=norm(rows.get("OBJEKTIF PEMBELAJARAN") or rows.get("OBJEKTIF"))
    matches=[catalog[(int(year.group(1)),int(pdp),note,objective)] for note in notes if note and (int(year.group(1)),int(pdp),note,objective) in catalog]
    if not matches:
        # The final document formatter may already contain the corrected objective.
        matches=[item for (y,p,n,o),item in catalog.items() if y==int(year.group(1)) and p==int(pdp) and n in notes and item.get("corrected_objective") and norm(item["corrected_objective"])==objective]
    if len(matches)!=1 or "AKTIVITI UTAMA" not in rows:
        return rows
    item=matches[0]
    updated=dict(rows)
    if item.get("corrected_objective"):
        # Change the displayed objective only for the exact original source match.
        # SK/SP identifiers and source database remain unchanged.
        if item.get("corrected_sk_text"):
            codes=[norm(x) for x in state.get("grouped_sk_codes",[])]
            if codes!=item["sk_codes"] or len(codes)!=1:
                return rows
            code=codes[0]
            known={norm(item["original_sk_text"]),norm(item["corrected_sk_text"])}
            known |= {code+" "+value for value in known}
            sk_keys=[key for key,value in rows.items() if norm(value) in known]
            if len(sk_keys)!=1:
                return rows
            updated[sk_keys[0]]=jawi_display_digits(item["corrected_sk_text"])
        if [norm(x) for x in state.get("grouped_sp_codes",[])] != [norm(x) for x in item.get("sp_codes",[])]:
            return rows
        objective_key="OBJEKTIF PEMBELAJARAN" if "OBJEKTIF PEMBELAJARAN" in rows else "OBJEKTIF"
        updated[objective_key]=jawi_display_digits(item["corrected_objective"])
        if "KRITERIA KEJAYAAN" in rows:
            updated["KRITERIA KEJAYAAN"]=jawi_display_digits(item["corrected_success_criteria"])
        if "REFLEKSI" in rows and not str(state.get("rph_teacher_reflection") or "").strip() and str(state.get("rph_reflection_mode") or "").casefold()!="manual":
            updated["REFLEKSI"]=jawi_display_digits(item["corrected_auto_reflection"])
    updated["AKTIVITI UTAMA"]=jawi_display_digits("\n".join(f"اکتيۏيتي {i} - {title}\n1. {body}" for i,(title,body) in enumerate(item["activities"],1)))
    fields=item.get("final_review_fields")
    if fields:
        proposals=fields.get("sp_text_proposal") or {}
        if proposals:
            codes=[norm(x) for x in state.get("grouped_sp_codes",[])]
            texts=state.get("grouped_sp_texts",[])
            if not set(proposals).issubset(codes) or len(codes)!=len(texts):
                return rows
            # Preserve the exact code sequence; only the verified descriptions change.
            lines=[]
            for code,description in zip(codes,texts):
                description=proposals.get(code,str(description or "").strip())
                if norm(description).startswith(code+" "):
                    lines.append(description)
                else:
                    lines.append(code+" "+description)
            if "STANDARD PEMBELAJARAN" not in rows:
                return rows
            updated["STANDARD PEMBELAJARAN"]=jawi_display_digits("\n".join(lines))
        for key,field in (("KRITERIA KEJAYAAN","criterion"),("PENTAKSIRAN","assessment")):
            if key in rows:
                updated[key]=jawi_display_digits(fields[field])
        if "REFLEKSI" in rows and not str(state.get("rph_teacher_reflection") or "").strip() and str(state.get("rph_reflection_mode") or "").casefold()!="manual":
            updated["REFLEKSI"]=jawi_display_digits("____ / ____ "+fields["reflection"]+" موريد يڠ بلوم مڠواساءي دبمبيڠ سمولا.")
    return updated

def install(runtime):
    # Default disabled until integration tests and release decision are complete.
    if os.getenv("CIKGULAJU_PI_EDITORIAL_BULK","0")!="1":
        return False
    if getattr(runtime,"_CIKGULAJU_PI_EDITORIAL_BULK",False):
        return True
    catalog=load_catalog()
    old=getattr(runtime,"_rph_rows",None)
    if not callable(old):
        return False
    @wraps(old)
    def wrapper(state,*args,**kwargs):
        return apply(state,old(state,*args,**kwargs),catalog)
    runtime._rph_rows=wrapper
    previous_document=getattr(runtime,"_rph_document_rows",None)
    if callable(previous_document):
        @wraps(previous_document)
        def document_wrapper(state,rows,*args,**kwargs):
            result=previous_document(state,rows,*args,**kwargs)
            # A second pass only for the four explicit SP corrections, since the
            # final document formatter can rebuild standards from source state.
            if (norm(state.get("year"))=="Tahun 2" and norm(state.get("pdp_no") or state.get("lesson_no")) in ("2","3","5","6")) or (norm(state.get("year"))=="Tahun 5" and norm(state.get("pdp_no") or state.get("lesson_no")) in ("65","129")):
                return apply(state,result,catalog)
            return result
        runtime._rph_document_rows=document_wrapper
    renderer=getattr(runtime,"_create_rph_word",None)
    globals_=getattr(renderer,"__globals__",None)
    if isinstance(globals_,dict) and globals_ is not vars(runtime) and globals_.get("_rph_rows") is old:
        globals_["_rph_rows"]=wrapper
    if isinstance(globals_,dict) and globals_ is not vars(runtime) and callable(previous_document) and globals_.get("_rph_document_rows") is previous_document:
        globals_["_rph_document_rows"]=runtime._rph_document_rows
    runtime._CIKGULAJU_PI_EDITORIAL_BULK=True
    print("PI editorial bulk candidate count:",len(catalog),flush=True)
    return True
