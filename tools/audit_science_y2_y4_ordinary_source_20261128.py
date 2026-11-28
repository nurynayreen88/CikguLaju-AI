"""Offline extraction of ordinary RPH curriculum fields from pinned Telegram source.
No network, account, entitlement, render, database migration or production writes.
The original module may bootstrap local bundled DB copies inside the CI checkout.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

PIN="495d0b24d5ded8026f5e85cf4b39d45cbe2debb7"
APP_BLOB="a7180e112ec0ca3f36dad444c13332729f59e3ea"
COUNTS={2:58,3:54,4:85}
FIELDS={"TAJUK","BIDANG","TEMA","STANDARD KANDUNGAN","STANDARD PEMBELAJARAN",
        "OBJEKTIF","OBJEKTIF PEMBELAJARAN","KRITERIA KEJAYAAN","SET INDUKSI",
        "AKTIVITI","AKTIVITI PDP","AKTIVITI UTAMA","PENUTUP","PENTAKSIRAN","PBD",
        "PENILAIAN","BBM","BAHAN BANTU MENGAJAR","EMK","PAK21","KBAT","EMK / NILAI",
        "KBAT / PAK21","PEMULIHAN","PENGAYAAN","PEMULIHAN / PENGAYAAN",
        "RUJUKAN","RUJUKAN BUKU TEKS","BUKU TEKS","TINDAKAN SUSULAN"}
def deny(*args,**kwargs):
    raise RuntimeError("Network forbidden in source-only QA")
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--native-root",type=Path,required=True)
    p.add_argument("--index",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--year",type=int,choices=COUNTS,required=True)
    a=p.parse_args()
    native=a.native_root.resolve()
    out=a.out.resolve(); out.mkdir(parents=True,exist_ok=False)
    index=json.loads(a.index.resolve().read_text(encoding="utf-8"))
    if subprocess.check_output(["git","-C",str(native),"rev-parse","HEAD"],text=True).strip()!=PIN:
        raise ValueError("Incorrect native commit")
    raw=(native/"app.py").read_bytes()
    if hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()!=APP_BLOB:
        raise ValueError("Native module bytes mismatch")
    expected={r["lesson_id"]:r for r in index["records"] if r["year"]==a.year}
    if len(expected)!=COUNTS[a.year]: raise ValueError("Invalid index count")
    # No production secret or database path is supplied. Allow local bundled
    # bootstrap only, in a disposable checked-out source directory.
    os.chdir(native)
    sys.path.insert(0,str(native))
    for k in list(os.environ):
        if any(t in k.upper() for t in ("TOKEN","SECRET","API_KEY","DATABASE_URL","DB_PATH","WEBHOOK","SUPABASE")):
            os.environ.pop(k,None)
    import requests
    requests.sessions.Session.request=deny
    socket.create_connection=deny
    socket.socket.connect=deny
    socket.socket.connect_ex=deny
    import app as runtime
    from tools.science_y2_y4_native_identity_audit_20261128 import snapshot
    from web.telegram_verified_sequence_rph_bridge import _build_state,_source_text,_resolve,_science_textbook_pages
    if not getattr(runtime,"CIKGULAJU_DB_V2600_ACTIVE",False): raise ValueError("Pinned bundled DB inactive")
    actual=snapshot(runtime,a.year)
    if len(actual)!=len(expected) or {r["lesson_id"] for r in actual}!=set(expected):
        raise ValueError("Catalogue drift: no source adaptation authorized")
    records=[]; issues=[]
    teacher=dict(class_="",date="",time="",students="")
    teacher["class"]=teacher.pop("class_")
    for row in actual:
        cid=row["lesson_id"]; idx=expected[cid]
        try:
            if (row["unit"]!=idx["unit"] or row["title"]!=idx["title"]
                or sorted(s["sp_code"] for s in row["standards"])!=idx["sp_codes"]):
                raise ValueError("Identity mismatch")
            _,selected,mapped=_resolve(runtime,a.year,"SCIENCE",row["unit"],cid)
            state=_build_state(runtime,a.year,"SCIENCE",row["unit"],cid,teacher)
            text=_source_text(runtime,state)
            fields=runtime._rph_rows(state,text)
            if not isinstance(fields,dict): raise ValueError("Unexpected original RPH fields")
            safe={str(k):v for k,v in fields.items() if str(k).strip().upper() in FIELDS and isinstance(v,str)}
            if not safe or not any("OBJEKTIF" in k.upper() for k in safe) or not any("AKTIVITI" in k.upper() for k in safe):
                raise ValueError("Required curriculum fields missing")
            records.append({"id":cid,"year":a.year,"unit":row["unit"],"title":row["title"],
                "standards":row["standards"],"minutes":row["minutes"],
                "textbook_refs":row["textbook_refs"],"checked_pages":_science_textbook_pages(a.year,cid,selected),
                "opening":row["opening"],"ordinary_fields":safe,
                "source_text_sha256":hashlib.sha256(text.encode()).hexdigest(),
                "hold":idx["status"]=="HOLD","ready":False})
        except Exception as exc:
            # No raw exception payload, state, credentials or personal fields.
            issues.append({"id":cid,"type":type(exc).__name__})
    report={"year":a.year,"source_commit":PIN,"expected":len(expected),"extracted":len(records),
            "held_extracted":sum(r["hold"] for r in records),"issues":issues,"release":False}
    (out/"curriculum_source.json").write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding="utf-8")
    (out/"report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report))
    return int(bool(issues) or len(records)!=len(expected))
if __name__=="__main__":
    raise SystemExit(main())
