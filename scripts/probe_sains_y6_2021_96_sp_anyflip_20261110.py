"""Fetch a public facsimile of KPM 2021 Sains Year6 DSKP and locate 96 SP.

The site is NOT the original KPM PDF; this read-only probe extracts text
contexts for manual crosscheck and never creates teacher RPT or signoff.
"""
from __future__ import annotations
from bs4 import BeautifulSoup
from pathlib import Path
import hashlib
import json
import re
import requests

from rpt_2027.common.calendar_week_mapping_staging import load_calendar_weeks

ROOT=Path(__file__).resolve().parents[1]
SOURCE_INDEX=ROOT/"rpt_2027/sains/kssr2017_t6_2021_secondary_mirror_sp_code_ranges_20261107_DRAF.json"
URLS=[
    "https://anyflip.com/mcde/frne/basic/51-94",
    "https://anyflip.com/mcde/frne/basic",
    "https://fliphtml5.com/mcbrg/xizk/DSKP_KSSR_Semakan_2017_Sains_Tahun_6/",
]
CODE=re.compile(r"(?<!\d)(?:[1-9]|1[0-3])\.\d{1,2}\.\d{1,2}(?!\d)")


def official_codes():
    j=json.loads(SOURCE_INDEX.read_text("utf-8"))
    if j["academic_release_approved"] is not False or j["official_sp_count"]!=96:
        raise ValueError("Original 2021 96-SP index changed or incorrectly approved")
    result={f"{sk}.{n}" for sk,maximum in
            j["official_sp_codes_by_sk_max_suffix"].items()
            for n in range(1,maximum+1)}
    if len(result)!=96:
        raise ValueError("Source code inventory not 96")
    return result


def probe():
    expected=official_codes()
    result={"status":"READ_ONLY_SOURCE_CONTEXT_NOT_KPM_ORIGINAL_PDF",
            "academic_release_approved":False,"source_urls":URLS,
            "expected_unique_sp":96,"sources":[]}
    for url in URLS:
        record={"url":url}
        try:
            response=requests.get(url,timeout=28,headers={"User-Agent":"Mozilla/5.0"})
            record.update(http_status=response.status_code,html_bytes=len(response.content),
                          html_sha256=hashlib.sha256(response.content).hexdigest())
            response.raise_for_status()
            soup=BeautifulSoup(response.text,"html.parser")
            for tag in soup(["script","style","noscript"]):
                tag.decompose()
            raw=soup.get_text(" ",strip=True)
            clean=re.sub(r"\s+"," ",raw)
            codes=list(CODE.finditer(clean))
            hits={}
            for m in codes:
                if m.group(0) in expected:
                    hits.setdefault(m.group(0),[]).append({
                        "char_offset":m.start(),
                        "context":clean[max(0,m.start()-30):m.end()+330]
                    })
            missing=sorted(expected-hits.keys(),key=lambda x:tuple(map(int,x.split("."))))
            record.update(text_chars=len(clean),official_unique_code_hits=len(hits),
                          missing_codes=missing,
                          matching_code_contexts={code:examples[:3] for code,examples in sorted(
                              hits.items(),key=lambda x:tuple(map(int,x[0].split("."))))})
        except Exception as ex:
            record["error"]=type(ex).__name__+": "+str(ex)[:200]
        print("SAINS_Y6_ANYFLIP_PROBE",url,record.get("http_status"),
              record.get("official_unique_code_hits",0),record.get("text_chars",0),
              record.get("error",""),flush=True)
        result["sources"].append(record)
    result["source_code_coverage_ready"] = source_code_coverage_complete(result)
    result["status"] = (
        "SOURCE_CODE_COVERAGE_FOUND_NOT_ACADEMIC_APPROVAL"
        if result["source_code_coverage_ready"]
        else "SOURCE_COVERAGE_BLOCKED")
    return result


def source_code_coverage_complete(result):
    """Require 96 matched codes within one readable source before green CI.

    Code coverage is only a prerequisite, never academic text approval.
    A 403 mirror and an empty HTML result must NEVER pass as verified.
    """
    if (not isinstance(result, dict)
            or result.get("expected_unique_sp") != 96
            or result.get("academic_release_approved") is not False):
        return False
    for source in result.get("sources", []):
        if not isinstance(source, dict):
            continue
        contexts = source.get("matching_code_contexts")
        if (source.get("http_status") == 200
                and source.get("official_unique_code_hits") == 96
                and type(source.get("text_chars")) is int
                and source["text_chars"] >= 10000
                and source.get("missing_codes") == []
                and isinstance(contexts, dict)
                and len(contexts) == 96):
            return True
    return False


if __name__=="__main__":
    result=probe()
    out=Path("output/sains_y6_2021_anyflip_96_sp_source_contexts_20261110.json")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n","utf-8")
    print("Y6_2021_OFFICIAL_SP_COVERAGE_SUMMARY",
          [(x["url"],x.get("official_unique_code_hits",0)) for x in result["sources"]],flush=True)
    print("Y6_2021_SOURCE_COVERAGE_STATUS",result["status"],flush=True)
    if not result["source_code_coverage_ready"]:
        raise SystemExit("BLOCKED: No complete 96-SP source contexts; "
                         "RPT academic release remains forbidden")
