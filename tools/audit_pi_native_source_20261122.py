"""Read-only audit: native PI Jawi RPT DB vs 696 2027 draft metadata.

This script uses only the repository's existing curriculum files, does not
import a server, does not access secrets, and never modifies source content.
"""
from __future__ import annotations
import csv
import json
import re
import sqlite3
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/"CikguLaju_Curriculum_Master_v25_93_PI_ENGLISH_Y1_Y4.db"
PARTS=[ROOT/(DB.name+suffix) for suffix in (".part1",".part2")]
OUT=ROOT/"audit_output_pi_20261122"
ARABIC=re.compile(r"[\u0600-\u06ff]")
ROMAN=re.compile(r"(?i)[a-z]{3,}")
YEARS=range(1,7)

def tokens(s):
    text=str(s or "")
    return {"jawi":bool(ARABIC.search(text)),"roman":bool(ROMAN.search(text)),
            "empty":not bool(text.strip())}

def main():
    OUT.mkdir(exist_ok=True)
    if not DB.exists():
        if any(not p.exists() for p in PARTS):
            raise SystemExit("Master DB part missing")
        with DB.open("wb") as dest:
            for part in PARTS:
                with part.open("rb") as source:
                    while True:
                        b=source.read(1024*1024)
                        if not b: break
                        dest.write(b)
    conn=sqlite3.connect("file:"+str(DB)+"?mode=ro",uri=True)
    conn.row_factory=sqlite3.Row
    valid=conn.execute("PRAGMA integrity_check").fetchone()[0]
    assert valid=="ok",valid
    cols={r["name"] for r in conn.execute("PRAGMA table_info(rpt_entries)")}
    cols_det={r["name"] for r in conn.execute("PRAGMA table_info(pi_pdp_details_v2591)")}
    stats=[]
    exported=[]
    for year in YEARS:
        label=f"Tahun {year}"
        rows=conn.execute("""SELECT * FROM rpt_entries
                             WHERE subject='Pendidikan Islam' AND year_label=? AND verified=1
                             ORDER BY sequence_no,id""",(label,)).fetchall()
        counter=Counter()
        seen=set()
        for r in rows:
            rec=dict(r)
            n=rec["sequence_no"]
            if n in seen:counter["duplicate_pdp_numbers"]+=1
            seen.add(n)
            a=tokens(rec.get("activity_note"))
            s=tokens(rec.get("assessment_note"))
            counter["activity_jawi"]+=int(a["jawi"])
            counter["activity_roman"]+=int(a["roman"])
            counter["activity_blank"]+=int(a["empty"])
            counter["assessment_jawi"]+=int(s["jawi"])
            counter["assessment_roman"]+=int(s["roman"])
            counter["assessment_blank"]+=int(s["empty"])
            standards=conn.execute("""SELECT standard_type,standard_code,standard_text
              FROM rpt_entry_standards WHERE rpt_entry_id=? AND verified=1""",(rec["id"],)).fetchall()
            sk=[r for r in standards if r["standard_type"]=="SK"]
            sp=[r for r in standards if r["standard_type"]=="SP"]
            counter["sk_missing"]+=int(not sk)
            counter["sp_missing"]+=int(not sp)
            objective=""
            if "objective_jawi" in cols_det:
                try:
                    x=conn.execute("""SELECT objective_jawi FROM pi_pdp_details_v2591
                    WHERE year_label=? AND pdp_no=? AND verified=1 LIMIT 1""",(label,n)).fetchone()
                    objective=str(x[0] or "") if x else ""
                except sqlite3.Error:
                    pass
            counter["objective_jawi"]+=int(tokens(objective)["jawi"])
            exported.append({"year":year,"pdp":n,"source":"verified-2026-RPT-native",
                "activity_jawi":a["jawi"],"activity_roman":a["roman"],
                "assessment_jawi":s["jawi"],"assessment_roman":s["roman"],
                "sk_count":len(sk),"sp_count":len(sp),"objective_jawi":bool(ARABIC.search(objective))})
        stat={"year":year,"verified_rows":len(rows),**dict(counter)}
        if year>=2:
            data=json.loads((ROOT/f"rph_standalone/pendidikan_islam_draf_2027/year{year}.json").read_text(encoding="utf8"))
            recs=data.get("records",[])
            stat.update({"draft_rows":len(recs),
                         "draft_ready":sum(bool(r.get("verified_ready")) for r in recs),
                         "draft_withheld":sum(bool(r.get("withheld")) for r in recs),
                         "draft_bbm_roman":sum(tokens((r.get("fields") or {}).get("bahan"))["roman"] for r in recs),
                         "draft_closing_roman":sum(tokens((r.get("fields") or {}).get("penutup"))["roman"] for r in recs)})
        stats.append(stat)
    assert sum(s["verified_rows"] for s in stats)==809, "unexpected older 809-PdP catalogue"
    with (OUT/"pi_native_2026_versus_draf_2027_stats.json").open("w",encoding="utf8") as f:
        json.dump({"db_integrity":valid,"database":DB.name,"pi_rows":809,"stats":stats},f,ensure_ascii=False,indent=2)
    with (OUT/"pi_native_809_readonly_flags.csv").open("w",encoding="utf8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(exported[0]))
        w.writeheader();w.writerows(exported)
    print(json.dumps({"db_integrity":valid,"pi_rows":809,"stats":stats},ensure_ascii=False))
    print("AUDIT_PASSED: source database not modified; no deployment performed")
    conn.close()

if __name__=="__main__":
    main()
