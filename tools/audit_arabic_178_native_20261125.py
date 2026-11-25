"""Audit 178 Arabic Y4–6 RPH using current native download route.
Read-only; do not promote SP transcription candidates or modify the source.
"""
import io
import os
import json
import re
from collections import Counter,defaultdict
from pathlib import Path
from unittest.mock import patch
from flask import Flask
from docx import Document
from web.telegram_provisional_arab_music_api import _unit_rows,_lesson_rows,_selected,_arab_index,create_provisional_subjects_blueprint
from tools.arabic_178_draft_shared_layout_20261124 import BANK
from scripts.render_bahasa_arab_staging import first

COUNTS={4:58,5:60,6:60}
def norm(s):
    return " ".join(str(s or "").casefold().split())

def main():
    os.environ.update(BOT_TOKEN="",GEMINI_API_KEY="",CIKGULAJU_AUTHORITATIVE_API_TOKEN="t"*40,CIKGULAJU_WEB_NATIVE_RPH_ENABLED="1")
    import requests
    def deny(*a,**k):
        raise AssertionError("network prohibited")
    with patch.object(requests.sessions.Session,"request",new=deny):
        import app as runtime
    server=Flask("arabic178-audit")
    server.register_blueprint(create_provisional_subjects_blueprint(runtime))
    client=server.test_client()
    auth={"Authorization":"Bearer "+"t"*40}
    bank=json.loads(BANK.read_text(encoding="utf8"))["years"]
    records=[]
    activity_groups=defaultdict(list)
    for y,count in COUNTS.items():
        year=[]
        for unit in _unit_rows(y,"ARAB"):
            u=unit["value"]
            for option in _lesson_rows(y,"ARAB",u):
                n=int(option["value"])
                s=_selected(y,"ARAB",u,option["value"])
                f=s["fields"]
                row=_arab_index()[(y,n)]
                candidate=bank[str(y)]["entries"].get(row["sp"])
                record={"year":y,"pdp":n,"unit":u,"topic":row["unit_name"],"focus":row["fokus"],"sk":row["sk"],"sp":row["sp"],"pages":row["halaman_buku"],"sp_candidate":candidate,"objective":first(f,"Objektif PdP","Objektif pembelajaran","Objektif"),"criterion":first(f,"Kriteria kejayaan"),"activity1":first(f,"Aktiviti 1"),"activity2":first(f,"Aktiviti 2"),"assessment":first(f,"Pengukuhan","Penilaian (PBD)","PBD"),"issues":[]}
                activity_groups[norm(record["activity1"]+" "+record["activity2"])].append([y,n])
                selection={"year":y,"subject":"ARAB","unit":u,"lesson":option["value"]}
                response=client.post("/internal/rph/v1/other-drafts/render",headers=auth,json={"selection":selection,"teacher":dict.fromkeys(("class","date","time","students"),""),"format":"word"})
                if response.status_code!=200:
                    record["issues"].append(f"Word HTTP {response.status_code}")
                else:
                    doc=Document(io.BytesIO(response.data))
                    record["tables"]=len(doc.tables)
                    if len(doc.tables)!=4:
                        record["issues"].append("RTL four-table layout")
                    else:
                        fields={r.cells[0].text:r.cells[1].text for r in doc.tables[1].rows}
                        sk=fields.get("معيار المحتوى","")
                        sp=fields.get("معيار التعلّم","")
                        if norm(sk)==norm(row["sk"]):record["issues"].append("SK code only")
                        if norm(sp)==norm(row["sp"]):record["issues"].append("SP code only")
                        if any(not re.search(r"[\u0600-\u06ff]",record[k]) for k in ("objective","criterion","activity1","activity2")):
                            record["issues"].append("one or more core fields lack Arabic text")
                        if any(abs(sum(c.width.mm for c in t.columns)-187)>1 for t in doc.tables):
                            record["issues"].append("unequal grid widths")
                if not candidate:record["issues"].append("SP source candidate absent")
                year.append(record)
                records.append(record)
        assert len(year)==count
        print("ARAB_NATIVE_AUDIT",y,len(year),dict(Counter(i for r in year for i in r["issues"])),flush=True)
    assert len(records)==178
    out=Path("qa/arabic178")
    out.mkdir(parents=True,exist_ok=True)
    groups=[v for v in activity_groups.values() if len(v)>1]
    (out/"report.json").write_text(json.dumps({"records":records,"identical_activity_groups":groups},ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("ARAB_NATIVE_TOTAL",len(records),"identical_activity_groups",len(groups),flush=True)

if __name__=="__main__":
    main()
