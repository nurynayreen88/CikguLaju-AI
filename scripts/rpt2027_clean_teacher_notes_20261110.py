#!/usr/bin/env python3
"""Targeted teacher-facing RPT 2027 PDF note cleanup; no academic approval change."""
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
import fitz

ARABIC={f"bahasa_arab/tahun_{y}.pdf" for y in range(2,7)}
ISLAM={"pendidikan_islam/tahun_2.pdf"}
CALENDAR={f"pjpk/tahun_{y}.pdf" for y in range(2,7)} | {f"sejarah/tahun_{y}.pdf" for y in range(4,7)}
TARGETS=ARABIC | ISLAM | CALENDAR
LEAK=re.compile(
    r"(?i)Buka DSKP asal|pemetaan buku teks belum disahkan|"
    r"CALON BUKAN VISUAL|Masih DRAF|DRAF PKJR|"
    r"perlu padanan fokus halaman|Padanan SK/TOC terdahulu|"
    r"M\d{2}\s*\(cadangan\)"
)
CODE=re.compile(r"(?<!\d)\d+\.\d+(?:\.\d+)?(?!\d)")
FIRST=re.compile(r"(?i)(?:PdP|Lesson)\s*0*1\b")
WEEK1=re.compile(r"(?i)(?<!\d)M\s*01(?!\d)")

def digest(data): return hashlib.sha256(data).hexdigest()

def snapshot(doc):
    content="\n".join(p.get_text() for p in list(doc)[1:])
    return {
        "pages":len(doc),
        "dimensions":[(round(p.rect.width,2),round(p.rect.height,2)) for p in doc],
        "codes":sorted(CODE.findall(content)),
        "first_week":bool(WEEK1.search(doc[1].get_text())),
        "first_lesson":bool(FIRST.search(doc[1].get_text())),
        "leaks":sorted(set(LEAK.findall(content))),
    }

def make_clean(src,dst,rel):
    doc=fitz.open(src)
    before=snapshot(doc)
    redactions=0
    for page in list(doc)[1:]:
        areas=[]
        if rel in ARABIC:
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines",[]):
                    for span in line["spans"]:
                        if span["text"].startswith("Buka DSKP asal"):
                            areas.append(fitz.Rect(span["bbox"]))
        if rel in ISLAM:
            for term in ("Padanan SK/TOC terdahulu","perlu padanan fokus halaman"):
                # Shrink to avoid touching adjacent right-to-left Jawi SK/SP glyphs.
                areas += [fitz.Rect(b.x0+1.4,b.y0+1.4,b.x1-1.4,b.y1-1.4)
                          for b in page.search_for(term)]
        if rel in CALENDAR:
            areas += page.search_for("(cadangan)")
        for box in areas:
            fill=(234/255,241/255,227/255) if rel in CALENDAR else (1,1,1)
            page.add_redact_annot(box,fill=fill)
        if areas:
            page.apply_redactions(images=0,graphics=0,text=0)
            redactions+=len(areas)
    dst.parent.mkdir(parents=True,exist_ok=True)
    doc.save(dst,garbage=4,deflate=True)
    doc.close()
    with fitz.open(dst) as new:
        after=snapshot(new)
    assert before["pages"]==after["pages"],rel
    assert before["dimensions"]==after["dimensions"],rel
    assert before["codes"]==after["codes"],("SK/SP tokens altered",rel)
    assert before["first_week"] and after["first_week"],("M01 lost",rel)
    assert before["first_lesson"] and after["first_lesson"],("PdP001 lost",rel)
    assert not after["leaks"],("internal notes remain",rel,after["leaks"])
    return {"file":rel,"redaction_boxes":redactions,"pages":after["pages"],
            "preserved_sk_sp_numeric_tokens":len(after["codes"])}

def main():
    root=Path(sys.argv[1])
    out=Path(sys.argv[2])
    manifest_path=root/"manifest.json"
    manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["count"]==56 and len(manifest["files"])==56
    assert manifest["academic_final_approved"] is False
    index={v["path"]:key for key,v in manifest["files"].items()}
    assert TARGETS <= set(index),sorted(TARGETS-set(index))
    for rel,key in index.items():
        data=(root/rel).read_bytes()
        assert digest(data)==manifest["files"][key]["sha256"],("source hash",rel)
        assert len(data)==manifest["files"][key]["bytes"],("source bytes",rel)

    findings=[]
    for rel in sorted(TARGETS):
        src=root/rel
        with fitz.open(src) as current:
            has_leak=bool(snapshot(current)["leaks"])
        if not has_leak:
            findings.append({"file":rel,"already_clean":True})
            continue
        dst=out/"cleaned"/rel
        row=make_clean(src,dst,rel)
        raw=dst.read_bytes()
        src.write_bytes(raw)
        info=manifest["files"][index[rel]]
        info["sha256"]=digest(raw)
        info["bytes"]=len(raw)
        assert info["pages"]==row["pages"],rel
        findings.append(row)

    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    total_pages=0
    remaining=[]
    for rel,key in index.items():
        data=(root/rel).read_bytes()
        info=manifest["files"][key]
        assert digest(data)==info["sha256"],("final hash",rel)
        assert len(data)==info["bytes"],("final bytes",rel)
        with fitz.open(root/rel) as pdf:
            assert len(pdf)==info["pages"] and len(pdf)>=2
            assert all(p.rect.width>p.rect.height for p in pdf)
            total_pages+=len(pdf)
            s=snapshot(pdf)
            if s["leaks"]:remaining.append({"file":rel,"leaks":s["leaks"]})
            assert s["first_week"] and s["first_lesson"],("week01",rel)
    assert total_pages==manifest["pages"],(total_pages,manifest["pages"])
    assert not remaining,remaining
    assert manifest["academic_final_approved"] is False
    out.mkdir(exist_ok=True,parents=True)
    report={"target_files":len(TARGETS),"changes":findings,
            "redaction_boxes":sum(x.get("redaction_boxes",0) for x in findings),
            "all_56_file_hashes_verified":True,"total_pages":total_pages,
            "all_56_m01_pdp001_verified":True,"academic_final_approved":False,
            "source_notes_remaining":[]}
    (out/"QA_RPT2027_14_PDF_TEACHER_NOTE_CLEANUP.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("RPT2027_14_PDF_NOTES_CLEAN_PASS",len(TARGETS),report["redaction_boxes"],
          total_pages,flush=True)

if __name__=="__main__": main()
