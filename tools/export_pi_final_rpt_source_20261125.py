"""Export the final native 698 PI RPH as a source-locked RPT input.
No DB writes, date reassignment, account access or production changes.
"""
import os
import json
import sqlite3
from pathlib import Path
from collections import Counter
from tools.bm_native_v26_navigation_audit import database
from web.pi_editorial_bulk_20261125 import load_catalog, apply, norm
from web.rph_pi_jawi_numerals_20261124 import jawi_display_digits

EXPECTED={2:112,3:148,4:152,5:144,6:142}
OLD={2:112,3:147,4:151,5:143,6:143}

def main():
    os.environ["CIKGULAJU_PI_EDITORIAL_BULK"]="0"
    from tools import run_telegram_with_curriculum_api as running
    from web.telegram_verified_rpt_rph_bridge import _native_state,_native_text
    runtime=running.telegram_runtime
    catalog=load_catalog()
    tmp,db=database()
    try:
        runtime.DB_PATH=str(db)
        runtime.CIKGULAJU_DB_V2600_ACTIVE=True
        records=[]
        with sqlite3.connect(db.resolve().as_uri()+"?mode=ro",uri=True) as con:
            con.row_factory=sqlite3.Row
            con.execute("PRAGMA query_only=ON")
            for item in sorted(catalog.values(),key=lambda x:(x["year"],x["pdp"])):
                source=dict(con.execute("SELECT * FROM rpt_entries WHERE id=? AND verified=1 AND subject='Pendidikan Islam'",(item["id"],)).fetchone())
                assert source["sequence_no"]==item["pdp"]
                assert source["year_label"]==f"Tahun {item['year']}"
                state=_native_state(runtime,{"year":item["year"],"subject":"PI","unit":item["unit"],"lesson":item["id"]},{"class":"","date":"","time":"","students":"","reflection":""})
                old=runtime._rph_rows(state,_native_text(runtime,state))
                revised=apply(state,old,catalog)
                expected=jawi_display_digits("\n".join(f"اکتيۏيتي {i} - {title}\n1. {body}" for i,(title,body) in enumerate(item["activities"],1)))
                assert revised["AKTIVITI UTAMA"]==expected,item["id"]
                record={"year":item["year"],"pdp":item["pdp"],"id":item["id"],"unit":item["unit"],
                    "topic":state.get("topic"),"subtopic":state.get("subtopic"),
                    "sk_codes":state.get("grouped_sk_codes",[]),"sp_codes":state.get("grouped_sp_codes",[]),
                    "sk":revised.get("STANDARD KANDUNGAN"),"sp":revised.get("STANDARD PEMBELAJARAN"),
                    "objective":revised.get("OBJEKTIF PEMBELAJARAN") or revised.get("OBJEKTIF"),
                    "activities":item["activities"],"activity_display":expected,
                    "assessment":revised.get("PENTAKSIRAN"),"criterion":revised.get("KRITERIA KEJAYAAN"),
                    "recitation":bool(state.get("_pi_khatam_tasmik_v25210")),
                    "textbook_unit":state.get("textbook_unit"),"textbook_pages":state.get("textbook_pages"),
                    "source_schedule_fields":{k:v for k,v in source.items() if any(x in k.lower() for x in ("duration","minute","minit","week","date","time"))},
                    "native_schedule_fields":{k:v for k,v in state.items() if isinstance(v,(str,int,float,bool,type(None))) and any(x in k.lower() for x in ("duration","minute","minit","week"))}}
                assert record["objective"]
                records.append(record)
        assert len(records)==698
        assert len({x["id"] for x in records})==698
        summary={}
        for year,total in EXPECTED.items():
            selected=[x for x in records if x["year"]==year]
            assert [x["pdp"] for x in selected]==list(range(1,total+1))
            summary[str(year)]={"final_count":total,"old_rpt_count":OLD[year],"recitation_count":sum(x["recitation"] for x in selected),
                "source_schedule_keys":sorted({k for x in selected for k in x["source_schedule_fields"]}),
                "source_schedule_values":{k:dict(Counter(str(x["source_schedule_fields"].get(k)) for x in selected)) for k in sorted({k for x in selected for k in x["source_schedule_fields"]}) if not any(v in k.lower() for v in ("date","week"))}}
            print("PI_RPT_SOURCE",year,json.dumps(summary[str(year)],ensure_ascii=False),flush=True)
        out=Path("qa/pi-rpt-final-source")
        out.mkdir(parents=True,exist_ok=True)
        (out/"records.json").write_text(json.dumps({"status":"RPT_SOURCE_EXPORT_NOT_PUBLISHED","source_commit":"758f15c44e06dc8d9923cb9eb5137c9e77503d14","summary":summary,"records":records},ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        print("PI_RPT_SOURCE_TOTAL",len(records),flush=True)
    finally:
        tmp.cleanup()

if __name__=="__main__":
    main()
