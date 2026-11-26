"""Checksum-locked paired Science RPT release; existing auth/profile pipeline retained."""
from pathlib import Path
from hashlib import sha256
from functools import lru_cache
import json,os
KEY="CIKGULAJU_DLP_PAIRED_SCIENCE_YEARS"
def enabled(subject,year):
    if subject=="mathematics_dlp":return year in (3,4,5,6) and str(year) in os.getenv("CIKGULAJU_DLP_PAIRED_MATH_YEARS","").split(",")
    return subject=="science_dlp" and year in (2,3,6) and str(year) in os.getenv(KEY,"").split(",")
@lru_cache(maxsize=7)
def assets(root,year,subject="science_dlp"):
    math=subject=="mathematics_dlp"
    count=101 if math else 70
    folder=Path(root)/("paired_math_release" if math else "paired_science_release")
    manifest=json.loads((folder/"manifest.json").read_text())
    entry=manifest["sets"][str(year)]
    if entry["sessions"]!=count:raise ValueError("Invalid session count")
    result={}
    for fmt in ("pdf","docx","index"):
        info=entry["files"][fmt]
        expected=f"{subject}_y{year}"+("_index.json" if fmt=="index" else "."+fmt)
        if info["path"]!=expected:raise ValueError("Invalid paired file path")
        raw=(folder/expected).read_bytes()
        if len(raw)!=info["bytes"] or sha256(raw).hexdigest()!=info["sha256"]:raise ValueError("Paired RPT integrity failure")
        result[fmt]=raw
    rows=json.loads(result["index"])
    if [r["session"] for r in rows]!=list(range(1,count+1)):raise ValueError("Invalid calendar")
    return result

def word_document(root,year,account,config,subject="science_dlp"):
    from web.rpt_native_word_cover import personalized_word,cover_png
    from web.english_rpt_2027_http import _has_paid_access
    from io import BytesIO
    from docx import Document
    from docx.oxml.ns import qn
    from copy import deepcopy
    if not _has_paid_access(account):raise PermissionError("Paid only")
    data=assets(str(root),year,subject)
    key=f"{subject}:{year}"
    lock=json.loads((Path(root)/"web_2027_pdfs/original_cover_layout_verified.json").read_text())
    # The install job checked exact first-page pixels against current approved cover.
    import fitz
    old=(Path(root)/f"full_standards_dlp_pdf_2027/{subject}/tahun_{year}.pdf").read_bytes()
    with fitz.open(stream=old,filetype="pdf") as a,fitz.open(stream=data["pdf"],filetype="pdf") as b:
        if a[0].get_pixmap(matrix=fitz.Matrix(2,2)).samples!=b[0].get_pixmap(matrix=fitz.Matrix(2,2)).samples:
            raise ValueError("Paired cover differs")
    layout=deepcopy(lock["full_standards_dlp_pdf_covers"])
    layout["source_sha256_by_subject_year"][key]=sha256(data["pdf"]).hexdigest()
    d=Document(BytesIO(data["docx"]))
    rid=d.paragraphs[0]._p.xpath(".//a:blip")[0].get(qn("r:embed"))
    d.part.related_parts[rid]._blob=cover_png(data["pdf"],layout,key)
    out=BytesIO();d.save(out)
    blob=personalized_word(out.getvalue(),data["pdf"],layout,key,account,config)
    return blob,sha256(blob).hexdigest()
def suggestion(root,year,target,group_a,subject="science_dlp"):
    rows=json.loads(assets(str(root),year,subject)["index"])
    matched=[r for r in rows if r["dates"][0 if group_a else 1]["start"]<=target.isoformat()<=r["dates"][0 if group_a else 1]["end"]]
    if not matched:return None
    return {"week":matched[0]["week"],"group":"A" if group_a else "B","lessons":{"":[]},"dlp_labels":[f"Session {r['session']:02d}" for r in matched],"dlp_reserve_slots":0}
