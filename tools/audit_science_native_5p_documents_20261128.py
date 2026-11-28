"""Render source-adapted Science 5P documents for offline QA only.

Do not publish, install a route, or claim academic approval.
Word uses the approved shared layout; PDF is a conversion for layout QA.
"""
import argparse
import json
import re
import subprocess
import tempfile
from hashlib import sha1, sha256
from pathlib import Path

from docx import Document
from web.rph_5p_v5_layout import FIELDS, PHASE_KEYS, MS_LABELS, Palette, render_word
from tools.audit_science_5p_layout_fixtures_20261128 import inspect_pdf

ROOT = Path(__file__).resolve().parents[1]
COUNTS = {5: 116, 6: 89}
DRAFT = "DRAF QA - BUKAN UNTUK PdP"
PENDING = "Belum disahkan untuk versi 5P."

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def git_blob(data):
    return sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def inventory(year):
    audit = read(ROOT / f"audits/rph_5p_science_y{year}_native_complete_identity_audit_20261128.json")
    if (audit["count"] != COUNTS[year] or audit["unique"] != COUNTS[year]
            or audit["minutes"] != 3840 or audit["issues"] or audit["missing"]
            or audit["release"] is not False):
        raise ValueError(f"Unverified identity audit for Year {year}")
    rows = []
    for entry in audit["blobs"]:
        path = ROOT / entry["path"]
        data = path.read_bytes()
        if git_blob(data) != entry["sha"]:
            raise ValueError(f"Draft source blob changed: {path}")
        d = json.loads(data)
        if d["year"] != year or len(d["records"]) != entry["count"]:
            raise ValueError("Draft inventory mismatch")
        rows.extend(d["records"])
    expected = list(range(1, 117)) if year == 5 else [*range(85, 90), *range(1, 85)]
    if [r["lesson_id"] for r in rows] != [f"SK27-SCI-Y{year}-PDP-{n:03d}" for n in expected]:
        raise ValueError("Missing, duplicated or reordered lessons")
    if sum(r["minutes"] for r in rows) != 3840 or any(r["ready"] is not False for r in rows):
        raise ValueError("Invalid duration or release status")
    return rows

def fields(year, r):
    if year == 5:
        objective = criteria = r["original_pbd"]
        materials = r["original_materials"]
        safety = r.get("original_safety")
        sk = r.get("sk") or ("1.1 Kemahiran Proses Sains" if r["sp_code"].startswith("1.1.") else "")
        sp = r["sp_code"] + " " + r["sp_text"]
        closure = ("Guru meminta murid menyatakan satu langkah yang boleh diulang. Murid menyatakan satu perkara penting dalam tugas ini."
                   if r["lesson_id"][-3:] in {f"{i:03d}" for i in range(1,16)} or
                   "guide_teacher" in r.get("source_activity", {}) else
                   "Guru meminta murid mengaitkan bukti dengan tajuk. Murid menjelaskan satu dapatan dengan bukti aktiviti.")
        support = PENDING
    else:
        o = r["original"]
        objective, criteria, materials = o["objective"], o["pbd"], o["materials"]
        safety = o.get("safety")
        sk, sp = r["sk"], " · ".join(x["code"] + " " + x["text"] for x in r["sp"])
        closure = o.get("closure") or "Guru meminta murid mengaitkan bukti dengan tajuk. Murid menjelaskan satu dapatan dengan bukti aktiviti."
        support = o.get("support") or PENDING
        if r["lesson_id"].endswith("-014"):
            criteria = r["phases"]["evaluation"]
    if not sk.strip() or not sp.strip():
        raise ValueError("Missing full standards")
    unit, title = r["unit"], r["title"]
    # Correct only the known malformed display prefix; preserve exact source
    # identity in locked draft data and manifest, never alter the RPT.
    if year == 6 and unit == "Unit 5: Pemeliharaan dan":
        prefix = "Pemuliharaan Pemeliharaan dan Pemuliharaan — "
        if not title.startswith(prefix):
            raise ValueError("Unexpected conservation display title")
        unit = "Unit 5: Pemeliharaan dan Pemuliharaan"
        title = title[len(prefix):]
    aids = "BBM: " + materials + "\nPAK21 / EMK: " + PENDING
    if safety:
        aids += "\nKeselamatan: " + safety
    source = dict(subject="SAINS SK", year=year, lesson_id=r["lesson_id"], curriculum="KSSR",
                  topic=unit + "\n" + title, sk=sk, sp=sp,
                  objective=objective, criteria=criteria, closure=closure,
                  aids_pak21_emk=aids, remedial_enrichment=support, reflection="",
                  reference=f"Buku Teks Sains Tahun {year} SK, m/s {r['textbook_pages']} · Tempoh: {r['minutes']} minit")
    raw = json.dumps(source, ensure_ascii=False, sort_keys=True).encode("utf-8")
    companion = {k:source[k] for k in ("subject","year","lesson_id","curriculum")}
    companion.update(source_sha256=sha256(raw).hexdigest(), phases=r["phases"])
    return source, companion, raw

def run(out, year):
    out.mkdir(parents=True, exist_ok=False)
    words=out/"word"; words.mkdir()
    pdfs=out/"pdf"; pdfs.mkdir()
    color = [r for r in read(ROOT/"web/rph_login_canonical_layout_20261121.json")["subjects"] if r["subject_code"]=="SCIENCE"]
    if len(color)!=1:
        raise ValueError("Science palette unavailable")
    c=color[0]
    palette=Palette(c["strong"].lstrip("#"),c["tone"].lstrip("#"),c["tone"].lstrip("#"),"9AB2B7")
    rows=inventory(year)
    manifest=[]; issues=[]
    heading=f"SAINS SK\nTAHUN {year}\n{DRAFT}"
    for r in rows:
        cid=r["lesson_id"]
        try:
            source, companion, raw=fields(year,r)
            path=words/(cid+".docx")
            path.write_bytes(render_word(source,companion,source_bytes=raw,palette=palette,subject_heading=heading))
            doc=Document(path)
            if len(doc.tables)!=1 or len(doc.tables[0].rows)!=21:
                raise ValueError("Expected one premium table, 21 rows")
            t=doc.tables[0]
            if "Kelas:" not in t.cell(1,0).text or t.cell(1,1).text!=heading:
                raise ValueError("Header orientation mismatch")
            for i,key in enumerate(FIELDS[:5],2):
                if t.cell(i,1).text!=source[key]:
                    raise ValueError("Word source mismatch: "+key)
            for i,key in enumerate(PHASE_KEYS):
                if t.cell(8+2*i,1).text!=r["phases"][key]:
                    raise ValueError("Word phase mismatch: "+key)
            if t.cell(20,0).text!="Refleksi":
                raise ValueError("Reflection label")
            manifest.append({"id":cid,"source_title":r["title"],"source_digest":companion["source_sha256"],
                "expected":[DRAFT,*MS_LABELS[5:],*[source[k] for k in FIELDS],*[r["phases"][k] for k in PHASE_KEYS],source["reference"]],
                "ready":False})
        except Exception as exc:
            issues.append({"id":cid,"stage":"word","error":str(exc)})
    paths=sorted(words.glob("*.docx"))
    try:
        with tempfile.TemporaryDirectory() as profile:
            for i in range(0,len(paths),40):
                subprocess.run(["libreoffice","-env:UserInstallation="+Path(profile).as_uri(),
                    "--headless","--convert-to","pdf","--outdir",str(pdfs),*map(str,paths[i:i+40])],
                    check=True,timeout=180)
    except (OSError,subprocess.SubprocessError) as exc:
        issues.append({"stage":"conversion","error":str(exc)})
    passed=0
    for r in manifest:
        try:
            inspect_pdf(pdfs/(r["id"]+".pdf"),r["expected"])
            passed+=1
        except Exception as exc:
            issues.append({"id":r["id"],"stage":"pdf","error":str(exc)})
    report={"status":"NATIVE_SOURCE_ADAPTED_DRAFT_LAYOUT_QA_ONLY","year":year,
            "total":COUNTS[year],"word_generated":len(manifest),"word_pdf_passed":passed,
            "academic_approved":False,"native_pdf_delivery_verified":False,"release":False,"issues":issues}
    (out/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    (out/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False))
    return not issues and passed==COUNTS[year]

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--year",required=True,type=int,choices=COUNTS)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    raise SystemExit(0 if run(a.out,a.year) else 1)
