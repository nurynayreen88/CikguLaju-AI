"""Read-only retrieval of KPM September-2021 Sains Year 6 DSKP facsimile.

Does not assert official hosting, approval or edit teacher PDFs. A downloaded
PDF must match the 96-code index; any missing text remains an explicit gate.
"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import hashlib
import json
import re
import requests

ORIGINAL_LINKS = [
    "https://drive.google.com/uc?export=download&id=1DnuslAy6KoH47AQTmQDEAu0C04pDBetP",
    "https://drive.usercontent.google.com/download?id=1DnuslAy6KoH47AQTmQDEAu0C04pDBetP&export=download&confirm=t",
    "https://beebeeclassroom.com/wp-content/uploads/2022/04/DSKP-KSSR-Semakan-2017-Sains-Tahun-6_ISBN_.pdf",
    "https://c.zoom-a.com/cache/dbp/refpub/1668665312763/DSKP-Sains-6-%28Semakan-2017%29.pdf",
    "https://c.zoom-a.com/cache/dbp/refpub/1668665312763/DSKP-Sains-6-(Semakan-2017).pdf",
]
SCHOOL_SOURCE_PAGES = [
    "https://sites.google.com/moe-dl.edu.my/dskpskfp1/tahun-6-2022",
    "https://sites.google.com/moe-dl.edu.my/sainssksp/dskprptdpk-2-0/dskp-tahun-6",
    "https://sites.google.com/moe-dl.edu.my/panitiasainsskkat/pdpc/dskp",
]
ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "rpt_2027/sains/kssr2017_t6_2021_secondary_mirror_sp_code_ranges_20261107_DRAF.json"
OUT = Path("output/rpt2027_sains_y6_2021_direct_source_audit.json")
CODE = re.compile(r"(?<!\d)([1-9]|1[0-3])\.\d{1,2}\.\d{1,2}(?!\d)")

def inspect():
    import fitz
    ledger=json.loads(INDEX.read_text("utf-8"))
    if ledger.get("official_sp_count")!=96 or ledger.get("academic_release_approved") is not False:
        raise ValueError("Y6 source ledger missing 96-SP academic hold")
    expected={f"{sk}.{n}" for sk,m in ledger["official_sp_codes_by_sk_max_suffix"].items()
              for n in range(1,m+1)}
    if len(expected)!=96:raise ValueError("Missing indexed SP codes")
    out={"release_ready":False,"index_codes":96,"edition":"KSSR Semakan 2017 BPK September 2021",
         "source_original_kpm_hosted_provenance":False,"sources":[]}
    for url in ORIGINAL_LINKS:
        record={"url":url}
        try:
            response=requests.get(url,timeout=25,headers={"User-Agent":"Mozilla/5.0","Accept":"application/pdf,*/*"})
            payload=response.content
            record.update(status_code=response.status_code,content_type=response.headers.get("content-type",""),
                          bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest())
            response.raise_for_status()
            if not payload.startswith(b"%PDF"):raise ValueError("Response not PDF")
            with fitz.open(stream=payload,filetype="pdf") as pdf:
                found=set()
                loc={}
                for i,page in enumerate(pdf):
                    for match in CODE.finditer(page.get_text()):
                        code=match.group(0)
                        if code in expected:
                            found.add(code)
                            loc.setdefault(code,[]).append(i+1)
                missing=sorted(expected-found,key=lambda x:tuple(map(int,x.split("."))))
                record.update(pdf_pages=len(pdf),unique_official_sp_codes=len(found),
                    missing_codes=missing,all_original_sp_codes_found=(len(missing)==0),
                    sp_source_pdf_pages=loc)
        except Exception as exc:
            record["error"]=type(exc).__name__+": "+str(exc)[:230]
        out["sources"].append(record)
        print("SAINS6_KPM2021_DIRECT",record.get("status_code"),
              record.get("pdf_pages"),record.get("unique_official_sp_codes",0),
              record.get("error",""),flush=True)
    # Find public Google Drive file IDs embedded by teacher school portals.
    # School portals are a locator only, not KPM academic verification.
    import html
    out["school_portal_drive_candidates"]=[]
    for portal in SCHOOL_SOURCE_PAGES:
        entry={"site":portal}
        try:
            resp=requests.get(portal,timeout=20,headers={"User-Agent":"Mozilla/5.0"})
            entry["http_status"]=resp.status_code
            raw=html.unescape(resp.text).replace("\\\\u003d","=").replace("\\\\u0026","&").replace("\\\\u002f","/")
            ids=set(re.findall(r"(?:drive\.google\.com/file/d/|docs\.google\.com/(?:file|document)/d/)([A-Za-z0-9_-]{20,})",raw))
            # Encoded escaped solidus paths are common in Google Sites.
            ids|=set(re.findall(r"(?:drive\.google\.com.{0,120}?/file/d/)([A-Za-z0-9_-]{20,})",raw))
            entry["candidate_drive_file_ids"]=sorted(ids)
            entry["html_length"]=len(raw)
        except Exception as exc:
            entry["error"]=type(exc).__name__+": "+str(exc)[:150]
        out["school_portal_drive_candidates"].append(entry)
        print("SAINS6_SCHOOL_PORTAL_DRIVE_ID",portal,
              entry.get("http_status"),len(entry.get("candidate_drive_file_ids",[])),
              entry.get("candidate_drive_file_ids",[])[:25],flush=True)
    if any(row.get("pdf_pages")==94 and row.get("all_original_sp_codes_found")
           for row in out["sources"]):
        out["all_96_text_codes_located"]=True
    else:
        out["all_96_text_codes_located"]=False
    return out

if __name__=="__main__":
    report=inspect()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n","utf-8")
    print("SAINS6_2021_DIRECT_SOURCE_AVAILABLE",report["all_96_text_codes_located"],flush=True)
