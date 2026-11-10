#!/usr/bin/env python3
"""Restore original DSKP URL annotations lost during the 14-PDF text cleanup.

Only hyperlink annotations on Bahasa Arab Tahun 2-6 are restored, from exact
pre-clean Git commit. All curriculum text and all PDF rendered pixels are
preserved. Update SHA manifest + locked cover hashes together.
"""
from __future__ import annotations
import hashlib, json, subprocess, tempfile
from pathlib import Path
import fitz

PRE_CLEAN="77d69a938e906f34e497e530e31f5c5655e52295"
ROOT=Path("rpt_2027/web_2027_pdfs")
FILES=[f"bahasa_arab/tahun_{y}.pdf" for y in range(2,7)]
SCOPED_FIELDS=("kind","from","uri","page","to","zoom","file","nameddest")

def sha(raw): return hashlib.sha256(raw).hexdigest()

def links(page):
    return page.get_links()

def compact_link(link):
    # PyMuPDF's annotation xref/id are not portable across documents.
    d={k:v for k,v in link.items() if k in SCOPED_FIELDS and v is not None}
    assert d.get("kind") in (fitz.LINK_URI,fitz.LINK_GOTO,
                             fitz.LINK_GOTOR,fitz.LINK_LAUNCH,
                             fitz.LINK_NAMED),d
    assert "from" in d
    return d

def fingerprint(page):
    # A link must not change rendered content (normal annotations invisible).
    pix=page.get_pixmap(matrix=fitz.Matrix(0.65,0.65),alpha=False)
    return hashlib.sha256(pix.samples).hexdigest()

def main():
    manifest_path=ROOT/"manifest.json"
    layout_path=ROOT/"original_cover_layout_verified.json"
    manifest=json.loads(manifest_path.read_text("utf-8"))
    layout=json.loads(layout_path.read_text("utf-8"))
    assert manifest["count"]==56 and len(manifest["files"])==56
    assert manifest["academic_final_approved"] is False
    assert set(layout["source_sha256_by_subject_year"])==set(manifest["files"])
    # Fetch the exact historical commit (no reliance on a moving branch).
    subprocess.run(["git","fetch","--no-tags","--depth=1","origin",PRE_CLEAN],check=True)
    report=[]
    originals=0
    restored=0
    for rel in FILES:
        key=rel.replace("/",":").replace("tahun_","").removesuffix(".pdf")
        item=manifest["files"][key]
        source=ROOT/rel
        current=source.read_bytes()
        assert sha(current)==item["sha256"] and len(current)==item["bytes"],rel
        old=subprocess.check_output(["git","show",f"{PRE_CLEAN}:rpt_2027/web_2027_pdfs/{rel}"])
        assert old.startswith(b"%PDF-"),rel
        with fitz.open(stream=old,filetype="pdf") as original,fitz.open(source) as now:
            assert len(original)==len(now)==item["pages"],rel
            initial_text=[p.get_text("text") for p in now]
            before_renders=[fingerprint(p) for p in now]
            original_links=[list(map(compact_link,links(p))) for p in original]
            counts_before=sum(len(links(p)) for p in now)
            counts_original=sum(len(v) for v in original_links)
            originals+=counts_original
            assert counts_original>0,(rel,"no original source links")
            signature=lambda pages: [[(x["kind"],x.get("uri"),
                tuple(round(v,2) for v in x["from"])) for x in page] for page in pages]
            current_links=[list(map(compact_link,p.get_links())) for p in now]
            if signature(current_links)==signature(original_links):
                report.append({"file":rel,"before_links":counts_before,
                               "restored_links":counts_original,"already_restored":True,
                               "sha256":item["sha256"],"pages":item["pages"],"pixel_parity":True})
                continue
            # Prior cleanup mistakenly removed links at redacted editorial cells.
            # Re-add only those present in the fixed original source.
            for page,reference_links in zip(now,original_links):
                existing={(x["kind"],x.get("uri"),tuple(round(v,2) for v in x["from"]))
                          for x in page.get_links()}
                for link in reference_links:
                    marker=(link["kind"],link.get("uri"),
                            tuple(round(v,2) for v in link["from"]))
                    if marker not in existing:
                        page.insert_link(link)
                        restored+=1
                        existing.add(marker)
            with tempfile.NamedTemporaryFile(suffix=".pdf",delete=False) as handle:
                temp=Path(handle.name)
            try:
                now.save(temp,garbage=4,deflate=True)
                with fitz.open(temp) as clean:
                    assert len(clean)==len(original),rel
                    assert [p.get_text("text") for p in clean]==initial_text,("text drift",rel)
                    assert [fingerprint(p) for p in clean]==before_renders,("visual drift",rel)
                    final_links=[list(map(compact_link,p.get_links())) for p in clean]
                    assert [len(x) for x in final_links]==[len(x) for x in original_links],("link counts",rel)
                    # Preserve link destinations, not just the number of hotspots.
                    assert [[(x["kind"],x.get("uri"),tuple(round(v,2) for v in x["from"]))
                             for x in page] for page in final_links] == [
                            [(x["kind"],x.get("uri"),tuple(round(v,2) for v in x["from"]))
                             for x in page] for page in original_links],("link target",rel)
                bytes_out=temp.read_bytes()
            finally:
                temp.unlink(missing_ok=True)
        source.write_bytes(bytes_out)
        item["sha256"]=sha(bytes_out)
        item["bytes"]=len(bytes_out)
        layout["source_sha256_by_subject_year"][key]=item["sha256"]
        report.append({"file":rel,"before_links":counts_before,"restored_links":counts_original,
                       "sha256":item["sha256"],"pages":item["pages"],"pixel_parity":True})
    assert originals==298,("expected exact original 298 Bahasa Arab source links",originals)
    assert restored>=0,restored
    assert all(layout["source_sha256_by_subject_year"][k]==v["sha256"]
               for k,v in manifest["files"].items()),"cover layout SHA drift"
    for key,item in manifest["files"].items():
        raw=(ROOT/item["path"]).read_bytes()
        assert sha(raw)==item["sha256"] and len(raw)==item["bytes"],key
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    layout_path.write_text(json.dumps(layout,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    Path("qa_rpt2027_links").mkdir(exist_ok=True)
    Path("qa_rpt2027_links/restored_298_arabic_links.json").write_text(
        json.dumps({"source_commit":PRE_CLEAN,"files":report,
                    "original_link_total":originals,"links_inserted":restored,
                    "academic_final_approved":False,
                    "text_and_visual_unchanged":True},indent=2)+"\n",encoding="utf-8")
    print("RPT2027_BAHASA_ARAB_298_LINK_RESTORE_PASS",originals,restored,flush=True)

if __name__=="__main__":
    main()
