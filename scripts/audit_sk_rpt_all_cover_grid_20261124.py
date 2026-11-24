"""Read-only batch inspection of SK RPT PDF cover and table geometry.
Audit the exact files shipped by Web, including dedicated replacement sources.
Do not alter the PDFs or treat geometry as academic approval.
"""
from pathlib import Path
import hashlib
import json
import re
import fitz
from rpt_2027.matematik import sk_documents as math
from rpt_2027.sains import sk_documents as science

ROOT=Path(__file__).resolve().parents[1]/"rpt_2027"
OUT=Path("qa-sk-rpt-all")
OUT.mkdir(exist_ok=True)
V2=ROOT/"web_2027_pdfs"
manifest=json.loads((V2/"manifest.json").read_text("utf-8"))
cover=json.loads((V2/"original_cover_layout_verified.json").read_text("utf-8"))
assert len(manifest["files"])==56
assert set(cover["source_sha256_by_subject_year"])==set(manifest["files"])

def positions(page):
    result={}
    for label in ("NAMA SEKOLAH","NAMA GURU","LOGO SEKOLAH","RANCANGAN PENGAJARAN TAHUNAN"):
        rects=page.search_for(label)
        result[label]=[[round(r.x0,1),round(r.y0,1),round(r.x1,1),round(r.y1,1)] for r in rects]
    return result

def inspect(page):
    lines=[]
    for drawing in page.get_drawings():
        for kind,*rest in drawing["items"]:
            if kind=="l":
                a,b=rest[:2]
                lines.append((a.x,a.y,b.x,b.y))
            elif kind=="re":
                r=rest[0]
                if drawing.get("color") is not None or min(r.width,r.height)<2:
                    lines.extend([(r.x0,r.y0,r.x1,r.y0),(r.x0,r.y1,r.x1,r.y1),
                                  (r.x0,r.y0,r.x0,r.y1),(r.x1,r.y0,r.x1,r.y1)])
    vx=sorted({round(a,1) for a,b,c,d in lines if abs(a-c)<0.7 and abs(b-d)>12})
    hy=sorted({round(b,1) for a,b,c,d in lines if abs(b-d)<0.7 and abs(a-c)>12})
    xclusters=[]
    for x in vx:
        if not xclusters or x-xclusters[-1]>2:
            xclusters.append(x)
    overflow=[list(b[:4]) for b in page.get_text("blocks")
              if b[0]<-0.5 or b[1]<-0.5 or b[2]>page.rect.width+0.5 or b[3]>page.rect.height+0.5]
    return {"page":page.number+1,"vertical_positions":xclusters,
            "horizontal_positions":len(hy),"text_overflow":overflow,
            "landscape":page.rect.width>page.rect.height}

def audit(key,path,expected,variant,reference):
    if not path.is_file():
        return {"key":key,"variant":variant,"path":str(path.relative_to(ROOT)),"status":"MISSING"}
    raw=path.read_bytes()
    digest=hashlib.sha256(raw).hexdigest()
    if expected and digest!=expected:
        return {"key":key,"variant":variant,"status":"HASH_MISMATCH","sha256":digest}
    with fitz.open(stream=raw,filetype="pdf") as doc:
        pos=positions(doc[0])
        flags=[]
        for label,expected_boxes in reference.items():
            if not expected_boxes:
                continue
            boxes=pos[label]
            if len(boxes)!=len(expected_boxes) or any(
                abs(a[0]-b[0])>4 or abs(a[1]-b[1])>4 for a,b in zip(boxes,expected_boxes)):
                flags.append(label)
        pages=[inspect(p) for p in list(doc)[1:]]
        if flags or any(p["text_overflow"] or not p["landscape"] or len(p["vertical_positions"])<6 for p in pages):
            for idx in sorted({0,min(1,len(doc)-1)}):
                doc[idx].get_pixmap(matrix=fitz.Matrix(.8,.8),alpha=False).save(str(OUT/(key.replace(":","_")+"_"+variant+"_p"+str(idx+1)+".png")))
        return {"key":key,"variant":variant,"path":str(path.relative_to(ROOT)),
                "sha256":digest,"status":"REVIEW" if flags or any(p["text_overflow"] or not p["landscape"] or len(p["vertical_positions"])<6 for p in pages) else "GEOMETRY_SCREEN_PASS",
                "cover_different_label_positions":flags,"cover_labels":pos,
                "page_count":len(doc),"body_pages":pages,
                "cover_dimensions":list(doc[0].rect)}

bm=V2/manifest["files"]["bahasa_melayu:2"]["path"]
assert hashlib.sha256(bm.read_bytes()).hexdigest()==manifest["files"]["bahasa_melayu:2"]["sha256"]
with fitz.open(bm) as doc:
    reference=positions(doc[0])
    assert reference["NAMA SEKOLAH"] and reference["NAMA GURU"]
    doc[0].get_pixmap(matrix=fitz.Matrix(1.2,1.2),alpha=False).save(str(OUT/"REFERENCE_BM_KSSR_T2.png"))
results=[]
for key,item in sorted(manifest["files"].items()):
    assert cover["source_sha256_by_subject_year"][key]==item["sha256"]
    results.append(audit(key,V2/item["path"],item["sha256"],"56_source",reference))
for year,digest in math.DIGESTS.items():
    results.append(audit(f"matematik:{year}",ROOT/"matematik"/(math.FILE_TEMPLATE%year),digest,"replacement",reference))
for year,digest in math.DPK_DIGESTS.items():
    results.append(audit(f"matematik:{year}",ROOT/"matematik"/(math.DPK_FILE_TEMPLATE%year),digest,"DPK",reference))
for year in science.PDP_COUNTS:
    results.append(audit(f"sains:{year}",ROOT/"sains"/f"CikguLaju_RPT_Sains_SK_Tahun{year}_2027.pdf",None,"replacement",reference))
integrated=cover.get("english_integrated",{}).get("source_sha256_by_subject_year",{})
for key,digest in sorted(integrated.items()):
    year=int(key.split(":")[1])
    results.append(audit(key,ROOT/"english"/f"RPT_English_SK_2027_Year_{year}_A_B.pdf",digest,"integrated",reference))
from collections import Counter
summary=dict(Counter(r["status"] for r in results))
(OUT/"audit.json").write_text(json.dumps({"status":"GEOMETRY_SCREEN_ONLY_NOT_VISUAL_OR_ACADEMIC_SIGNOFF",
    "reference":"bahasa_melayu:2","summary":summary,"files":results},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("SK RPT BATCH:",len(results),summary)
for r in results:
    if r["status"]!="GEOMETRY_SCREEN_PASS":
        print(r["key"],r["variant"],r["status"],r.get("cover_different_label_positions"),
              "flagged body pages",[p["page"] for p in r.get("body_pages",[]) if p["text_overflow"] or not p["landscape"] or len(p["vertical_positions"])<6])
