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
    # Inventory instructional English phrases in the original 809 PI records.
    # Retain source row IDs and exact snippets. Do not infer all Latin text is wrong.
    english_groups={}
    english_rows=[]
    for y in YEARS:
        rows=conn.execute("""SELECT id,sequence_no,activity_note,assessment_note,topic,subtopic
                             FROM rpt_entries WHERE subject='Pendidikan Islam'
                             AND year_label=? AND verified=1 ORDER BY sequence_no,id""",
                          (f"Tahun {y}",)).fetchall()
        for row in rows:
            for field in ("activity_note","assessment_note","topic","subtopic"):
                val=str(row[field] or "")
                phrases=re.findall(r"[A-Za-z][A-Za-z -]{2,}[A-Za-z]",val)
                for raw in phrases:
                    value=" ".join(raw.split())
                    if not value:continue
                    english_groups.setdefault(value.casefold(),{"original":value,"count":0,"rows":[]})
                    e=english_groups[value.casefold()]
                    e["count"]+=1
                    if len(e["rows"])<4:e["rows"].append(f"T{y}-PdP{row['sequence_no']}-{field}")
                    english_rows.append({"year":y,"pdp":row["sequence_no"],"field":field,
                                        "english":value,"context":val[max(0,val.find(raw)-55):val.find(raw)+len(raw)+55]})
    inventory=sorted(english_groups.values(),key=lambda x:(-x["count"],x["original"].casefold()))
    (OUT/"native_pi_english_term_inventory.json").write_text(
        json.dumps({"term_groups":len(inventory),"term_occurrences":len(english_rows),
                    "terms":inventory,"examples":english_rows[:200]},
                   ensure_ascii=False,indent=2),encoding="utf8")
    print("PI_ENGLISH_TERM_INVENTORY",json.dumps({
        "distinct":len(inventory),"occurrences":len(english_rows),"top":inventory[:90]
    },ensure_ascii=False))
    groups=["stay","stray","Role-Play","i-Think","THE YARN YARN","n- think","think",
            "Roling Chip","Puzzle it Out -selesaikan","MIX-N-MATCH",
            "Personal Learning Experiences","spin","talk partners","round table",
            "hot seat","brainstorming","free discussion","Recap Group","Game"]
    contexts={}
    for group in groups:
        ctx=[r for r in english_rows if r["english"].casefold()==group.casefold()]
        contexts[group]=ctx[:2]
    (OUT/"pi_selected_english_term_contexts.json").write_text(
        json.dumps(contexts,ensure_ascii=False,indent=2),encoding="utf8")
    print("PI_SELECTED_CONTEXTS",json.dumps(contexts,ensure_ascii=False))
    print("AUDIT_PASSED: source database not modified; no deployment performed")
    conn.close()

if __name__=="__main__":
    main()
