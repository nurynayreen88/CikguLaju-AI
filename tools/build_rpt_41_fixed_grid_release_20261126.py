"""One-time free PDF candidate builder; never persist private Word files."""
import json, re, tempfile
from pathlib import Path
from hashlib import sha256
from concurrent.futures import ProcessPoolExecutor
import fitz
from docx import Document
from docx.oxml.ns import qn
from tools import build_kssr_rpt_merged_week_batch_20261126 as kssr
from tools import build_rpt_math_upper_native_word_20261126 as math
from tools import build_rpt_science_approved_word_20261126 as science
from tools import build_english_rpt_merged_week_word_pdf_20261126 as english
ROOT=Path("rpt_2027")
FOLDERS={"free":"compact_free_pdf_2027","approved":"compact_approved_pdf_2027","english":"compact_english_pdf_2027"}
LOCK=ROOT/"web_2027_pdfs"/"original_cover_layout_verified.json"
def read(path):return json.loads(path.read_text())
def digest(data):return sha256(data).hexdigest()
def build(task):
    group,key,entry=task
    subject,y=key.split(":");year=int(y)
    dest=ROOT/FOLDERS[group]/entry["path"]
    assert digest(dest.read_bytes())==entry["sha256"]
    with tempfile.TemporaryDirectory() as td:
        out=Path(td)
        if group=="free":
            kssr.render(subject,year,out,read(kssr.ROOT/"manifest.json"),read(LOCK))
        elif group=="approved":
            (math if subject=="matematik" else science).render(year,out)
        else:
            english.render(year,out)
        word=Document(next(out.glob("*.docx")))
        t=word.tables[0];pr=t._tbl.tblPr
        assert pr.find(qn("w:tblW")).get(qn("w:type"))=="dxa"
        assert int(pr.find(qn("w:tblW")).get(qn("w:w")))==sum(c.width.twips for c in t.columns)
        assert t.rows[0]._tr.trPr.find(qn("w:tblHeader")) is not None
        assert all(any(c.text.strip() for c in row.cells[1:]) for table in word.tables for row in table.rows[1:])
        headings=[re.sub(r"\s+"," ",c.text).strip().casefold() for c in t.rows[0].cells]
        candidate=next(out.glob("*.pdf"))
        with fitz.open(dest) as before,fitz.open(candidate) as after:
            assert before[0].get_pixmap().samples==after[0].get_pixmap().samples,key
            for page in list(after)[1:]:
                text=re.sub(r"\s+"," ",page.get_text()).strip().casefold()
                assert all(h in text for h in headings),(key,page.number,"header")
            data=candidate.read_bytes()
            update=dict(entry,sha256=digest(data),bytes=len(data),pages=len(after))
        print(key,"PASS",update["pages"],flush=True)
        return group,key,update,data
def main():
    manifests={g:read(ROOT/f/"manifest.json") for g,f in FOLDERS.items()}
    assert {g:len(m["files"]) for g,m in manifests.items()}=={"free":31,"approved":5,"english":5}
    lock=read(LOCK)
    jobs=[(g,k,e) for g,m in manifests.items() for k,e in m["files"].items()]
    with ProcessPoolExecutor(max_workers=3) as pool:results=list(pool.map(build,jobs))
    assert len(results)==41
    for group,key,entry,data in results:
        (ROOT/FOLDERS[group]/entry["path"]).write_bytes(data)
        manifests[group]["files"][key]=entry
        target=lock[{"free":"compact_pdf_covers","approved":"compact_approved_pdf_covers","english":"compact_english_pdf_covers"}[group]]
        if group=="approved":target=target[key]
        target["source_sha256_by_subject_year"][key]=entry["sha256"]
    for group,m in manifests.items():
        (ROOT/FOLDERS[group]/"manifest.json").write_text(json.dumps(m,indent=2)+"\n")
    LOCK.write_text(json.dumps(lock,indent=2)+"\n")
if __name__=="__main__":main()
