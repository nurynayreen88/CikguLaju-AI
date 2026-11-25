"""Read-only audit of all 175 Music lessons through the registered native endpoint.
Report repeated/generic activity text and real downloadable document QA.
No production credentials, quota, DB writes, or release status changes.
"""
import io
import os
import json
import re
from pathlib import Path
from collections import defaultdict,Counter
from unittest.mock import patch
from flask import Flask
from docx import Document
from pypdf import PdfReader
from web.telegram_provisional_arab_music_api import _unit_rows,_lesson_rows,_selected,create_provisional_subjects_blueprint

def norm(s):
    return " ".join(str(s).casefold().split())

def main():
    os.environ.update(BOT_TOKEN="",GEMINI_API_KEY="",CIKGULAJU_AUTHORITATIVE_API_TOKEN="t"*40,CIKGULAJU_WEB_NATIVE_RPH_ENABLED="1")
    import requests
    def deny(*a,**k):
        raise AssertionError("network prohibited in audit")
    with patch.object(requests.sessions.Session,"request",new=deny):
        import app as runtime
    from web.rph_teacher_reflection import install
    assert install(runtime)
    server=Flask("music175-audit")
    server.register_blueprint(create_provisional_subjects_blueprint(runtime))
    client=server.test_client()
    auth={"Authorization":"Bearer "+"t"*40}
    out=Path("qa/music175")
    out.mkdir(parents=True,exist_ok=True)
    records=[]
    repeats=defaultdict(list)
    errors=[]
    for y in range(2,7):
        year=[]
        for unit in _unit_rows(y,"MUZIK"):
            u=unit["value"]
            for option in _lesson_rows(y,"MUZIK",u):
                selection={"year":y,"subject":"MUZIK","unit":u,"lesson":option["value"]}
                selected=_selected(y,"MUZIK",u,option["value"])
                music=selected["music"]
                layout=music["preview"]["layout"]
                header={x["label"]:x["value"] for x in layout["header"]}
                activity=layout["phases"][1]["activity"]
                rec={"year":y,"lesson":option["value"],"unit":u,"title":music["title"],"sk":header["Standard Kandungan"],"sp":header["Standard Pembelajaran"],"objective":header["OBJEKTIF PEMBELAJARAN"],"criterion":header["KRITERIA KEJAYAAN"],"activity":activity,"phase_text":music["preview"]["phase_text"],"issues":[]}
                key=(y,option["value"])
                repeats[norm(activity)].append(key)
                if not rec["objective"].strip() or not rec["criterion"].strip(" _—"):
                    rec["issues"].append("missing objective or criterion")
                if any(not re.match(r"^\d+\.\d+(?:\.\d+)?\s+\S",line) for line in rec["sp"].splitlines()):
                    rec["issues"].append("SP without description")
                if len(rec["sk"].splitlines()) != len(music["preview"]["sk_codes"]) or any(not line.startswith(code+" ") for line,code in zip(rec["sk"].splitlines(),music["preview"]["sk_codes"])):
                    rec["issues"].append("SK display delimiter")
                teacher=dict.fromkeys(("class","date","time","students"),"")
                for fmt in ("word","pdf"):
                    response=client.post("/internal/rph/v1/other-drafts/render",headers=auth,json={"selection":selection,"teacher":teacher,"format":fmt})
                    if response.status_code!=200:
                        rec["issues"].append(f"{fmt} HTTP {response.status_code}")
                        continue
                    try:
                        if fmt=="word":
                            document=Document(io.BytesIO(response.data))
                            lines=[p.text for t in document.tables for row in t.rows for cell in row.cells for p in cell.paragraphs]
                            rec["word_tables"]=len(document.tables)
                            rec["word_activity_heading_bold"]=sum(1 for t in document.tables for row in t.rows for cell in row.cells for p in cell.paragraphs for r in p.runs if r.bold and re.match(r"^Aktiviti\s+\d",r.text,re.I))
                        else:
                            pdf=PdfReader(io.BytesIO(response.data))
                            rec["pdf_pages"]=len(pdf.pages)
                            if len(pdf.pages)!=1:
                                rec["issues"].append("PDF not one page")
                            lines=[p.extract_text() or "" for p in pdf.pages]
                        joined="\n".join(lines)
                        if re.search(r"(?im)^\s*(?:Aktiviti\s+\d|Set Induksi|Penutup)[^\n]{0,100}\(\d+\s*minit\)",joined):
                            rec["issues"].append(f"{fmt} printed phase duration")
                    except Exception as exc:
                        rec["issues"].append(f"{fmt} parse {type(exc).__name__}")
                records.append(rec)
                year.append(rec)
        assert len(year)==35
        print("MUSIC_NATIVE_AUDIT",y,len(year),dict(Counter(issue for r in year for issue in r["issues"])),flush=True)
    assert len(records)==175
    repeated=[v for v in repeats.values() if len(v)>1]
    (out/"report.json").write_text(json.dumps({"records":records,"identical_activities":repeated},ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("MUSIC_NATIVE_TOTAL",len(records),"identical_activity_groups",len(repeated),"issue_count",sum(len(r["issues"]) for r in records),flush=True)

    assert not any(r["issues"] for r in records), "Native document or standard format issues remain"

if __name__=="__main__":
    main()
