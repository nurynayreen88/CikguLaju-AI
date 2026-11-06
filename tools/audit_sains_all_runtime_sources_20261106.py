"""Read-only science source topology across shipped SQLite checkpoints.

Every assembled DB lives in a temporary directory. NO writes to shipped data,
NO migrations, NO app import, NO runtime fallback. Counts are *source facts*
and must never be described as approved or rendered RPH.
"""
from __future__ import annotations
import hashlib
import json
import re
import sqlite3
import tempfile
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
NAMES=(
    "CikguLaju_Curriculum_Master_v25_68_SCIENCE_MATH_UPLOAD_READY.db",
    "CikguLaju_Curriculum_Master_v25_70_SCIENCE_SEQUENCE_REPAIRED.db",
    "CikguLaju_Curriculum_Master_v25_71_PRIMARY_QA_FIX.db",
    "CikguLaju_Curriculum_Master_v25_82_PRIMARY_LANGUAGE_SCIENCE_VERB_QA.db",
    "CikguLaju_v26_16.db",
)
SUBJECT=("sains","science")

def locate_parts(stem):
    full=ROOT/stem
    if full.is_file():
        return [full]
    raw=sorted(ROOT.glob(stem+".part*"))
    if raw:
        ids=[]
        for p in raw:
            suffix=p.name[len(stem)+len(".part"):]
            if not suffix.isdigit():
                return []
            ids.append(int(suffix))
        if ids!=list(range(min(ids),max(ids)+1)):
            raise ValueError("Noncontiguous DB parts: "+stem)
    return raw

def analyze(name, path):
    result={"source":name,"size":path.stat().st_size,
            "sha256_observed_NOT_signed":hashlib.sha256(path.read_bytes()).hexdigest()}
    with sqlite3.connect(path.resolve().as_uri()+"?mode=ro&immutable=1",uri=True) as db:
        db.row_factory=sqlite3.Row
        db.execute("PRAGMA query_only=ON")
        result["quick_check"]=db.execute("PRAGMA quick_check").fetchone()[0]
        if result["quick_check"]!="ok":
            result["status"]="INVALID_CHECKPOINT"
            return result
        tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        result["science_related_tables"]=[t for t in sorted(tables) if any(
            token in t.lower() for token in ("science","sains","rph","pdp","rpt"))][:50]
        for table in ("verified_pdp_sequence","verified_pdp_sequence_v2",
                      "curriculum_standards","rpt_entries"):
            if table not in tables:continue
            cols={r[1] for r in db.execute(f'PRAGMA table_info("{table}")')}
            info={"columns":sorted(cols)}
            if {"subject","year_label"}<=cols:
                rows=[dict(r) for r in db.execute(
                    f'SELECT * FROM "{table}" WHERE lower(trim(subject)) IN (?,?)',
                    SUBJECT)]
                info["science_primary_rows"]=sum(str(r["year_label"]).startswith("Tahun ") for r in rows)
                info["years"]=dict(sorted(Counter(str(r["year_label"]) for r in rows
                                                  if str(r["year_label"]).startswith("Tahun ")).items()))
                if "pdp_sequence_code" in cols:
                    info["unique_primary_pdp_codes_by_year"]={
                        str(y):len({str(r.get("pdp_sequence_code") or "").strip()
                                    for r in rows if r["year_label"]==f"Tahun {y}"
                                    and str(r.get("pdp_sequence_code") or "").strip()})
                        for y in range(1,7)
                    }
                if "textbook_ref" in cols:
                    info["rows_with_textbook_ref"]=sum(bool(str(
                        r.get("textbook_ref") or "").strip()) for r in rows)
                if "verification_status" in cols:
                    info["verification_status_counts"]=dict(Counter(str(
                        r.get("verification_status") or "").strip() for r in rows))
                if "sp_code" in cols:
                    info["distinct_sp_codes"]=len({str(r.get("sp_code") or "").strip()
                                                    for r in rows if r.get("sp_code")})
                if "pdp_title" in cols and "pdp_sequence_code" in cols:
                    info["sample_title"]=[{
                        "year":r["year_label"],
                        "code":r.get("pdp_sequence_code"),
                        "sp":r.get("sp_code"),
                        "title":r.get("pdp_title")} for r in rows[:2]]
            result[table]=info
    return result

def main():
    result={"release_decision":"HOLD","sources":[],"note":
            "Source DB existence is not evidence of active Render deployment or a usable PDF."}
    with tempfile.TemporaryDirectory(prefix="cikgulaju_science_source_probe_") as td:
        for name in NAMES:
            parts=locate_parts(name)
            if not parts:
                result["sources"].append({"source":name,"present":False})
                continue
            dest=Path(td)/(name+".TEMP")
            with dest.open("wb") as dst:
                for part in parts:
                    with part.open("rb") as inp:
                        for chunk in iter(lambda:inp.read(1024*1024),b""):
                            dst.write(chunk)
            try:
                item=analyze(name,dest)
                item["present"]=True
                item["source_parts"]=[p.name for p in parts]
                result["sources"].append(item)
            except (sqlite3.DatabaseError,ValueError) as exc:
                result["sources"].append({"source":name,"present":True,
                                          "status":"NOT_READABLE",
                                          "error":type(exc).__name__})
    print(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
