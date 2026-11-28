"""Render layout-only QA fixtures, never release or change the native RPH.

The candidate's DSKP and 5P texts are preserved. Unavailable ordinary RPH
fields are explicitly marked pending; the fixture digest is NOT a production
source digest. PDF is LibreOffice conversion of Word, not native delivery.
"""
import argparse
import json
import re
import subprocess
import tempfile
from hashlib import sha256, sha1
from pathlib import Path
from unicodedata import normalize

import fitz
from docx import Document
from web.rph_5p_v5_layout import FIELDS, PHASE_KEYS, MS_LABELS, Palette, render_word

ROOT = Path(__file__).resolve().parents[1]
COUNTS = {2:47, 3:40, 4:47, 5:51, 6:47}
PENDING = "Belum dipadankan dengan RPH asal."
DRAFT = "DRAF QA - BUKAN UNTUK PdP"

def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

def inputs():
    palette_rows = load_json(ROOT/"web/rph_login_canonical_layout_20261121.json")["subjects"]
    colors = [r for r in palette_rows if r["subject_code"]=="SCIENCE"]
    if len(colors)!=1:
        raise ValueError("Science palette missing or ambiguous")
    color=colors[0]
    # Border is a QA-only neutral choice, not a newly approved production palette.
    palette=Palette(color["strong"].lstrip("#"),color["tone"].lstrip("#"),
                    color["tone"].lstrip("#"),"9AB2B7")
    all_ids=set()
    for year,count in COUNTS.items():
        p=ROOT/f"audits/rph_5p_science_kssr_t{year}_dskp_candidates_20261128.json"
        idx=load_json(ROOT/f"audits/rph_5p_science_t{year}_textbook_topic_references_20261128.json")
        data=p.read_bytes()
        blob=sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
        if idx["source_candidate_blob"]!=blob:
            raise ValueError(f"Year {year}: candidate source changed")
        records=json.loads(data)["records"]
        refs={r["candidate_id"]:r for r in idx["records"]}
        if len(records)!=count or len(idx["records"])!=count or len(refs)!=count:
            raise ValueError(f"Year {year}: incomplete or duplicate inventory")
        for r in records:
            cid=r["candidate_id"]
            if cid in all_ids or not re.fullmatch(rf"SCI-T{year}-DRAFT-\d{{3}}",cid):
                raise ValueError("Invalid candidate identity")
            all_ids.add(cid)
            ref=refs[cid]
            if (r["ready"] is not False or ref["ready"] is not False or
                ref["title"]!=r["title"] or
                ref["sp_codes"]!=[s["code"] for s in r["dskp"]]):
                raise ValueError("Candidate/index mismatch")
            pages=ref["suggested_printed_pages"]
            if len(pages)!=2 or not all(type(x) is int for x in pages) or not 1<=pages[0]<=pages[1]:
                raise ValueError("Invalid proposed textbook range")
            yield year,r,pages,palette

def fixture(year,r,pages):
    source=dict(subject="SAINS SK",year=year,lesson_id=r["candidate_id"],curriculum="KSSR",
        topic=r["title"],sk="\n".join(dict.fromkeys(s["sk"] for s in r["dskp"])),
        sp="\n".join(s["code"]+" "+s["sp"] for s in r["dskp"]),
        objective=PENDING,criteria=PENDING,closure=PENDING,
        aids_pak21_emk=PENDING,remedial_enrichment=PENDING,reflection="",
        reference=f"Cadangan rujukan BT: hlm. {pages[0]}–{pages[1]} (julat tajuk; belum disahkan pada PdP).")
    raw=json.dumps(source,ensure_ascii=False,sort_keys=True).encode("utf-8")
    companion={k:source[k] for k in ("subject","year","lesson_id","curriculum")}
    companion.update(source_sha256=sha256(raw).hexdigest(),phases=r["phases"])
    return source,companion,raw

def norm(s):
    s=normalize("NFKC",s).replace("\u00ad","")
    s=re.sub(r"(?<=\w)-[ \t]*\r?\n[ \t]*(?=\w)","-",s)
    return "".join(s.split())

def inspect_pdf(path,expected):
    with fitz.open(path) as pdf:
        if len(pdf)!=1:
            raise ValueError(f"Expected one A4 page, got {len(pdf)}")
        page=pdf[0]
        if abs(page.rect.width-595.28)>2 or abs(page.rect.height-841.89)>2:
            raise ValueError("Not A4")
        txt=norm(page.get_text(flags=fitz.TEXTFLAGS_TEXT & ~fitz.TEXT_PRESERVE_LIGATURES))
        for term in expected:
            if term and norm(term) not in txt:
                raise ValueError("Missing text: "+term[:100])
        for block in page.get_text("blocks"):
            if block[6]==0 and not page.rect.contains(fitz.Rect(block[:4])):
                raise ValueError("Text outside page")
        return len(pdf)

def run(out):
    out.mkdir(parents=True,exist_ok=False)
    words=out/"word";words.mkdir()
    pdfs=out/"pdf";pdfs.mkdir()
    manifest=[];issues=[]
    for year,r,pages,palette in inputs():
        cid=r["candidate_id"]
        try:
            source,companion,raw=fixture(year,r,pages)
            # Internal fixture identifier is not printed in the document.
            heading=f"SAINS SK\nTAHUN {year}\n{DRAFT}"
            path=words/(cid+".docx")
            path.write_bytes(render_word(source,companion,source_bytes=raw,
                                         palette=palette,subject_heading=heading))
            word=Document(path)
            if len(word.tables)!=1 or len(word.tables[0].rows)!=21:
                raise ValueError("Expected one table, 21 rows")
            t=word.tables[0]
            if "Kelas:" not in t.cell(1,0).text or heading!=t.cell(1,1).text:
                raise ValueError("Header orientation")
            for i,key in enumerate(PHASE_KEYS):
                if t.cell(8+2*i,1).text!=r["phases"][key]:
                    raise ValueError("Word phase mismatch")
            if t.cell(20,0).text!="Refleksi":
                raise ValueError("Reflection label")
            manifest.append({"id":cid,"year":year,"ready":False,
                "expected":[DRAFT,*MS_LABELS[5:],*[source[k] for k in FIELDS],
                            *[r["phases"][k] for k in PHASE_KEYS],source["reference"]]})
        except Exception as e:
            issues.append({"id":cid,"stage":"word","error":str(e)})
    if len(manifest)+len(issues)!=sum(COUNTS.values()):
        raise ValueError("Incomplete fixture output")
    paths=sorted(words.glob("*.docx"))
    try:
        with tempfile.TemporaryDirectory() as profile:
            for i in range(0,len(paths),40):
                subprocess.run(["libreoffice","-env:UserInstallation="+Path(profile).as_uri(),
                                "--headless","--convert-to","pdf","--outdir",str(pdfs),
                                *map(str,paths[i:i+40])],check=True,timeout=180)
    except (OSError,subprocess.SubprocessError) as e:
        issues.append({"stage":"conversion","error":type(e).__name__})
    passed=0
    for row in manifest:
        try:
            inspect_pdf(pdfs/(row["id"]+".pdf"),row["expected"])
            passed+=1
        except Exception as e:
            issues.append({"id":row["id"],"stage":"pdf","error":str(e)})
    report={"status":"LAYOUT_FIXTURE_QA_ONLY","total":sum(COUNTS.values()),
            "word_generated":len(manifest),"word_pdf_passed":passed,
            "production_source_verified":False,"release":False,"issues":issues}
    (out/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False))
    return not issues and passed==sum(COUNTS.values())

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    raise SystemExit(0 if run(args.out) else 1)
