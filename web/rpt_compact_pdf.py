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

LANGUAGE_PINS={
    "bm": {
        "bahasa_melayu:2": "fbaa1d1c81b2feffc1150957c3d3a49c614871ad16440cc6d7bec1798fe5cbbd",
        "bahasa_melayu:3": "98db51ca3f37a7be29fa379c6d670061753884517acd2abd9a40a21283552756",
        "bahasa_melayu:4": "eb231841184177fa27a14f60fd4e2c4d0caf2cb0a15ebf674129e802d38d0c6f",
        "bahasa_melayu:5": "fbe90a74a6b8768e75215b189de93805decb3aa9f739caae3e0b450e79a0b11e",
        "bahasa_melayu:6": "480e8b4f47a807e1d3b1870b5cf224283b77171455a2f033d4fca9d9dea18da2"
    },
    "english": {
        "english:2": "7cd4dd1eabd568dcaa9de3faba1fa0de3c4f8469ed69c3df7101b7c74a8600e9",
        "english:3": "55528e8481f9af52386d6f7b898458aad80dcf1996f70c6b424a10da89515eb2",
        "english:4": "0e72c8e993c9ef9e0d8112872b343cf58efcb512400a76d355d65bfdb4cb347e",
        "english:5": "5a58b042920643d342060a7d9634481c57e67261245ca6b98b416aa470020019",
        "english:6": "f9c8ca388328f123aad9202e26397eeb1fae5359ac1e9b1fbda1004541fda34f"
    }
}

def read_language(subject,year,original,*,root):
    if os.environ.get("CIKGULAJU_RPT_COMPACT_PDF_BATCH")!="1":
        return None
    code={"bahasa_melayu":"bm","english":"english"}.get(subject)
    if code is None:
        return None
    pins=LANGUAGE_PINS[code]
    key=f"{subject}:{year}"
    original_sha=pins.get(key)
    if not original_sha or hashlib.sha256(original).hexdigest()!=original_sha:
        return None
    try:
        base=Path(root)/f"compact_{code}_pdf_2027"
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
        layout=json.loads((Path(root)/"web_2027_pdfs"/"original_cover_layout_verified.json").read_text("utf8"))[f"compact_{code}_pdf_covers"]
        if not raw.startswith(b"%PDF-") or len(raw)!=e["bytes"] or digest!=e["sha256"] or layout["source_sha256_by_subject_year"].get(key)!=digest:
            return None
        return raw,digest
    except (OSError,ValueError,KeyError,TypeError,AttributeError):
        return None

def read_dlp(subject,year,original,*,root):
    if os.environ.get("CIKGULAJU_RPT_COMPACT_PDF_BATCH")!="1":
        return None
    from tools.build_rpt_dlp_native_20261126 import PINS as pins
    key=f"{subject}:{year}"
    expected=pins.get(key)
    if not expected or hashlib.sha256(original).hexdigest()!=expected:
        return None
    try:
        base=Path(root)/"compact_dlp_pdf_2027"
        manifest=json.loads((base/"manifest.json").read_text("utf8"))
        entries=manifest["files"]
        if manifest["version"]!=1 or manifest["count"]!=10 or manifest["status"]!="LAYOUT_QA_CANDIDATE" or set(entries)!=set(pins):
            return None
        e=entries[key]
        relative=f"{subject}/tahun_{year}.pdf"
        if e["source_sha256"]!=expected or e["path"]!=relative:
            return None
        file=base/relative
        if file.is_symlink() or not 8000<=file.stat().st_size<=25*1024*1024:
            return None
        raw=file.read_bytes()
        digest=hashlib.sha256(raw).hexdigest()
        layout=json.loads((Path(root)/"web_2027_pdfs"/"original_cover_layout_verified.json").read_text("utf8"))["compact_dlp_pdf_covers"][key]
        if not raw.startswith(b"%PDF-") or len(raw)!=e["bytes"] or digest!=e["sha256"] or layout["source_sha256_by_subject_year"].get(key)!=digest:
            return None
        return raw,digest
    except (OSError,ValueError,KeyError,TypeError,AttributeError):
        return None

RTL_PINS={
    "bahasa_arab:2": "ed5699127c118f28fe86cff6edef6e8ee85e7d787e5ef753cb251a771b4ea4b7",
    "pendidikan_islam:2": "79129ba5613f672cb105fb2621252283dfa7bb76ccc67cee0842d0339e50c92e",
    "pendidikan_islam:3": "134253d2bc89c1736347df70e3e2929ab94e537e14869c69c0bf559fae7e5a33",
    "pendidikan_islam:4": "e77bfd0654b5bf687bbb74fbc5c1d22a3c088adb735e0b6e62e001899a941e74",
    "pendidikan_islam:5": "f8830f4efbcd8bf26a33acb804ee2673e5dabdc354b8dfe34bb5d21bce1fc159",
    "pendidikan_islam:6": "b993b3cf5baeebc4e67d37456b5b2e12955a0d4373a5dc29b5014fc4fb98f41f",
    "bahasa_arab:3": "c91f7b38a059ee9a208f852a3b371ee606326aa4d50e5742dc523efc68743d3b",
    "bahasa_arab:4": "8b979445bcf8bc1663e4fc4196da11bb9a32fd756f5c916ace6503be059ae217",
    "bahasa_arab:5": "be92eff7fc8b1017f88641bbe2ad1227b26436b41cf3f9e327b632de1d52b0ca",
    "bahasa_arab:6": "279d576410b261261190e3a8cb146cbd333bea5f04d31f5bd4711130cfdc4f30"
}

def read_rtl(subject,year,original,*,root):
    if os.environ.get("CIKGULAJU_RPT_COMPACT_PDF_BATCH")!="1":
        return None
    key=f"{subject}:{year}"
    expected=RTL_PINS.get(key)
    if not expected or hashlib.sha256(original).hexdigest()!=expected:
        return None
    try:
        base=Path(root)/"compact_rtl_pdf_2027"
        manifest=json.loads((base/"manifest.json").read_text("utf8"))
        entries=manifest["files"]
        if manifest["version"]!=1 or manifest["count"]!=10 or manifest["status"]!="LAYOUT_QA_CANDIDATE" or set(entries)!=set(RTL_PINS):
            return None
        e=entries[key]
        relative=f"{subject}/tahun_{year}.pdf"
        if e["source_sha256"]!=expected or e["path"]!=relative:
            return None
        file=base/relative
        if file.is_symlink() or not 8000<=file.stat().st_size<=25*1024*1024:
            return None
        raw=file.read_bytes()
        digest=hashlib.sha256(raw).hexdigest()
        layout=json.loads((Path(root)/"web_2027_pdfs"/"original_cover_layout_verified.json").read_text("utf8"))["compact_rtl_pdf_covers"]
        if not raw.startswith(b"%PDF-") or len(raw)!=e["bytes"] or digest!=e["sha256"] or layout["source_sha256_by_subject_year"].get(key)!=digest:
            return None
        return raw,digest
    except (OSError,ValueError,KeyError,TypeError,AttributeError):
        return None

def read_full_standards_dlp(subject,year,original,*,root):
    # New revision is opt-in only via the complete, checksum-locked manifest.
    if os.environ.get("CIKGULAJU_RPT_FULL_STANDARDS_DLP")!="1":
        return None
    from tools.build_rpt_dlp_native_20261126 import PINS
    key=f"{subject}:{year}"
    expected=PINS.get(key)
    if not expected or hashlib.sha256(original).hexdigest()!=expected:
        return None
    try:
        base=Path(root)/"full_standards_dlp_pdf_2027"
        m=json.loads((base/"manifest.json").read_text("utf8"))
        if m["version"]!=1 or m["count"]!=10 or m["status"]!="LAYOUT_QA_CANDIDATE" or set(m["files"])!=set(PINS):
            return None
        e=m["files"][key]
        relative=f"{subject}/tahun_{year}.pdf"
        if e["path"]!=relative or e["source_sha256"]!=expected:
            return None
        file=base/relative
        if file.is_symlink() or not 8000<=file.stat().st_size<=25*1024*1024:
            return None
        raw=file.read_bytes()
        digest=hashlib.sha256(raw).hexdigest()
        lock=json.loads((Path(root)/"web_2027_pdfs"/"original_cover_layout_verified.json").read_text("utf8"))
        layout=lock["full_standards_dlp_pdf_covers"]
        if layout["status"]!="FULL_STANDARDS_DLP_RPT_PDF_COVER_VERIFIED" or set(layout["source_sha256_by_subject_year"])!=set(PINS):
            return None
        if not raw.startswith(b"%PDF-") or len(raw)!=e["bytes"] or digest!=e["sha256"] or layout["source_sha256_by_subject_year"].get(key)!=digest:
            return None
        return raw,digest
    except (OSError,ValueError,KeyError,TypeError,AttributeError):
        return None
