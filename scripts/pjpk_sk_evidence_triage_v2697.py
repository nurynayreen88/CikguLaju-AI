"""Read-only SK evidence triage; evidence presence never creates an RPT SK link."""
import argparse
import csv
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ("dskp_sk_direct_t1_pj_v2690.csv", "dskp_sk_direct_t2_t6_pj_v2694.csv")

def load_sk(root=ROOT):
    index = {}
    for name in FILES:
        with (root / "curriculum_sources" / "pjpk" / name).open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                key = (row["year_label"].strip(), row["subject"].strip(), row["sk_code"].strip())
                if not all(key) or not all(row[k].strip() for k in ("sk_text","source_document","source_page","source_file_id")) or row["verification_status"] != "DIRECT_SOURCE_TRANSCRIPTION":
                    raise ValueError("Invalid direct SK source row: " + repr(key))
                if key in index and index[key]["sk_text"] != row["sk_text"]:
                    raise ValueError("Conflicting direct SK source: " + repr(key))
                index[key] = row
    return index

def triage(db, root=ROOT):
    evidence = load_sk(root)
    uri = Path(db).resolve().as_uri() + "?mode=ro"
    with sqlite3.connect(uri, uri=True) as con:
        con.row_factory = sqlite3.Row
        entries = con.execute("""SELECT e.id,e.year_label,e.subject,e.unit_title,e.topic
            FROM rpt_entries e WHERE e.subject IN ('Pendidikan Jasmani','Pendidikan Kesihatan')
            AND NOT EXISTS (SELECT 1 FROM rpt_entry_standards s
              WHERE s.rpt_entry_id=e.id AND s.standard_type='SK')
            ORDER BY e.year_label,e.subject,e.id""").fetchall()
        output = []
        for e in entries:
            sp = con.execute("""SELECT standard_code,standard_text FROM rpt_entry_standards
                WHERE rpt_entry_id=? AND standard_type='SP' ORDER BY sequence_no""",(e["id"],)).fetchall()
            prefixes = sorted({r["standard_code"].rsplit(".",1)[0] for r in sp
                               if r["standard_code"] and r["standard_code"].count(".")==2})
            matches = [evidence[(e["year_label"],e["subject"],code)] for code in prefixes
                       if (e["year_label"],e["subject"],code) in evidence]
            output.append({"entry_id":e["id"],"year":e["year_label"],"subject":e["subject"],
                "topic":(e["unit_title"] or "")+" — "+(e["topic"] or ""),
                "sp_codes":[r["standard_code"] for r in sp],
                "candidate_sk_codes":prefixes,"direct_sk_sources":matches,
                "status":"SOURCE_CANDIDATE_REQUIRES_RPT_VERIFICATION" if matches else "SK_SOURCE_NOT_YET_TRANSCRIBED",
                "rpt_sk_link_created":False})
    return {"read_only":True,"production_promoted":False,"missing_sk_entries":len(output),
        "source_candidates":sum(bool(x["direct_sk_sources"]) for x in output),
        "items":output}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--db",required=True)
    a=p.parse_args()
    print(json.dumps(triage(a.db),ensure_ascii=False,indent=2))
