"""Four source-reviewed PI KSSR T2 activity improvements. Fail closed on source drift.
Native structural evidence: CI 45542565887. No DB, billing, or template edits.
"""
import json
import re
import unicodedata
from pathlib import Path
from functools import wraps
from web.rph_pi_jawi_numerals_20261124 import is_active_pi_rph, jawi_display_digits

RECORDS=json.loads(Path(__file__).with_name("pi_editorial_wave1_20261125.json").read_text(encoding="utf8"))
DIGITS=str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹","01234567890123456789")
def norm(value):
    return " ".join(unicodedata.normalize("NFC",str(value or "")).translate(DIGITS).split())

def apply(state, rows):
    if not is_active_pi_rph(state) or not isinstance(rows,dict):
        return rows
    year=norm(state.get("year") or state.get("year_label"))
    if year!="Tahun 2":
        return rows
    notes=[state.get("rpt_activity_note")]
    for key in ("_quick_selected_rpt_row_v2388","quick_rpt_row"):
        master=state.get(key)
        if isinstance(master,dict):
            notes.append(master.get("activity_note"))
    objective=norm(rows.get("OBJEKTIF PEMBELAJARAN") or rows.get("OBJEKTIF"))
    sp=re.findall(r"(?<![0-9.])[0-9]+\.[0-9]+\.[0-9]+(?![0-9.])",norm(rows.get("STANDARD PEMBELAJARAN")))
    for item in RECORDS:
        if norm(item["source_note"]) not in {norm(n) for n in notes if n}:
            continue
        if objective!=norm(item["objective"]) or sp!=item["sp"]:
            continue
        if not all(k in rows for k in ("AKTIVITI UTAMA","KRITERIA KEJAYAAN","PENTAKSIRAN","REFLEKSI")):
            return rows
        changed=dict(rows)
        changed["AKTIVITI UTAMA"]=jawi_display_digits("\n".join(f"اکتيۏيتي {i} - {title}\n1. {body}" for i,(title,body) in enumerate(item["activities"],1)))
        changed["KRITERIA KEJAYAAN"]=jawi_display_digits(item["criterion"])
        changed["PENTAKSIRAN"]=jawi_display_digits(item["assessment"])
        if not str(state.get("rph_teacher_reflection") or "").strip() and str(state.get("rph_reflection_mode") or "").casefold()!="manual":
            changed["REFLEKSI"]=jawi_display_digits("____ / ____ "+item["reflection"]+" موريد يڠ بلوم مڠواساءي دبمبيڠ سمولا.")
        return changed
    return rows

def install(runtime):
    if getattr(runtime,"_CIKGULAJU_PI_EDITORIAL_WAVE1",False):
        return True
    old=getattr(runtime,"_rph_rows",None)
    if not callable(old):
        return False
    @wraps(old)
    def wrapped(state,*args,**kwargs):
        return apply(state,old(state,*args,**kwargs))
    runtime._rph_rows=wrapped
    renderer=getattr(runtime,"_create_rph_word",None)
    globals_=getattr(renderer,"__globals__",None)
    if isinstance(globals_,dict) and globals_ is not vars(runtime) and globals_.get("_rph_rows") is old:
        globals_["_rph_rows"]=wrapped
    runtime._CIKGULAJU_PI_EDITORIAL_WAVE1=True
    return True
