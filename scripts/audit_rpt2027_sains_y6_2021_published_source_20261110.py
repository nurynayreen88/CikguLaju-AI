"""Find actual KSSR2017 Sains Year6 2021 standard statements in public facsimile.

Read-only. Published third-party mirrors of KPM-authorized documents are NOT
proof of KPM primary PDF SHA or visual/source teacher approval. No RPH, RPT,
Web catalog, database or teacher release writes.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
import requests
from bs4 import BeautifulSoup

URLS={
    "fliphtml5_primary_facsimile": "https://fliphtml5.com/mcbrg/xizk/DSKP_KSSR_Semakan_2017_Sains_Tahun_6/",
    "fliphtml5_other_facsimile": "https://fliphtml5.com/oreta/ewne/006_DSKP_KSSR_Tahun_6_-_SAINS/",
    "fliphtml5_old_basic_page": "https://online.fliphtml5.com/mcbrg/xizk/files/basic-html/page57.html",
    "published_scribd_text": "https://id.scribd.com/document/545665489/4-Dskp-Kssr-Semakan-2017-Sains-Tahun-6-isbn",
}
ROOT=Path(__file__).resolve().parents[1]
INDEX=ROOT/"rpt_2027/sains/kssr2017_t6_2021_secondary_mirror_sp_code_ranges_20261107_DRAF.json"
PATTERN=re.compile(r"(?<![0-9])(?:1[0-3]|[1-9])\.\d{1,2}\.\d{1,2}(?![0-9])")


def official_codes():
    obj=json.loads(INDEX.read_text("utf-8"))
    assert obj["official_sp_count"]==96 and obj["academic_release_approved"] is False
    result={f"{sk}.{n}" for sk,m in obj["official_sp_codes_by_sk_max_suffix"].items()
            for n in range(1,m+1)}
    if len(result)!=96:
        raise ValueError("Expected exactly 96 official 2021 source code indices")
    return result


def run(output):
    expected=official_codes()
    data=[]
    for label,url in URLS.items():
        record={"source":label,"url":url,"official_pdf_sha256":None,
                "source_approved":False,"academic_rpt_ready":False}
        try:
            resp=requests.get(url,timeout=22,headers={"User-Agent":"Mozilla/5.0 (compatible; CikguLaju-RPT-Source-Audit/1.0)"})
            record["status_code"]=resp.status_code
            record["download_bytes"]=len(resp.content)
            resp.raise_for_status()
            soup=BeautifulSoup(resp.text,"html.parser")
            for t in soup(("script","style","noscript")):t.decompose()
            text=" ".join(soup.stripped_strings)
            matches=list(PATTERN.finditer(text))
            found={m.group(0) for m in matches}
            record.update(
                text_length=len(text),raw_code_matches=len(matches),
                unique_codes=len(found),
                official_codes_found=len(found & expected),
                official_codes_missing=sorted(expected-found,key=lambda x:list(map(int,x.split(".")))),
                unexpected_codes=sorted(found-expected)[:30],
                excerpt=text[:500],
                first_code_context=[
                    {"code":m.group(0),
                     "before":text[max(0,m.start()-25):m.start()],
                     "after":text[m.end():m.end()+160]}
                    for m in matches[:25]
                ]
            )
        except Exception as error:
            record["error"]=type(error).__name__+": "+str(error)[:240]
        data.append(record)
        print("SAINS_Y6_SOURCE_PROBE",label,
              record.get("status_code"),
              record.get("official_codes_found",0),"/96",
              record.get("text_length",0),record.get("error",""),flush=True)
    report={"academic_release_ready":False,
            "requires_kpm_source_original_pdf_sha_and_sp_visual_signoff":True,
            "expected_96_official_codes":len(expected),
            "mirrors":data}
    p=Path(output);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n","utf-8")
    return report


if __name__=="__main__":
    run("output/rpt2027_sains_y6_public_source_probe_20261110.json")
