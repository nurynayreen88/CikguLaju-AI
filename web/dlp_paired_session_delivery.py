"""Protected DLP session renderer. Disabled unless a verified release is installed.
The original DLP lesson selection/render path is not changed.
"""
from hashlib import sha256
from pathlib import Path
from functools import lru_cache
import json, os, re

ROOT=Path(__file__).resolve().parents[1]/"staging/dlp/paired_release"
SETS={(2,"SCIENCE_DLP"):70,(3,"SCIENCE_DLP"):70,(6,"SCIENCE_DLP"):70}
SETS.update({(y,"MATH_DLP"):101 for y in (3,4,5,6)})
TOKEN=re.compile(r"SESSION-(\d{3})")
@lru_cache(maxsize=7)
def _load(year,subject):
    count=SETS[year,subject]
    manifest=json.loads((ROOT/"manifest.json").read_text())
    entry=manifest["sets"][f"{subject}:{year}"]
    # Explicit owner publication authorization is separate from academic review.
    # The source review status stays unchanged; do not label these academically certified.
    if entry.get("academic_approved") is not True and entry.get("publication_authorized") is not True:
        raise ValueError("DLP publication approval missing")
    raw=(ROOT/f"{subject}_{year}.json").read_bytes()
    if sha256(raw).hexdigest()!=entry["sha256"]:
        raise ValueError("DLP data integrity mismatch")
    rows=json.loads(raw)
    if len(rows)!=count or [r["session"] for r in rows]!=list(range(1,count+1)):
        raise ValueError("DLP incomplete session inventory")
    return rows

def enabled(year,subject):
    key="CIKGULAJU_DLP_PAIRED_MATH_YEARS" if subject=="MATH_DLP" else "CIKGULAJU_DLP_PAIRED_SCIENCE_YEARS"
    return (year,subject) in SETS and str(year) in os.getenv(key,"").split(",")

def resolve(year,subject,unit,lesson):
    if not enabled(year,subject) or unit!="sessions":
        return None
    m=TOKEN.fullmatch(lesson)
    if not m: return None
    n=int(m[1])
    if not 1<=n<=SETS[year,subject]: return None
    return _load(year,subject)[n-1]

def catalogue(year,subject):
    if not enabled(year,subject): return None
    return {"id":"sessions","title":"RPT 2027 sessions","lessons":[
        {"id":f"SESSION-{r['session']:03d}","label":f"Session {r['session']:02d} · Week {r['week']:02d}",
         "title":r["heading"][2],"minutes":r["minutes"],"book_reference":r["references"]}
        for r in _load(year,subject)]}

def render(row,fmt,teacher):
    from dlp_year2_rph import science_class_fields
    from web.rph_unified_engine import render_structured_rph
    fields=science_class_fields(teacher,english=True)
    denominator=teacher.get("students","")
    denominator=denominator if re.fullmatch(r"[1-9]\d{0,2}",denominator) else "___"
    reflection=teacher.get("reflection") or "; ".join(f"Obj. {n}: ___/{denominator}" for n in range(1,row["objectives"]+1))+" pupils achieved. Follow-up: ____________________."
    payload=dict(source="dlp",fmt=fmt,heading=row["heading"],details=[row["details"][0],row["details"][1],*fields,*row["details"][2:]],activities=row["activities"],footer=[("Reflection",reflection)],teacher=teacher,compact=True,mathematics=row["heading"][1].startswith("Mathematics"))
    blob=render_structured_rph(**payload)
    if fmt=="pdf":
        import fitz
        with fitz.open(stream=blob,filetype="pdf") as doc: pages=len(doc)
        if pages>1:
            for density in (1,2,3,4):
                blob=render_structured_rph(**payload,paired_density=density)
                with fitz.open(stream=blob,filetype="pdf") as doc: pages=len(doc)
                if pages==1: break
            if pages!=1: raise ValueError("Paired RPH PDF exceeds one page")
    return blob
