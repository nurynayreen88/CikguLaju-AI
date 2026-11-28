"""Validate proposed ordinary/5P alignment and print only the 12 new drafts."""
import json, subprocess, tempfile, sys
from pathlib import Path
from hashlib import sha256
from docx import Document
from web.rph_5p_v5_layout import FIELDS, PHASE_KEYS, Palette, MS_LABELS, render_word
from tools.audit_science_5p_layout_fixtures_20261128 import inspect_pdf
from tools.audit_science_y2_y4_native_pdf_20261128 import render_pdf
ROOT=Path(__file__).resolve().parents[1]
DRAFT="DRAF QA - BUKAN UNTUK PdP"
def read(path):return json.loads(path.read_text(encoding="utf-8"))
def main():
    out=Path(sys.argv[1]).resolve(); out.mkdir(parents=True,exist_ok=False)
    source_dir=Path(sys.argv[2]).resolve()
    data=read(ROOT/"audits/rph_science_y2_y4_167_ordinary_5p_sync_proposals_20261128.json")
    native={}
    for y in (2,3,4):
        rows=read(source_dir/f"qa_original_science_y{y}"/"curriculum_source.json")
        native.update({r["id"]:r for r in rows})
    assert len(native)==197
    records=data["records"]; assert len(records)==167 and len({r["lesson_id"] for r in records})==167
    marker=data["generic_marker"]
    generic={cid for cid,r in native.items() if marker in r["ordinary_fields"].get("AKTIVITI UTAMA","")}
    assert len(generic)==166 and generic-{r["lesson_id"] for r in records}=={"SCI-Y2-PDP-048"}
    colors=[r for r in read(ROOT/"web/rph_login_canonical_layout_20261121.json")["subjects"] if r["subject_code"]=="SCIENCE"]
    assert len(colors)==1
    c=colors[0]; palette=Palette(c["strong"].lstrip("#"),c["tone"].lstrip("#"),c["tone"].lstrip("#"),"9AB2B7")
    words=out/"word"; words.mkdir(); pdfs=out/"converted_pdf"; pdfs.mkdir(); direct=out/"independent_pdf"; direct.mkdir()
    issues=[]; manifest=[]; verified=0
    for r in records:
        cid=r["lesson_id"]; n=native[cid]
        try:
            assert r["ready"] is False and n["unit"]==r["unit"] and n["title"]==r["original_title"]
            assert sorted(s["sp_code"] for s in n["standards"])==sorted(r["sp_codes"])
            assert r["original_generic_marker"]==(cid in generic)
            assert len(set(r["phases"].values()))==5
            if r["kind"]=="RESTORE_PINNED_OPENING_PLAN":
                assert len(r["ordinary_rph_proposal"]["aktiviti_utama"])==2
            else:
                assert [a["text"] for a in r["ordinary_rph_proposal"]["aktiviti_utama"]]==[r["phases"][k] for k in ("exploration","explanation","elaboration")]
            verified+=1
            if r["kind"] not in ("SAME_SP_SCOPE_PROPOSAL","CODE_PRESERVING_TITLE_REPAIR"):continue
            support=r["support"]
            s=dict(subject="SAINS SK",year=r["year"],lesson_id=cid,curriculum="KSSR",topic=r["proposed_title"],sk="\n".join(dict.fromkeys(d["sk"] for d in r["dskp"])),sp="\n".join(d["code"]+" "+d["sp"] for d in r["dskp"]),objective=r["objective"],criteria=r["criterion"],closure=r["ordinary_rph_proposal"]["penutup"],aids_pak21_emk="BBM: "+support["bbm"]+"\nPAK21: "+support["pak21"]+"\nEMK: "+support["emk"],remedial_enrichment="Pemulihan: "+support["pemulihan"]+"\nPengayaan: "+support["pengayaan"],reflection="",reference="Draf QA. Tempoh, rujukan BT dan padanan RPT belum disahkan.")
            raw=json.dumps(s,ensure_ascii=False,sort_keys=True).encode()
            comp={k:s[k] for k in ("subject","year","lesson_id","curriculum")}; comp.update(source_sha256=sha256(raw).hexdigest(),phases=r["phases"])
            heading=f"SAINS SK\nTAHUN {r['year']}\n{DRAFT}"
            path=words/(cid+".docx"); path.write_bytes(render_word(s,comp,source_bytes=raw,palette=palette,subject_heading=heading))
            doc=Document(path); assert len(doc.tables)==1 and len(doc.tables[0].rows)==21
            t=doc.tables[0]
            for i,k in enumerate(FIELDS[:5],2):assert t.cell(i,1).text==s[k]
            for i,k in enumerate(PHASE_KEYS):assert t.cell(8+2*i,1).text==comp["phases"][k]
            for i,k in enumerate(FIELDS[5:-1],17):assert t.cell(i,1).text==s[k]
            expected=[DRAFT,*[s[k] for k in FIELDS],*comp["phases"].values(),s["reference"]]
            pdf=direct/(cid+".pdf"); pdf.write_bytes(render_pdf(s,comp,raw,dict.fromkeys(("class","date","time","students"),""),palette,heading))
            inspect_pdf(pdf,expected)
            manifest.append({"id":cid,"expected":expected})
        except Exception as exc:issues.append({"id":cid,"error":str(exc),"stage":"source or direct print"})
    with tempfile.TemporaryDirectory() as profile:
        paths=sorted(words.glob("*.docx"))
        if paths:subprocess.run(["libreoffice","-env:UserInstallation="+Path(profile).as_uri(),"--headless","--convert-to","pdf","--outdir",str(pdfs),*map(str,paths)],check=True,timeout=180)
    passed=0
    for row in manifest:
        try:inspect_pdf(pdfs/(row["id"]+".pdf"),row["expected"]); passed+=1
        except Exception as exc:issues.append({"id":row["id"],"stage":"converted pdf","error":str(exc)})
    report={"proposals":167,"source_identity_verified":verified,"new_draft_print_expected":12,"all_three_print_passed":passed,"issues":issues,"release":False}
    (out/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8"); print(json.dumps(report,ensure_ascii=False))
    return int(bool(issues) or verified!=167 or passed!=12)
if __name__=="__main__":raise SystemExit(main())
