"""Source-locked opening Science 5P draft QA, no production registration.
Full SP wording is checked against the project DSKP file manifest;
current catalogue coverage and duration remain pending. Never overwrite ordinary RPH or RPT.
"""
import json
from pathlib import Path
from hashlib import sha1, sha256
from io import BytesIO
from docx import Document
from web import sains_unit_awal as opening, sains_y3_unit_awal as y3
from web.sains_opening_pedagogy_20261121 import pedagogy_for_plan
from web.rph_5p_v5_layout import Palette, FIELDS, PHASE_KEYS, render_word

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/"audits/rph_5p_science_y2_y3_y4_opening_22_drafts_20261128.json"
def git_blob(raw):
    return sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def records():
    d=json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected={p.code:p for p in (*opening.LESSONS,*y3.LESSONS) if p.year in (2,3,4)}
    if len(expected)!=22 or d["total"]!=22 or len(d["records"])!=22:
        raise ValueError("Opening inventory mismatch")
    seen=set()
    for r in d["records"]:
        cid=r["lesson_id"]
        if cid in seen or cid not in expected:
            raise ValueError("Opening identity mismatch")
        seen.add(cid)
        p=expected[cid]
        expected_path="web/sains_y3_unit_awal.py" if p.year==3 else "web/sains_unit_awal.py"
        if r["source_path"]!=expected_path or git_blob((ROOT/expected_path).read_bytes())!=r["source_blob"]:
            raise ValueError("Original opening source changed")
        if (r["year"]!=p.year or r["title"]!=p.title or r["textbook_pages"]!=p.pages
                or r["sp_codes"]!=list(p.standards) or r["ready"] is not False or r["duration"] is not None):
            raise ValueError("Opening plan metadata changed")
        for k in ("objective","materials","induction","guided","independent","assessment","closure","follow_up"):
            if r["original"][k]!=getattr(p,k):
                raise ValueError("Original plan field changed: "+k)
        if r["phases"]["engagement"]!=p.induction or r["phases"]["elaboration"]!=p.independent or r["phases"]["evaluation"]!=p.assessment:
            raise ValueError("Original source activity or PBD changed")
        yield r,p
    if seen!=set(expected):
        raise ValueError("Incomplete opening identities")

def prepare(r,p):
    standards=json.loads((ROOT/'audits/rph_5p_science_y2_y3_y4_opening_dskp_text_20261128.json').read_text(encoding='utf-8'))
    if standards['source_manifest_blob']!=git_blob(MANIFEST.read_bytes()) or standards['total_lessons']!=22:
        raise ValueError('DSKP source mapping changed')
    descriptions={code:item['text'] for code,item in standards['years'][str(p.year)]['standards'].items()}
    teaching=pedagogy_for_plan(p)
    data=dict(subject="SAINS SK",year=p.year,lesson_id=p.code,curriculum="KSSR",
        topic=p.unit+" / "+p.title,sk=p.sk+" "+y3.SK[p.sk],
        sp="\n".join(code+" "+descriptions[code] for code in p.standards),
        objective=p.objective,criteria=p.objective,closure=p.closure,
        aids_pak21_emk="BBM: "+p.materials+"\n"+teaching["KBAT / PAK21"]+"\nEMK: "+teaching["EMK / NILAI"],
        remedial_enrichment=p.follow_up,reflection="",
        reference=f"Buku Teks Sains Tahun {p.year} SK, m/s {p.pages}. Draf: semak tempoh dan katalog aktif.")
    raw=json.dumps(data,sort_keys=True,ensure_ascii=False).encode("utf-8")
    c={k:data[k] for k in ("subject","year","lesson_id","curriculum")}
    c.update(source_sha256=sha256(raw).hexdigest(),phases=r["phases"])
    return data,c,raw

def main():
    out=ROOT/"qa_science_opening_5p"
    out.mkdir(exist_ok=False)
    color=[r for r in json.loads((ROOT/"web/rph_login_canonical_layout_20261121.json").read_text())["subjects"] if r["subject_code"]=="SCIENCE"]
    if len(color)!=1:raise ValueError("Science palette missing")
    c=color[0]
    palette=Palette(c["strong"].lstrip("#"),c["tone"].lstrip("#"),c["tone"].lstrip("#"),"9AB2B7")
    report=[]
    for row,p in records():
        s,c,raw=prepare(row,p)
        docx=render_word(s,c,source_bytes=raw,palette=palette,subject_heading=f"SAINS SK\nTAHUN {p.year}\nDRAF QA")
        doc=Document(BytesIO(docx))
        if len(doc.tables)!=1 or len(doc.tables[0].rows)!=21:raise ValueError("Unexpected layout")
        t=doc.tables[0]
        for i,k in enumerate(FIELDS[:5],2):
            if t.cell(i,1).text!=s[k]:raise ValueError("Source print mismatch")
        for i,k in enumerate(PHASE_KEYS):
            if t.cell(8+2*i,1).text!=c["phases"][k]:raise ValueError("Phase print mismatch")
        (out/(p.code+".docx")).write_bytes(docx)
        report.append(dict(id=p.code,year=p.year,expected=[s[k] for k in FIELDS if k!="reflection"]+list(c["phases"].values())+[s["reference"],"DRAF QA"],ready=False))
    assert len(report)==22
    (out/"manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Verified 22 original opening plans and generated 22 draft Word documents")
if __name__=="__main__":main()
