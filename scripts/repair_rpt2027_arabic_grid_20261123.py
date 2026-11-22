"""Fix missing INNER COLUMN dividers in five existing Arabic KSSR RPT PDFs.

Vector strokes only: no OCR, no text/image overlay, no PDF rebuilding,
no curriculum rewriting and no Web route changes. Arabic RTL order stays:
  left CATATAN | SP | SK | UNIT/TAJUK | MINGGU right.
Original cover graphics, clickable source links and 51 other PDFs stay intact.
All five remain DRAF.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import tempfile
from pathlib import Path
import fitz

ROOT=Path("rpt_2027/web_2027_pdfs")
ASSET="bahasa_arab"
YEARS=(2,3,4,5,6)
TABLE_LEFT=35.0
TABLE_RIGHT=818.89
BODY_RIGHT=713.89
INNER_X=(193.0,403.0,528.0)
HEADER_X=INNER_X+(BODY_RIGHT,)
HEADER_Y=(49.0,78.7)
COLOR=(0.58,0.64,0.66)
WIDTH=0.65
AUDIT=Path("qa_rpt_arab_grid/repaired_audit.json")


def digest(b):
    return hashlib.sha256(b).hexdigest()


def text_snapshot(doc):
    return [page.get_text("text",sort=False) for page in doc]


def links_snapshot(doc):
    pages=[]
    for page in doc:
        links=[]
        for link in page.get_links():
            box=link["from"]
            links.append((link["kind"],link.get("uri"),link.get("page"),
                         tuple(round(v,2) for v in box)))
        pages.append(links)
    return pages


def vertical_rules(page):
    for path in page.get_drawings():
        for entry in path.get("items",[]):
            if entry[0] != "l":
                continue
            a,b=entry[1:3]
            if abs(a.x-b.x)<0.8 and abs(a.y-b.y)>7:
                yield a.x,min(a.y,b.y),max(a.y,b.y)


def near_rule(lines,x,y0,y1):
    return any(abs(rx-x)<1 and abs(ry0-y0)<1.5 and abs(ry1-y1)<1.5
               for rx,ry0,ry1 in lines)


def row_boxes(page):
    found=[]
    for path in page.get_drawings():
        if path.get("color") is None:
            continue
        for item in path.get("items",[]):
            if item[0] != "re":
                continue
            r=item[1]
            if (abs(r.x0-TABLE_LEFT)<1 and abs(r.x1-BODY_RIGHT)<1
                and 78<r.y0<552 and 16<r.height<170 and r.y1<553):
                found.append((r.y0,r.y1))
    found=sorted(set((round(a,2),round(b,2)) for a,b in found))
    if not 1<=len(found)<=12:
        raise ValueError("Unrecognized Arabic source row geometry")
    for i, (a,b) in enumerate(found):
        if i and a<found[i-1][1]-0.8:
            raise ValueError("Overlapping Arabic row geometry")
    return found


def cells(page):
    lines=list(vertical_rules(page))
    boxes=row_boxes(page)
    expected=[(x,HEADER_Y[0],HEADER_Y[1]) for x in HEADER_X]
    expected.extend((x,a,b) for a,b in boxes for x in INNER_X)
    present=sum(near_rule(lines,*rule) for rule in expected)
    return boxes,expected,present


def check_final(doc):
    total=0
    for page in list(doc)[1:]:
        boxes,expected,have=cells(page)
        if have!=len(expected):
            raise ValueError(f"Not all Arabic RPT separators present p{page.number+1}: {have}/{len(expected)}")
        total+=len(expected)
    return total


def apply_one(file,out_dir):
    raw=file.read_bytes()
    if not raw.startswith(b"%PDF-"):
        raise ValueError("Not original PDF")
    with fitz.open(stream=raw,filetype="pdf") as source:
        if not 3<=len(source)<=50 or any(p.rect.width<p.rect.height for p in source):
            raise ValueError("Arabic landscape RPT page format unsupported")
        before_text=text_snapshot(source)
        before_links=links_snapshot(source)
        before_first=source[0].get_pixmap(matrix=fitz.Matrix(1.0,1.0)).samples
        work=[]
        count=0
        for page in list(source)[1:]:
            boxes,expected,existing=cells(page)
            if existing not in (0,len(expected)):
                raise ValueError("Partially ruled Arabic PDF: refuse duplicate/unsafe repair")
            if not existing:
                shape=page.new_shape()
                for x,y0,y1 in expected:
                    shape.draw_line(fitz.Point(x,y0),fitz.Point(x,y1))
                shape.finish(color=COLOR,width=WIDTH)
                shape.commit(overlay=True)
                count+=len(expected)
            work.append({"page":page.number+1,"rows":len(boxes),
                         "expected_separators":len(expected),"drawn":0 if existing else len(expected)})
        if count==0:
            check_final(source)
            return {"before_sha256":digest(raw),"after_sha256":digest(raw),
                    "bytes":len(raw),"pages":len(source),"added":0,
                    "links":sum(map(len,before_links)),"pages_audited":work,
                    "already_fixed":True}
        Path(out_dir).mkdir(parents=True,exist_ok=True)
        with tempfile.NamedTemporaryFile(suffix=".pdf",delete=False) as temp:
            tmp=Path(temp.name)
        try:
            source.save(str(tmp),garbage=4,deflate=True)
            revised=tmp.read_bytes()
        finally:
            tmp.unlink(missing_ok=True)
    with fitz.open(stream=revised,filetype="pdf") as check:
        if text_snapshot(check)!=before_text:
            raise ValueError("Source Arabic RPT text changed: reject")
        if links_snapshot(check)!=before_links:
            raise ValueError("Original 298 DSKP links changed: reject")
        if check[0].get_pixmap(matrix=fitz.Matrix(1.0,1.0)).samples!=before_first:
            raise ValueError("Teacher cover pixels altered: reject")
        required=check_final(check)
        if required!=count:
            raise ValueError(f"Divider total inconsistent: {required}/{count}")
        if file.name in ("tahun_2.pdf","tahun_6.pdf"):
            with fitz.open(stream=raw,filetype="pdf") as orig:
                orig[1].get_pixmap(matrix=fitz.Matrix(1.3,1.3),alpha=False).save(
                    str(Path(out_dir)/f"{file.stem}_before.png"))
            check[1].get_pixmap(matrix=fitz.Matrix(1.3,1.3),alpha=False).save(
                str(Path(out_dir)/f"{file.stem}_after.png"))
    file.write_bytes(revised)
    return {"before_sha256":digest(raw),"after_sha256":digest(revised),
            "bytes":len(revised),"pages":len(before_text),"added":count,
            "links":sum(map(len,before_links)),"pages_audited":work,
            "text_exact_parity":True,"links_exact_parity":True,
            "teacher_cover_pixel_parity":True}


def main():
    manifest_path=ROOT/"manifest.json"
    lock_path=ROOT/"original_cover_layout_verified.json"
    m=json.loads(manifest_path.read_text(encoding="utf-8"))
    lock=json.loads(lock_path.read_text(encoding="utf-8"))
    if (m.get("count")!=56 or m.get("status")!="DRAF_USER_VISIBLE_NOT_ACADEMIC_FINAL"
        or m.get("academic_final_approved") is not False
        or lock.get("status")!="ORIGINAL_COVER_TEMPLATE_LOCKED_TO_56_SOURCE_PDF_SHA256"
        or set(m["files"])!=set(lock["source_sha256_by_subject_year"])):
        raise ValueError("Manifest or original school cover integrity gate changed")
    expected_keys={f"bahasa_arab:{y}" for y in YEARS}
    previous={key:entry.copy() for key,entry in m["files"].items()}
    for key,entry in m["files"].items():
        p=ROOT/entry["path"]
        if (not p.is_file() or p.is_symlink()
            or p.stat().st_size!=entry["bytes"]
            or digest(p.read_bytes())!=entry["sha256"]
            or lock["source_sha256_by_subject_year"][key]!=entry["sha256"]):
            raise ValueError("Baseline 56-PDF digest mismatch: "+key)
    results={}
    for year in YEARS:
        key=f"bahasa_arab:{year}"
        p=ROOT/m["files"][key]["path"]
        result=apply_one(p,AUDIT.parent)
        if result["links"]!={2:60,3:60,4:58,5:60,6:60}[year]:
            raise ValueError("Original Arabic PDF hyperlinks missing")
        m["files"][key]["sha256"]=result["after_sha256"]
        m["files"][key]["bytes"]=result["bytes"]
        lock["source_sha256_by_subject_year"][key]=result["after_sha256"]
        results[key]=result
    if sum(v["links"] for v in results.values())!=298:
        raise ValueError("Arabic 298 DSKP source links not preserved")
    if any(m["files"][key]!=entry for key,entry in previous.items() if key not in expected_keys):
        raise ValueError("Non-Arabic RPT source unexpectedly modified")
    if sum(e["pages"] for e in m["files"].values())!=m["pages"]:
        raise ValueError("Arabic RPT page count changed")
    for key,entry in m["files"].items():
        path=ROOT/entry["path"]
        if digest(path.read_bytes())!=entry["sha256"] or path.stat().st_size!=entry["bytes"]:
            raise ValueError("Final 56-PDF release source mismatch: "+key)
        if lock["source_sha256_by_subject_year"][key]!=entry["sha256"]:
            raise ValueError("Teacher cover SHA ledger mismatch")
    changed=sum(v["added"]>0 for v in results.values())
    audit={
        "status":"DRAF_VECTOR_GRID_ONLY_NOT_ACADEMIC_FINAL",
        "issue":"Missing internal vertical dividers in five-column Arabic RPT source PDFs",
        "year":2027,"years":list(YEARS),
        "files_repaired":changed,"other_51_pdfs_unchanged":True,
        "arabic_dskp_original_links_preserved":298,
        "source_text_unchanged":True,"school_cover_pixels_unchanged":True,
        "no_pdp_sequence_or_2027_calendar_changes":True,
        "no_user_database_or_credit_changes":True,
        "added_dividers":sum(v["added"] for v in results.values()),
        "entries":results
    }
    if changed:
        manifest_path.write_text(json.dumps(m,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        lock_path.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    AUDIT.parent.mkdir(exist_ok=True)
    AUDIT.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("RPT_BAHASA_ARAB_GRID_FIXED",json.dumps({
        "five_files":len(results),"changed":changed,
        "added":audit["added_dividers"],"links":298,
        "other_pdfs_unchanged":True},ensure_ascii=False))


if __name__=="__main__":
    argparse.ArgumentParser().parse_args()
    main()
