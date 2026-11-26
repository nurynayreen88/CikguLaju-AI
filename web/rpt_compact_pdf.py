"""Opt-in compact FREE PDF with original source and cover locks. Fall back safely."""
import hashlib
import json
import os
from pathlib import Path
from web.rpt_native_word_batch import PINS

def read(subject,year,original,*,root):
    if os.environ.get("CIKGULAJU_RPT_COMPACT_PDF_BATCH")!="1":
        return None
    key=f"{subject}:{year}"
    original_sha=PINS.get(key)
    if not original_sha or hashlib.sha256(original).hexdigest()!=original_sha:
        return None
    try:
        base=Path(root)/"compact_free_pdf_2027"
        manifest=json.loads((base/"manifest.json").read_text("utf8"))
        entries=manifest["files"]
        if manifest["version"]!=1 or manifest["count"]!=31 or manifest["status"]!="LAYOUT_QA_CANDIDATE" or set(entries)!=set(PINS):
            return None
        e=entries[key]
        relative=f"{subject}/tahun_{year}.pdf"
        if e["source_sha256"]!=original_sha or e["path"]!=relative:
            return None
        file=base/relative
        if file.is_symlink() or not 8000<=file.stat().st_size<=25*1024*1024:
            return None
        raw=file.read_bytes()
        digest=hashlib.sha256(raw).hexdigest()
        layout=json.loads((Path(root)/"web_2027_pdfs"/"original_cover_layout_verified.json").read_text("utf8"))["compact_pdf_covers"]
        if not raw.startswith(b"%PDF-") or len(raw)!=e["bytes"] or digest!=e["sha256"] or layout["source_sha256_by_subject_year"].get(key)!=digest:
            return None
        return raw,digest
    except (OSError,ValueError,KeyError,TypeError,AttributeError):
        return None

def read_approved(subject,year,original,*,root):
    if os.environ.get("CIKGULAJU_RPT_COMPACT_PDF_BATCH")!="1":
        return None
    from rpt_2027.matematik.sk_documents import DIGESTS
    from web.rpt_native_word_batch import APPROVED_SCIENCE_PINS
    pins={**{f"matematik:{y}":v for y,v in DIGESTS.items()},**{f"sains:{y}":v for y,v in APPROVED_SCIENCE_PINS.items()}}
    key=f"{subject}:{year}"
    original_sha=pins.get(key)
    if not original_sha or hashlib.sha256(original).hexdigest()!=original_sha:
        return None
    try:
        base=Path(root)/"compact_approved_pdf_2027"
        manifest=json.loads((base/"manifest.json").read_text("utf8"))
        entries=manifest["files"]
        if manifest["version"]!=1 or manifest["count"]!=5 or manifest["status"]!="LAYOUT_QA_CANDIDATE" or set(entries)!=set(pins):
            return None
        e=entries[key]
        relative=f"{subject}/tahun_{year}.pdf"
        if e["source_sha256"]!=original_sha or e["path"]!=relative:
            return None
        file=base/relative
        if file.is_symlink() or not 8000<=file.stat().st_size<=25*1024*1024:
            return None
        raw=file.read_bytes()
        digest=hashlib.sha256(raw).hexdigest()
        layout=json.loads((Path(root)/"web_2027_pdfs"/"original_cover_layout_verified.json").read_text("utf8"))["compact_approved_pdf_covers"][key]
        if not raw.startswith(b"%PDF-") or len(raw)!=e["bytes"] or digest!=e["sha256"] or layout["source_sha256_by_subject_year"].get(key)!=digest:
            return None
        return raw,digest
    except (OSError,ValueError,KeyError,TypeError,AttributeError):
        return None
