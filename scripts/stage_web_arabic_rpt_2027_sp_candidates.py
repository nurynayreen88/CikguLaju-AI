"""Stage five source-page SHA-locked Bahasa Arab DRAF RPTs on Web only.

This does not declare academic approval and does not modify the other 51 PDFs.
Invocation: python -m scripts.stage_web_arabic_rpt_2027_sp_candidates --artifacts /tmp/bundle
Source artifacts must come from a successful immutable CI run (validated by workflow).
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path
import fitz

ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/"rpt_2027/web_2027_pdfs"
YEARS=(2,3,4,5,6)
PDP_COUNT={2:60,3:60,4:58,5:60,6:60}
CANDIDATE_MIN={2:58,3:54,4:54,5:60,6:60}
# The shipped Web templates at the verified Nov 8 2026 baseline:
BASELINE_HASHES={
    2:"e5d582ffecd134cbf6682b60a8940146bfb1b8de4f672bd995a46a349bd285d7",
    3:"f80f920368e76cc1f39c937b0047e901fca3786b71998d975ce93891ea0c9b58",
    4:"ddd4632c78985deb01df688f5a269b186023884857542858c35499dbe912fe20",
    5:"8099c47516e20e92683947813724008ebd1025c934d6e5a254da9fec449414a7",
    6:"195f97e5c92d2c38019f7677983526e1794da7785b20a1c86c02e0eb2f4e2ff5",
}
BAD=("Pernyataan penuh","teks belum disahkan","sumber v26","RPH sebenar",
     "DRAF LEGACY","source_status","curriculum_provenance","AMARAN:",
     "jangan merge","kelulusan panitia")

def update(artifacts):
    artifacts=Path(artifacts)
    manifest_path=WEB/"manifest.json"
    cover_path=WEB/"original_cover_layout_verified.json"
    manifest=json.loads(manifest_path.read_text("utf-8"))
    cover=json.loads(cover_path.read_text("utf-8"))
    files=manifest["files"]
    before={k:dict(v) for k,v in files.items()}
    assert manifest["count"]==56 and len(files)==56
    assert manifest["status"]=="DRAF_USER_VISIBLE_NOT_ACADEMIC_FINAL"
    assert manifest.get("academic_final_approved") is False
    assert cover["status"]=="ORIGINAL_COVER_TEMPLATE_LOCKED_TO_56_SOURCE_PDF_SHA256"
    assert len(cover["source_sha256_by_subject_year"])==56
    for year in YEARS:
        key=f"bahasa_arab:{year}"
        dest=WEB/f"bahasa_arab/tahun_{year}.pdf"
        entry=files[key]
        old=dest.read_bytes()
        assert entry["sha256"]==BASELINE_HASHES[year] and hashlib.sha256(old).hexdigest()==entry["sha256"],key
        assert cover["source_sha256_by_subject_year"][key]==entry["sha256"],key
        artifact=artifacts/f"CIKGULAJU_RPT_BAHASA_ARAB_TAHUN_{year}_2027_LIMA_LAJUR_DRAF.pdf"
        raw=artifact.read_bytes()
        assert raw[:5]==b"%PDF-" and raw!=old,(year,"invalid or unchanged artifact")
        assert 50_000<len(raw)<500_000,(year,len(raw))
        with fitz.open(stream=old,filetype="pdf") as oldpdf,fitz.open(stream=raw,filetype="pdf") as pdf:
            assert pdf.page_count==oldpdf.page_count,(year,"page count or cover changed")
            assert abs(pdf[0].rect.width-oldpdf[0].rect.width)<.1
            assert abs(pdf[0].rect.height-oldpdf[0].rect.height)<.1
            assert pdf[0].get_text()==oldpdf[0].get_text(),(year,"original cover labels changed")
            assert len(pdf[0].get_drawings())==len(oldpdf[0].get_drawings()),(year,"original cover frame changed")
            text=unicodedata.normalize("NFKC","\n".join(p.get_text() for p in pdf))
            assert text.count("PdP ")==PDP_COUNT[year],(year,"source lesson count")
            assert text.count("Buka DSKP asal")==PDP_COUNT[year],(year,"source page links")
            assert text.count("القدرة")>=CANDIDATE_MIN[year],(year,"source SP text missing")
            assert all(bad.lower() not in text.lower() for bad in BAD),(year,"internal note leaked")
            for index,page in enumerate(pdf):
                assert page.rect.width>page.rect.height,(year,index,"not landscape")
                assert not any(b[0]<0 or b[1]<0 or b[2]>page.rect.width+.25 or b[3]>page.rect.height+.25
                               for b in page.get_text("blocks")),(year,index,"page overflow")
            pages=pdf.page_count
        sha=hashlib.sha256(raw).hexdigest()
        dest.write_bytes(raw)
        entry.update(sha256=sha,bytes=len(raw),pages=pages,status="DRAF",
                     source_stage="ARABIC_Y2_Y6_117_SOURCE_SP_VISUAL_CANDIDATES_NOT_ACADEMIC_FINAL_20261108")
        cover["source_sha256_by_subject_year"][key]=sha
        print(f"{key}: {pages} pages, {len(raw)} bytes, SHA256 {sha}")
    assert set(files)==set(before)
    for key in set(files)-{f"bahasa_arab:{i}" for i in YEARS}:
        assert files[key]==before[key],key
        assert cover["source_sha256_by_subject_year"][key]==before[key]["sha256"],key
    manifest["pages"]=sum(item["pages"] for item in files.values())
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    cover_path.write_text(json.dumps(cover,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Web DRAF Arabic source SP stage done; only 5 files + manifest + cover SHA updated; 51 untouched.")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--artifacts",required=True)
    args=p.parse_args()
    update(args.artifacts)

if __name__=="__main__":
    main()
