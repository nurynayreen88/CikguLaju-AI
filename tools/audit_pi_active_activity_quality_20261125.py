"""Audit and prepare source-grounded activity candidates, without publishing.
Run against checksum-verified v26 master and the actual active native generator.
No production accounts, DB writes, credit use, or 696 archive.
"""
from collections import Counter, defaultdict
from pathlib import Path
import json
import re
import sqlite3
import unicodedata
from tools.bm_native_v26_navigation_audit import database
from web.pi_jawi_english_terms_20261122 import normalize_english_terms
from web.rph_pi_jawi_numerals_20261124 import jawi_display_digits

MARKER = re.compile(r"(?<!\S)([1-9])\.\s+(?=\S)")
DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")

def normalized(text):
    text = unicodedata.normalize("NFC", str(text or "")).translate(DIGITS)
    return " ".join(text.split())

def source_steps(text):
    text = normalized(normalize_english_terms(text))
    markers = list(MARKER.finditer(text))
    if not 2 <= len(markers) <= 8 or markers[0].start() != 0:
        return []
    if [int(m.group(1)) for m in markers] != list(range(1,len(markers)+1)):
        return []
    steps = [text[m.end():markers[i+1].start() if i+1<len(markers) else len(text)].strip()
             for i,m in enumerate(markers)]
    if any(len(s)<12 or not re.search(r"[\u0600-\u08ff]",s) for s in steps):
        return []
    return steps

def inspect(rows, note):
    main = str(rows.get("AKTIVITI UTAMA") or "")
    all_text = normalized(" ".join(str(x) for x in rows.values()))
    plain_main = normalized(main)
    steps = source_steps(note)
    missing = [i for i,s in enumerate(steps,1) if normalized(s) not in all_text]
    present = [i for i,s in enumerate(steps,1) if normalized(s) in plain_main]
    duplicate = [i for i,s in enumerate(steps,1) if plain_main.count(normalized(s)) > 1]
    return {"main_chars":len(plain_main), "source_steps":len(steps), "missing":missing,
            "present_main":present, "duplicate":duplicate,
            "teacher_explicit":bool(re.search(r"(?:ݢورو|ڬورو|گورو|guru)", main,re.I)),
            "pupil_explicit":bool(re.search(r"(?:موريد|murid)",main,re.I))}

def candidate(rows,note,metrics):
    """QA-only proposal: restore exact missing teaching steps, not generic filler.
    Require at least one complete source step in current main activity, and
    only propose missing full steps (not a blind replacement of existing text).
    A human must review semantic duplication and real A4 output before adoption.
    """
    if not metrics["present_main"] or not metrics["missing"]:
        return None
    steps = source_steps(note)
    additions = [jawi_display_digits(f"{i}. {steps[i-1]}") for i in metrics["missing"]]
    return str(rows["AKTIVITI UTAMA"]).rstrip()+"\n"+"\n".join(additions)

def main():
    from tools import run_telegram_with_curriculum_api as running
    from web.telegram_verified_rpt_rph_bridge import _native_state,_native_text
    from web.pi_navigation import pi_navigation_unit
    runtime=running.telegram_runtime
    tmp,db=database()
    report={"status":"QA_ONLY_NOT_READY","source":"active v26 PI T2–6","years":{},"records":[]}
    examples=defaultdict(list)
    try:
        runtime.DB_PATH=str(db)
        runtime.CIKGULAJU_DB_V2600_ACTIVE=True
        with sqlite3.connect(db.resolve().as_uri()+"?mode=ro",uri=True) as con:
            con.row_factory=sqlite3.Row
            con.execute("PRAGMA query_only=ON")
            assert con.execute("PRAGMA quick_check").fetchone()[0]=="ok"
            source=[dict(r) for r in con.execute("""
                SELECT * FROM rpt_entries WHERE subject='Pendidikan Islam' AND verified=1
                AND year_label IN ('Tahun 2','Tahun 3','Tahun 4','Tahun 5','Tahun 6')
                AND lower(COALESCE(notes,'')) NOT LIKE '%superseded%'
                ORDER BY year_label,sequence_no,id""")]
        teacher={"class":"","date":"","time":"","students":"","reflection":""}
        for row in source:
            year=int(row["year_label"].split()[-1])
            unit=pi_navigation_unit(row)
            key=str(year)
            stats=report["years"].setdefault(key,Counter())
            stats["source"]+=1
            try:
                state=_native_state(runtime,{"year":year,"subject":"PI","unit":unit,
                    "lesson":int(row["id"])},teacher.copy())
                text=_native_text(runtime,state)
                rows=runtime._rph_rows(state,text)
                if not isinstance(rows,dict):
                    raise TypeError("unexpected native row structure")
                m=inspect(rows,row["activity_note"])
                stats["rendered"]+=1
                for k,v in (("numbered_source",m["source_steps"]),
                            ("missing_exact_source_step",m["missing"]),
                            ("duplicate_source_step",m["duplicate"]),
                            ("short_main_under_150_chars",m["main_chars"]<150),
                            ("no_explicit_teacher",not m["teacher_explicit"]),
                            ("no_explicit_pupil",not m["pupil_explicit"])):
                    if v: stats[k]+=1
                proposed=candidate(rows,row["activity_note"],m)
                if proposed is not None: stats["candidate"]+=1
                record={"year":year,"pdp":row["sequence_no"],"id":row["id"],"unit":unit,
                    "topic":row.get("topic"),**m,"candidate_available":proposed is not None}
                report["records"].append(record)
                # At most two diagnostic examples per field/year: actual
                # source, current output and candidate, not invented content.
                bucket=(year,str(unit))
                if len(examples[bucket])<2 and (proposed or m["duplicate"] or m["main_chars"]<150 or not m["teacher_explicit"] or not m["pupil_explicit"]):
                    examples[bucket].append({**record,"source_note":row["activity_note"],
                        "objective":rows.get("OBJEKTIF PEMBELAJARAN") or rows.get("OBJEKTIF"),
                        "current_main":rows.get("AKTIVITI UTAMA"),"candidate_main":proposed})
            except Exception as exc:
                stats["errors"]+=1
                report["records"].append({"year":year,"id":row["id"],"pdp":row["sequence_no"],
                    "error":type(exc).__name__})
        report["examples"]=[e for v in examples.values() for e in v]
        out=Path("qa/pi-activity-quality")
        out.mkdir(parents=True,exist_ok=True)
        (out/"audit.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        print("PI_ACTIVITY_QUALITY",json.dumps(report["years"],ensure_ascii=False),flush=True)
        for e in report["examples"][:20]:
            print("PI_ACTIVITY_EXAMPLE",json.dumps(e,ensure_ascii=False),flush=True)
        assert sum(s["source"] for s in report["years"].values())==698
        assert sum(s["rendered"] for s in report["years"].values())==698
    finally:
        tmp.cleanup()

if __name__=="__main__":
    main()
