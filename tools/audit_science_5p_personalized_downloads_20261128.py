"""Exercise all 205 personalized draft downloads in both reflection modes.
Uses a Flask test client, synthetic catalogue tokens and synthetic paid account.
Never connects to production or charges real credits.
"""
import argparse
import json
from io import BytesIO
from pathlib import Path
from flask import Flask
from docx import Document
from tools.audit_science_native_5p_documents_20261128 import inventory,support_inventory,fields,display_fields,COUNTS
from tools.audit_science_5p_layout_fixtures_20261128 import inspect_pdf
from tools.science_5p_native_selection_preflight_20261128 import map_catalogue
from tools.science_5p_web_integration_qa_20261128 import create_test_blueprint,URL,ORIGIN
from web.rph_5p_v5_layout import FIELDS,PHASE_KEYS,MS_LABELS

def run(year,out):
    out.mkdir(parents=True,exist_ok=False)
    drafts=inventory(year)
    rows={r["lesson_id"]:r for r in drafts}
    support=support_inventory(year,drafts)
    units={}; records=[]
    prefix={5:"v",6:"w"}[year]
    for r in drafts:
        token=units.setdefault(r["unit"],prefix+format(len(units)+1,"024x"))
        records.append(dict(year=year,subject="SCIENCE",curriculum="KSSR",unit=token,
            unit_label=r["unit"],lesson_id=r["lesson_id"],lesson_label=r["title"],ready=False))
    catalogue=dict(year=year,source="telegram-native-pdp-sequence",catalogue_prefix=prefix,
        rpt_count_match=True,native_selection_count=len(records),unique_lesson_ids=len(records),
        unit_count=len(units),records=records)
    mapping=map_catalogue(year,catalogue,drafts)
    def debit(*args,**kwargs):
        raise AssertionError("Paid QA account must not debit")
    app=Flask(__name__);app.testing=True
    account={"telegram_user_id":42,"authenticated":True,"free_remaining":0,"rakan_pembangun":True}
    app.register_blueprint(create_test_blueprint(account_for_request=lambda req:(42,account),
        mapping_for_year=lambda y:mapping,rows=rows,support=support,debit=debit))
    client=app.test_client()
    issues=[]; counts={"auto_word":0,"auto_pdf":0,"manual_word":0,"manual_pdf":0}
    for cid,r in rows.items():
        s,c,raw=fields(year,r,support[cid])
        s,c,raw=display_fields(s,c,raw)
        for mode in ("auto","manual"):
            reflection=("Bil. murid menguasai:    Belum menguasai:\nKriteria: "+s["criteria"]
                +"\nTindakan: Pemulihan seperti di atas dan pentaksiran semula." if mode=="auto"
                else "Murid memerlukan bimbingan berpandu dan pentaksiran semula.")
            payload=dict(year=year,subject="SCIENCE",unit=mapping[cid]["unit"],lesson=cid,rph_variant="5p",
                teacher_class=f"{year} Bestari",teacher_date="2027-03-02",teacher_start="08:00",
                teacher_end="09:00" if r["minutes"]==60 else "08:30",teacher_students="30",reflection_mode=mode)
            if mode=="manual":payload["reflection"]=reflection
            for fmt in ("word","pdf"):
                try:
                    resp=client.post(URL,json={**payload,"format":fmt},headers={"Origin":ORIGIN})
                    if resp.status_code!=200:
                        raise ValueError(f"HTTP {resp.status_code}: {resp.get_json()}")
                    if "X-RPH-Trial-Remaining" in resp.headers:
                        raise ValueError("Paid account charged")
                    if fmt=="word":
                        d=Document(BytesIO(resp.data))
                        if len(d.tables)!=1 or len(d.tables[0].rows)!=21:
                            raise ValueError("Wrong Word layout")
                        t=d.tables[0]
                        for term in (f"{year} Bestari","02/03/2027","08:00","30"):
                            if term not in t.cell(1,0).text:raise ValueError("Missing header: "+term)
                        if t.cell(20,0).text!="Refleksi" or t.cell(20,1).text!=reflection:
                            raise ValueError("Wrong reflection")
                        for i,k in enumerate(FIELDS[:5],2):
                            if t.cell(i,1).text!=s[k]:raise ValueError("Word field changed: "+k)
                        for i,k in enumerate(PHASE_KEYS):
                            if t.cell(8+2*i,1).text!=c["phases"][k]:raise ValueError("Word phase changed: "+k)
                        for i,k in enumerate(FIELDS[5:-1],17):
                            if t.cell(i,1).text!=s[k]:raise ValueError("Word field changed: "+k)
                    else:
                        file=out/f"{cid}_{mode}.pdf"
                        file.write_bytes(resp.data)
                        inspect_pdf(file,[*MS_LABELS[5:],*[s[k] for k in FIELDS if k!="reflection"],
                            *[c["phases"][k] for k in PHASE_KEYS],s["reference"],reflection,
                            f"{year} Bestari","02/03/2027","08:00",payload["teacher_end"],"30"])
                        file.unlink()
                    counts[mode+"_"+fmt]+=1
                except Exception as exc:
                    issues.append({"id":cid,"mode":mode,"format":fmt,"error":str(exc)})
    report={"status":"PERSONALIZED_DRAFT_TEST_CLIENT_QA_ONLY","year":year,"records":COUNTS[year],
        "passed":counts,"issues":issues,"live_auth_verified":False,"academic_approved":False,"release":False}
    (out/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False))
    return not issues and all(v==COUNTS[year] for v in counts.values())

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--year",type=int,choices=COUNTS,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    raise SystemExit(0 if run(a.year,a.out) else 1)
