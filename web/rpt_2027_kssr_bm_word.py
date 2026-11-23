"""Serve only checksum-verified, editable KSSR BM SK Tahun 2–6 Word.

The source is regenerated from the *same* native RPT HTML as the reviewed
PDF, not from a PDF image/overlay. An absent or mismatched document is never
advertised in the catalog. HTTP authorization is enforced in the main RPT
blueprint; this module only verifies the source documents.
"""
from __future__ import annotations
import hashlib
import json
from functools import lru_cache
from pathlib import Path
from zipfile import BadZipFile, ZipFile

ROOT=Path(__file__).resolve().parents[1]/"rpt_2027"
YEARS=(2,3,4,5,6)


@lru_cache(maxsize=8)
def _manifest(path):
    try:
        doc=json.loads(path.read_text("utf-8"))
    except (OSError,ValueError,TypeError):
        return None
    if doc.get("ready_for_paid_word_download") is not True or doc.get("academic_final") is not False:
        return None
    if doc.get("subject")!="bahasa_melayu" or sorted(doc.get("years",[]))!=list(YEARS):
        return None
    return doc


def word_document(year, *, root=ROOT):
    if type(year) is not int or year not in YEARS:
        return None
    root=Path(root)
    folder=root/"kssr_word_premium"
    manifest=_manifest(folder/"manifest.json")
    if not isinstance(manifest,dict):
        return None
    entry=manifest.get("files",{}).get(str(year))
    if not isinstance(entry,dict):
        return None
    if entry.get("status")!="DRAF_SEMAKAN_NOT_ACADEMIC_FINAL":
        return None
    rel=f"bahasa_melayu/tahun_{year}.docx"
    if entry.get("path")!=rel:
        return None
    path=folder/rel
    try:
        if path.is_symlink() or not path.is_file():
            return None
        content=path.read_bytes()
        if not 20000<=len(content)<=3_000_000 or content[:4]!=b"PK\x5cx03\x5cx04":
            return None
        digest=hashlib.sha256(content).hexdigest()
        if digest!=entry.get("sha256") or len(content)!=entry.get("bytes"):
            return None
        html=Path(__file__).resolve().parents[1]/entry["source_html"]
        if not html.is_file() or html.is_symlink():
            return None
        if hashlib.sha256(html.read_bytes()).hexdigest()!=entry.get("source_html_sha256"):
            return None
        pdf_manifest_path=root/"web_2027_pdfs"/"manifest.json"
        published=json.loads(pdf_manifest_path.read_text("utf-8"))
        if published["files"][f"bahasa_melayu:{year}"]["sha256"]!=entry.get("source_pdf_sha256"):
            return None
        with ZipFile(path) as z:
            if z.testzip() or "word/document.xml" not in z.namelist():
                return None
        return path,digest
    except (OSError,ValueError,KeyError,TypeError,BadZipFile):
        return None
