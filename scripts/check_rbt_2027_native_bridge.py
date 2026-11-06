#!/usr/bin/env python3
"""Off-line RBT Telegram->Web boundary smoke tests; no account/DB/network."""
from __future__ import annotations
import io
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from flask import Flask
from docx import Document
from reportlab.pdfgen.canvas import Canvas
from web.rbt_2027_user_runtime import SUBJECT, SELECTION, adapt_rows, install, _selected
from web.rbt_2027_native_api import create_rbt_2027_native_blueprint

TOKEN="rbt-ci-private-token-2027-0123456789-abcdef"


def run():
    orig=dict(os.environ)
    os.environ["CIKGULAJU_AUTHORITATIVE_API_TOKEN"]=TOKEN
    os.environ["CIKGULAJU_WEB_NATIVE_RPH_ENABLED"]="1"
    os.environ["CIKGULAJU_RBT_2027_DRAFT_USER_ENABLED"]="1"
    calls=[]
    state={}
    def send(cid,msg,kb=None):
        calls.append((cid,msg,kb))
    def old_callback(cid,data):
        calls.append(("old",cid,data))
    def old_rows(st, *_args, **_kwargs):
        return {"TAJUK":"Original RPH"}
    def choose_class(cid):
        calls.append(("class",cid))
    ns={"callback":old_callback,"send":send,"_rph_rows":old_rows,
        "_lesson_to_class_v2439":choose_class,"SUBJECTS_BY_GRADE":{
           f"Tahun {y}":["English"] for y in (4,5,6)},"state":state}
    try:
        assert install(ns,enabled=False) is False
        assert all(SUBJECT not in x for x in ns["SUBJECTS_BY_GRADE"].values())
        assert install(ns,enabled=True) is True
        assert install(ns,enabled=True) is True
        assert all(x.count(SUBJECT)==1 for x in ns["SUBJECTS_BY_GRADE"].values())
        ns["callback"](1,"unrelated")
        assert calls[-1]==("old",1,"unrelated")
        state[1]={"year":"Tahun 5"}
        ns["callback"](1,"sub_"+SUBJECT)
        assert calls[-1][2] and len(calls[-1][2])>=4
        ns["callback"](1,"rbt27u|01")
        assert calls[-1][2] and calls[-1][2][0][0]["text"].startswith("PdP 001")
        ns["callback"](1,"rbt27p|001")
        assert calls[-1]==("class",1)
        assert state[1]["subject"]==SUBJECT
        assert _selected(state[1]) is not None
        rows=ns["_rph_rows"](state[1],"irrelevant generated text")
        assert "DRAF" in rows["TAJUK"]
        assert "Buku Teks RBT Tahun" in rows["BAHAN BANTU MENGAJAR"]
        assert "Aktiviti 2 (25 minit)" in rows["AKTIVITI UTAMA"]
        state[1]["sk_code"]="0.0"
        assert _selected(state[1]) is None
        state[1]["sk_code"]="4.3"
        assert _selected(state[1]) is not None

        def native_word(st, source, unique):
            p=Path(tempfile.gettempdir())/(unique+"_RPH.docx")
            d=Document();d.add_heading("CIKGULAJU RPH RBT DRAF",1)
            # Native Telegram output has three top-level tables, with its
            # activity table using three columns. Keep the fake faithful.
            h=d.add_table(rows=2,cols=2)
            h.cell(0,0).text="Mata Pelajaran"
            h.cell(0,1).text=SUBJECT
            h.cell(1,0).text="Tajuk"
            h.cell(1,1).text=ns["_rph_rows"](st,source)["TAJUK"]
            t=d.add_table(rows=2,cols=3)
            t.cell(0,0).text="Fasa";t.cell(0,1).text="Aktiviti";t.cell(0,2).text="Catatan"
            t.cell(1,0).text="Aktiviti Utama"
            t.cell(1,1).text=ns["_rph_rows"](st,source)["AKTIVITI UTAMA"]
            f=d.add_table(rows=1,cols=2)
            f.cell(0,0).text="Refleksi";f.cell(0,1).text="Draf"
            d.save(p)
            return str(p)

        def native_pdf(st, source, unique):
            p=Path(tempfile.gettempdir())/(unique+"_RPH.pdf")
            c=Canvas(str(p),pagesize=(595.28,841.89))
            c.drawString(20,800,"CIKGULAJU RPH RBT DRAF")
            c.drawString(20,780,ns["_rph_rows"](st,source)["STANDARD PEMBELAJARAN"])
            c.showPage();c.save()
            return str(p)

        runtime=SimpleNamespace(RBT_2027_DRAFT_USER_BRIDGE_ACTIVE=True,
           create_word_file=native_word,create_pdf_file=native_pdf,
           _rph_rows=ns["_rph_rows"])
        app=Flask("rbt-native-gate-test")
        app.register_blueprint(create_rbt_2027_native_blueprint(runtime))
        client=app.test_client()
        def get(path):
            return client.get(path,headers={"Authorization":"Bearer "+TOKEN})
        auth_fail=client.get("/internal/rph/v1/rbt/units?year=5")
        assert auth_fail.status_code==401,auth_fail.status_code
        groups=0; count=0
        for y in (4,5,6):
            res=get(f"/internal/rph/v1/rbt/units?year={y}")
            assert res.status_code==200,(y,res.get_json())
            units=res.get_json()["items"]
            assert len({u["value"] for u in units})==len(units)
            groups+=len(units)
            all_pdp=[]
            for u in units:
                res=get(f"/internal/rph/v1/rbt/lessons?year={y}&unit={u['value']}")
                assert res.status_code==200,(y,u,res.get_json())
                lessons=res.get_json()["items"]
                assert lessons and all(l["status"]=="DRAF" for l in lessons)
                all_pdp.extend(int(l["value"]) for l in lessons)
                count+=len(lessons)
            assert sorted(all_pdp)==list(range(1,33))
        assert count==96,(groups,count)
        assert get("/internal/rph/v1/rbt/units?year=3").status_code==503
        assert get("/internal/rph/v1/rbt/lessons?year=5&unit=u99").status_code==503
        assert get("/internal/rph/v1/rbt/availability?year=5&unit=u01&lesson=001").get_json()["available"] is True
        assert get("/internal/rph/v1/rbt/availability?year=5&unit=u02&lesson=001").status_code==404
        for y,u,p in ((4,"u01","001"),(5,"u01","001"),(6,"u03","032")):
            for fmt in ("word","pdf"):
                res=client.post("/internal/rph/v1/rbt/render",
                    json={"selection":{"year":y,"unit":u,"lesson":p},
                          "teacher":{"class":"5 Ikhlas","date":"2027-01-04",
                                     "time":"08:00-09:00","students":"25"},
                          "format":fmt},
                    headers={"Authorization":"Bearer "+TOKEN})
                assert res.status_code==200,(y,p,fmt,res.status_code,res.get_json())
                assert res.data.startswith(b"PK\x03\x04" if fmt=="word" else b"%PDF-")
                assert b"DRAF" in res.headers["Content-Disposition"].encode()
                assert res.headers["Cache-Control"]=="no-store, private"
        os.environ["CIKGULAJU_RBT_2027_DRAFT_USER_ENABLED"]="0"
        res=get("/internal/rph/v1/rbt/units?year=4")
        assert res.status_code==503
        print(f"PASS: {count} lessons, {groups} units, menu callback, native Word/PDF proxy, gates, no DB changes.")
    finally:
        os.environ.clear();os.environ.update(orig)

if __name__=="__main__":
    run()
