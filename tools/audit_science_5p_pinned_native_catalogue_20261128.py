"""Offline, pinned Telegram endpoint catalogue verification for Science 5P.

No live HTTP, credentials or production mutations. The actual original
Telegram blueprint runs in an isolated test client against its real source.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from tools.audit_science_native_5p_documents_20261128 import inventory, support_inventory, COUNTS
from tools.science_5p_native_selection_preflight_20261128 import map_catalogue
PIN="207317c6d092561e2ffd07a6d2fb4ef604797030"

# This program runs entirely in the pinned original checkout.
EXTRACT=r'''
import json, os, sys
from unittest.mock import patch
from flask import Flask
from staging.sains.tahun5.semakan_penjana import register_downloads as y5
from staging.sains.tahun6.penjana_2027 import register_downloads as y6
year=int(sys.argv[1])
app=Flask(__name__);app.testing=True
(y5 if year==5 else y6)(app)
client=app.test_client()
route=f"/internal/rph/v1/sains-sk-y{year}-2027"
prefix={5:"v",6:"w"}[year]
params={"year":year,"subject":"SCIENCE"}
def get(path,query):
    resp=client.get(route+"/"+path,query_string=query)
    return resp.status_code,resp.get_json()
def read(path,query):
    status,data=get(path,query)
    if status!=200 or data.get("source")!="telegram-runtime-v1":
        raise ValueError(f"Original endpoint failed {path}: {status}")
    return data["items"]
with patch.dict(os.environ,{"CIKGULAJU_WEB_NATIVE_RPH_ENABLED":"1"}), patch("web.telegram_verified_sequence_rph_bridge._authorization",return_value=True):
    units=read("units",params)
    rows=[]; unavailable=[]
    for u in units:
        for r in read("lessons",{**params,"unit":u["value"]}):
            status,data=get("availability",{**params,"unit":u["value"],"lesson":r["value"]})
            if status!=200 or data.get("available") is not True:
                unavailable.append({"lesson":r["value"],"status":status})
            rows.append(dict(year=year,subject="SCIENCE",curriculum="KSSR",
                unit=prefix+u["value"][1:],unit_label=u["label"],lesson_id=r["value"],
                lesson_label=r["label"],textbook_ref=r.get("textbook_ref",""),ready=False))
print(json.dumps(dict(year=year,source="telegram-native-pdp-sequence",catalogue_prefix=prefix,
    unit_count=len(units),native_selection_count=len(rows),unique_lesson_ids=len({r["lesson_id"] for r in rows}),
    rpt_count_match=len(rows)=={5:116,6:89}[year],records=rows,unavailable=unavailable),ensure_ascii=False))
'''

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--native-root",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    root=a.native_root.resolve()
    if subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip()!=PIN:
        raise ValueError("Wrong pinned source")
    a.out.mkdir(parents=True,exist_ok=False)
    summary=[]; issues=[]
    for year in (5,6):
        native=json.loads(subprocess.check_output([sys.executable,"-c",EXTRACT,str(year)],cwd=root,text=True))
        (a.out/f"catalogue_y{year}.json").write_text(json.dumps(native,ensure_ascii=False,indent=2),encoding="utf-8")
        drafts=inventory(year); support_inventory(year,drafts)
        try:
            mapped=map_catalogue(year,native,drafts)
            for r,d in zip(native["records"],drafts,strict=True):
                # Exact expected original labels and printed page ranges.
                n=int(d["lesson_id"].rsplit("-",1)[-1])
                if r["lesson_label"]!=f"PdP {n:03d} • {d['title']}" or r["unit_label"]!=d["unit"] or r["textbook_ref"]!=f"Buku Teks m/s {d['textbook_pages']}":
                    issues.append({"year":year,"id":d["lesson_id"],"error":"Native label/page mismatch"})
            if native["unavailable"]:
                issues.extend({"year":year,**x,"error":"Original endpoint availability failed"} for x in native["unavailable"])
            summary.append({"year":year,"mapped":len(mapped),"native_endpoint_count":len(native["records"]),
                            "availability_passed":len(native["records"])-len(native["unavailable"])})
        except (ValueError,KeyError,TypeError) as exc:
            issues.append({"year":year,"error":str(exc)})
    report={"status":"PINNED_ORIGINAL_ENDPOINT_TEST_CLIENT_QA_ONLY","source_commit":PIN,
        "years":summary,"issues":issues,"live_backend_verified":False,"academic_approved":False,"release":False}
    (a.out/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False))
    return 1 if issues or len(summary)!=2 else 0

if __name__=="__main__":
    raise SystemExit(main())
