"""Exercise all 205 personalized draft downloads in both reflection modes.
Uses a Flask test client and synthetic paid account. Supports actual pinned original catalogue and LibreOffice pagination checks.
Never connects to production or charges real credits.
"""
import argparse
import json
import subprocess
import tempfile
import os
from contextlib import ExitStack
from unittest.mock import patch
from io import BytesIO
from pathlib import Path
from flask import Flask
from docx import Document
from tools.audit_science_native_5p_documents_20261128 import inventory,support_inventory,fields,display_fields,COUNTS
from tools.audit_science_5p_layout_fixtures_20261128 import inspect_pdf
from tools.science_5p_native_selection_preflight_20261128 import map_catalogue
from tools.science_5p_web_integration_qa_20261128 import create_test_blueprint,URL,ORIGIN
from web.rph_5p_v5_layout import FIELDS,PHASE_KEYS,MS_LABELS

def run(year,out,native_catalogue=None,check_word_pages=False,published=False):
    if published and native_catalogue is None:
        raise ValueError('Published QA requires pinned original catalogue')
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
    if native_catalogue is not None:
        catalogue=json.loads(native_catalogue.read_text(encoding="utf-8"))
        if catalogue.get("unavailable") != []:
            raise ValueError("Original catalogue contains unavailable selections")
    mapping=map_catalogue(year,catalogue,drafts)
    words=out/"word"; converted=out/"converted"
    if check_word_pages:
        words.mkdir(); converted.mkdir()
    word_manifest=[]
    def debit(*args,**kwargs):
        raise AssertionError("Paid QA account must not debit")
    app=Flask(__name__);app.testing=True
    account={"telegram_user_id":42,"authenticated":True,"free_remaining":0,"rakan_pembangun":True}
    stack=ExitStack()
    if published:
        from web import science_5p_candidate_web as candidate, science_5p_release as gate
        from web_v1_sessions import issue_session_ticket
        secret="science-published-test-only-not-production"
        approved={k:dict(v,ready=True,status="APPROVED_FOR_RELEASE") for k,v in gate.records().items()}
        original_units=list({m["unit"]:{"value":m["unit"],"label":m["native_unit_label"]} for m in mapping.values()}.values())
        original_lessons={u["value"]:[{"value":m["lesson"],"label":m["native_label"],"textbook_ref":"Buku Teks m/s "+str(m["source_pages"])} for m in mapping.values() if m["unit"]==u["value"]] for u in original_units}
        stack.enter_context(patch.dict(os.environ,{gate.FLAG:"1"}))
        stack.enter_context(patch.object(gate,"records",return_value=approved))
        stack.enter_context(patch.object(candidate,"_config",return_value={"account_backend":"supabase","CIKGULAJU_WEB_SESSION_SECRET":secret,"supabase_url":"https://example.invalid","supabase_key":"test-only"}))
        stack.enter_context(patch.object(candidate,"_lookup",return_value=account))
        stack.enter_context(patch.object(candidate,"debit_shared_trial",side_effect=debit))
        stack.enter_context(patch.object(candidate.native,"list_native_units",return_value=original_units))
        stack.enter_context(patch.object(candidate.native,"list_native_lessons",side_effect=lambda y,s,u:original_lessons[u]))
        stack.enter_context(patch.object(candidate.native,"verified_native_sequence_available",return_value=True))
        app.register_blueprint(candidate.create_blueprint(published=True))
        url="/api/kssr/sk/science/5p/download"
    else:
        app.register_blueprint(create_test_blueprint(account_for_request=lambda req:(42,account),
            mapping_for_year=lambda y:mapping,rows=rows,support=support,debit=debit))
        url=URL
    client=app.test_client()
    if published:
        client.set_cookie(candidate.COOKIE,issue_session_ticket(42,secret))
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
                    resp=client.post(url,json={**payload,"format":fmt},headers={"Origin":ORIGIN})
                    if resp.status_code!=200:
                        raise ValueError(f"HTTP {resp.status_code}: {resp.get_json()}")
                    if published and (resp.headers.get("X-RPH-QA-Status")!="INTERNAL-REVIEWED" or "DRAF_QA" in resp.headers.get("Content-Disposition","")):
                        raise ValueError("Published response status/name mismatch")
                    if "X-RPH-Trial-Remaining" in resp.headers:
                        raise ValueError("Paid account charged")
                    if fmt=="word":
                        d=Document(BytesIO(resp.data))
                        if len(d.tables)!=1 or len(d.tables[0].rows)!=21:
                            raise ValueError("Wrong Word layout")
                        t=d.tables[0]
                        if published and t.cell(1,1).text!=f"SAINS SK\nTAHUN {year}":
                            raise ValueError('Unexpected publication heading')
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
                        if check_word_pages:
                            file=words/f"{cid}_{mode}.docx"
                            file.write_bytes(resp.data)
                            word_manifest.append((file,cid,mode,[*MS_LABELS[5:],
                                *[s[k] for k in FIELDS if k!="reflection"],
                                *[c["phases"][k] for k in PHASE_KEYS],s["reference"],reflection,
                                f"{year} Bestari","02/03/2027","08:00",payload["teacher_end"],"30"]))
                    else:
                        file=out/f"{cid}_{mode}.pdf"
                        file.write_bytes(resp.data)
                        inspect_pdf(file,[*MS_LABELS[5:],*[s[k] for k in FIELDS if k!="reflection"],
                            *[c["phases"][k] for k in PHASE_KEYS],s["reference"],reflection,
                            f"{year} Bestari","02/03/2027","08:00",payload["teacher_end"],"30"])
                        if published:
                            import fitz
                            with fitz.open(file) as pdf:
                                if "DRAF QA" in pdf[0].get_text():raise ValueError("Draft watermark on publication PDF")
                        file.unlink()
                    counts[mode+"_"+fmt]+=1
                except Exception as exc:
                    issues.append({"id":cid,"mode":mode,"format":fmt,"error":str(exc)})
    stack.close()
    word_pages_passed=0
    if check_word_pages:
        paths=sorted(words.glob("*.docx"))
        try:
            with tempfile.TemporaryDirectory() as profile:
                for i in range(0,len(paths),40):
                    subprocess.run(["libreoffice","-env:UserInstallation="+Path(profile).as_uri(),
                        "--headless","--convert-to","pdf","--outdir",str(converted),*map(str,paths[i:i+40])],
                        check=True,timeout=180)
        except (OSError,subprocess.SubprocessError) as exc:
            issues.append({"stage":"personalized_word_conversion","error":str(exc)})
        for file,cid,mode,expected in word_manifest:
            try:
                inspect_pdf(converted/(file.stem+".pdf"),expected)
                word_pages_passed+=1
            except Exception as exc:
                issues.append({"id":cid,"mode":mode,"stage":"personalized_word_pagination","error":str(exc)})
        if word_pages_passed!=2*COUNTS[year]:
            issues.append({"stage":"personalized_word_pagination","error":"Incomplete single-page Word audit"})
    report={"status":"PUBLISHED_ROUTE_SIMULATION_QA_ONLY" if published else "PERSONALIZED_DRAFT_TEST_CLIENT_QA_ONLY","year":year,"records":COUNTS[year],
        "passed":counts,"catalogue":"pinned_original_endpoint" if native_catalogue else "synthetic",
        "personalized_word_pagination_checked":check_word_pages,"personalized_word_single_page_passed":word_pages_passed,"issues":issues,"live_auth_verified":False,"academic_approved":False,"release":False}
    (out/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False))
    return not issues and all(v==COUNTS[year] for v in counts.values())

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--year",type=int,choices=COUNTS,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--native-catalogue",type=Path)
    p.add_argument("--check-word-pages",action="store_true")
    p.add_argument("--published",action="store_true")
    a=p.parse_args()
    raise SystemExit(0 if run(a.year,a.out,a.native_catalogue,a.check_word_pages,a.published) else 1)
