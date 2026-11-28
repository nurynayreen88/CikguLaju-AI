"""Private layout QA for consolidated Science native drafts, never a release."""
import argparse
import json
from pathlib import Path
from hashlib import sha1, sha256
import subprocess
import tempfile
from docx import Document
from web.rph_5p_v5_layout import FIELDS, PHASE_KEYS, Palette, render_word
from tools.audit_science_5p_layout_fixtures_20261128 import inspect_pdf

ROOT=Path(__file__).resolve().parents[1]
INDEX=ROOT/"audits/rph_5p_science_y2_y3_y4_consolidated_197_20261128.json"
COUNTS={2:48,3:36,4:78}
DRAFT="DRAF QA - BUKAN UNTUK PdP"
PENDING="Belum disahkan dengan RPH asal."

def blob(raw):
    return sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def inputs(year):
    index=load(INDEX)
    rows=index["records"]
    if len(rows)!=197 or len({r["lesson_id"] for r in rows})!=197:
        raise ValueError("Native index mismatch")
    if sum(r["status"]=="HOLD" for r in rows)!=13 or any(r["ready"] is not False for r in rows):
        raise ValueError("Release gate mismatch")
    source_cache={}
    selected=[r for r in rows if r["year"]==year and not r["opening"] and r["status"]=="DRAFT_MATCHED_NOT_RELEASED"]
    if len(selected)!=COUNTS[year]:
        raise ValueError("Wrong year count")
    for idx in selected:
        path=idx["draft_file"]
        if path not in index["source_files"] or idx["draft_blob"]!=index["source_files"][path]:
            raise ValueError("Unpinned input")
        if path not in source_cache:
            raw=(ROOT/path).read_bytes()
            if blob(raw)!=idx["draft_blob"]:
                raise ValueError("Input bytes changed: "+path)
            recs=json.loads(raw)["records"]
            source_cache[path]={r["lesson_id"]:r for r in recs}
            if len(source_cache[path])!=len(recs):
                raise ValueError("Duplicate input ID")
        r=source_cache[path][idx["lesson_id"]]
        if (r["year"]!=year or r["unit"]!=idx["unit"] or r["native_title"]!=idx["title"]
            or sorted(s["code"] for s in r["dskp"])!=sorted(idx["sp_codes"])
            or r["ready"] is not False or not idx["identity_matched"] or not idx["five_phases_valid"]):
            raise ValueError("Identity changed: "+idx["lesson_id"])
        yield idx,r

def fixture(idx,r):
    support=r.get("support") or r.get("suggested_support") or {}
    if any(not support.get(k) for k in ("bbm","pak21","emk","pemulihan","pengayaan")):
        raise ValueError("Missing draft support")
    obj=r.get("objective") or r.get("proposed_objective_and_criterion")
    crit=r.get("criterion") or r.get("proposed_objective_and_criterion")
    if not obj or not crit:
        raise ValueError("Missing draft objective/criterion")
    # Preserve candidate wording. Unknown ordinary-RPH closure is explicitly pending.
    ref=idx.get("textbook_pages_reference")
    ref_text=("Rujukan BT: m/s "+ref+" (pemetaan terdahulu). " if ref else "Rujukan BT belum disahkan. ")
    source=dict(subject="SAINS SK",year=idx["year"],lesson_id=idx["lesson_id"],curriculum="KSSR",
        topic=idx["title"],sk="\n".join(dict.fromkeys(s["sk"] for s in r["dskp"])),
        sp="\n".join(s["code"]+" "+s["sp"] for s in r["dskp"]),
        objective=obj,criteria=crit,closure=PENDING,
        aids_pak21_emk="BBM: "+support["bbm"]+"\nPAK21: "+support["pak21"]+"\nEMK: "+support["emk"],
        remedial_enrichment="Pemulihan: "+support["pemulihan"]+"\nPengayaan: "+support["pengayaan"],
        reflection="",reference=ref_text+"Tempoh dan kandungan RPH asal belum disahkan.")
    raw=json.dumps(source,ensure_ascii=False,sort_keys=True).encode()
    companion={k:source[k] for k in ("subject","year","lesson_id","curriculum")}
    companion.update(source_sha256=sha256(raw).hexdigest(),phases=r["phases"])
    return source,companion,raw

def run(year,out):
    out.mkdir(parents=True,exist_ok=False)
    words=out/"word"; words.mkdir()
    pdfs=out/"pdf"; pdfs.mkdir()
    palette_rows=load(ROOT/"web/rph_login_canonical_layout_20261121.json")["subjects"]
    colors=[r for r in palette_rows if r["subject_code"]=="SCIENCE"]
    if len(colors)!=1: raise ValueError("Science palette unavailable")
    c=colors[0]
    palette=Palette(c["strong"].lstrip("#"),c["tone"].lstrip("#"),c["tone"].lstrip("#"),"9AB2B7")
    manifest=[]; issues=[]
    for idx,r in inputs(year):
        cid=idx["lesson_id"]
        try:
            source,comp,raw=fixture(idx,r)
            heading=f"SAINS SK\nTAHUN {year}\n{DRAFT}"
            path=words/(cid+".docx")
            path.write_bytes(render_word(source,comp,source_bytes=raw,palette=palette,subject_heading=heading))
            doc=Document(path)
            if len(doc.tables)!=1 or len(doc.tables[0].rows)!=21:
                raise ValueError("One 21-row table required")
            t=doc.tables[0]
            if "Kelas:" not in t.cell(1,0).text or t.cell(1,1).text!=heading:
                raise ValueError("Header orientation")
            for i,k in enumerate(FIELDS[:5],2):
                if t.cell(i,1).text!=source[k]: raise ValueError("Field mismatch: "+k)
            for i,k in enumerate(PHASE_KEYS):
                if t.cell(8+2*i,1).text!=comp["phases"][k]: raise ValueError("Phase mismatch: "+k)
            for i,k in enumerate(FIELDS[5:-1],17):
                if t.cell(i,1).text!=source[k]: raise ValueError("Field mismatch: "+k)
            if t.cell(20,0).text!="Refleksi": raise ValueError("Reflection label")
            if cid in "\n".join(c.text for row in t.rows for c in row.cells):
                raise ValueError("Internal lesson ID printed")
            manifest.append({"id":cid,"ready":False,"expected":[DRAFT,*[source[k] for k in FIELDS],*comp["phases"].values(),source["reference"]]})
        except Exception as exc:
            issues.append({"id":cid,"stage":"word","error":str(exc)})
    paths=sorted(words.glob("*.docx"))
    try:
        with tempfile.TemporaryDirectory() as profile:
            for i in range(0,len(paths),30):
                subprocess.run(["libreoffice","-env:UserInstallation="+Path(profile).as_uri(),"--headless","--convert-to","pdf","--outdir",str(pdfs),*map(str,paths[i:i+30])],check=True,timeout=180)
    except (OSError,subprocess.SubprocessError) as exc:
        issues.append({"stage":"conversion","error":str(exc)})
    passed=0
    for row in manifest:
        try:
            inspect_pdf(pdfs/(row["id"]+".pdf"),row["expected"])
            passed+=1
        except Exception as exc:
            issues.append({"id":row["id"],"stage":"pdf","error":str(exc)})
    report={"year":year,"expected":COUNTS[year],"word_verified":len(manifest),"word_pdf_verified":passed,
            "native_pdf_verified":False,"production_source_verified":False,"release":False,"issues":issues}
    (out/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    (out/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False))
    return passed==COUNTS[year] and not issues

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--year",type=int,choices=COUNTS,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    raise SystemExit(0 if run(a.year,a.out) else 1)
