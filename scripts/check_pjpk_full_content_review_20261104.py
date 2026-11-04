#!/usr/bin/env python3
"""PJPK Year2-6 full release audit: read-only, fail-closed, no DB access.

Compares 339 planned RPT PdP to 338 source RPH, validates key content
fixes and flags items that still require verified textbook, teacher approval
and real Telegram delivery. It never promotes READY.
"""
from __future__ import annotations
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "rpt_2027/pjpk/pjpk_2027_rpt_manifest.json"
RELEASE_FLAGS = ("READY", "DRAF TERHALANG")

def fields(text):
    out = {}
    for m in re.finditer(r"^\*\*([^*\n]+?):\*\*\s*(.+)$", text, re.M):
        out[m.group(1).strip().casefold()] = m.group(2).strip()
    return out

def standard_codes(text, mode):
    pat = r"(?<!\d)\d+\.\d+\.\d+(?!\d)" if mode == "SP" else r"(?<!\d)\d+\.\d+(?![\d.])"
    return re.findall(pat, text or "")

def run():
    report={"schema_version":1,"status":"STATIC_ONLY_NOT_READY",
        "counts":{},"findings":[],"individual":[],"notes":[
        "Content and safety gates require human subject-matter review.",
        "Word/PDF rendering and real Telegram document delivery are separate checks.",
        "2027 local class schedule, state holidays and textbook physical pages need validation.",
        "Year1 KP2027 excluded, four Year2 aquatic inserts not approved.",
        "Source RPT Year6 PJ PdP033 still requires DSKP reconciliation."]}
    manifest=json.loads(MANIFEST.read_text(encoding="utf-8"))
    if len(manifest.get("records", [])) != 339 or len(manifest.get("weeks", [])) != 38:
        raise AssertionError("Unexpected RPT master")
    counted=collections.Counter()
    seen=set()
    dup=collections.defaultdict(list)
    fatal=[]
    for row in manifest["records"]:
        y,sub,n=row["year"],row["subject"],row["pdp"]
        ident=(y,sub,n)
        if ident in seen: fatal.append(f"DUPLICATE RPT {ident}")
        seen.add(ident);counted[f"{y}-{sub}"]+=1
        if row.get("ready") is not False: fatal.append(f"UNSAFE READY flag {ident}")
        if y == 6 and sub == "PJ" and n == 33:
            if row.get("status") != "BLOK_KONFLIK_SK_SP": fatal.append("Y6 PJ033 must remain blocked")
            report["individual"].append({"year":y,"component":sub,"pdp":n,"disposition":"BLOCKED_SOURCE_CONFLICT"})
            continue
        path=ROOT / f"rph_standalone/pjpk/year{y}_{sub.lower()}/lesson_{n:03d}.md"
        if not path.is_file(): fatal.append(f"MISSING RPH {ident}"); continue
        text=path.read_text(encoding="utf-8")
        src=fields(text)
        title=src.get("tajuk") or src.get("unit/tajuk")
        actualSK=standard_codes(src.get("sk"),"SK")
        actualSP=standard_codes(src.get("sp"),"SP")
        if row["title"] != title or row["sk"]!=actualSK or row["sp"]!=actualSP:
            fatal.append(f"CROSSWALK MISALIGNMENT {ident}")
        if "draf" not in src.get("status","").lower(): fatal.append(f"UNSAFE RPH status {ident}")
        if not src.get("objektif") or not src.get("set induksi") or not src.get("penutup"):
            fatal.append(f"MISSING RPH ESSENTIAL {ident}")
        acts=[(k,v) for k,v in src.items() if k.startswith("aktiviti 1") or k.startswith("aktiviti 2")]
        if len(acts)!=2: fatal.append(f"ACTIVITY COUNT {ident}")
        a1=next((v for k,v in acts if k.startswith("aktiviti 1")),"")
        a2=next((v for k,v in acts if k.startswith("aktiviti 2")),"")
        if sub=="PJ" and ("Guru menunjukkan lakuan kemahiran sasaran" in a1 or
                          "Murid mencuba kemahiran menggunakan tanda laluan" in a2):
            fatal.append(f"GENERIC PLACEHOLDER {ident}")
        for k,v in acts:
            dup[(sub,k.split(" — ")[0],v.strip())].append(ident)
        words=len(text.split())
        if words<160 or words>550:report["findings"].append({"type":"LENGTH_REVIEW","lesson":ident,"words":words})
        disposition="DRAFT_PENDING_HUMAN_BOOK_AND_RUNTIME_REVIEW"
        report["individual"].append({"year":y,"component":sub,"pdp":n,
            "rph_path":path.relative_to(ROOT).as_posix(),"word_count":words,
            "code_title_crosswalk":row["title"]==title and row["sk"]==actualSK and row["sp"]==actualSP,
            "disposition":disposition})
    expected={ "2-PJ":37,"2-PK":35,"3-PJ":38,"3-PK":32,
       "4-PJ":34,"4-PK":32,"5-PJ":33,"5-PK":32,"6-PJ":34,"6-PK":32}
    if dict(counted)!=expected:fatal.append(f"COUNT MISMATCH {dict(counted)}")
    candidates={
      (3,"PJ",22):["kolam","penyelamat","tangguh"],
      (3,"PJ",23):["keribas","kolam","tangguh"],
      (3,"PJ",25):["karom","jentikan"],
      (3,"PJ",26):["seremban","uncang"],
      (3,"PJ",27):["dam","strategi"],
      (3,"PJ",28):["catur","strategi"],
      (5,"PJ",17):["smesy","adangan"],
      (6,"PJ",27):["Libat","elak"],
      (6,"PJ",28):["Hidup Mati","elak"],
      (5,"PJ",30):["Konda Kondi","pukulan"],
      (5,"PJ",31):["Tating Lawi Ayam","timang"],
      (6,"PJ",26):["Kad Misteri","pandu arah"]
    }
    for key,terms in candidates.items():
        y,sub,n=key
        text=(ROOT / f"rph_standalone/pjpk/year{y}_{sub.lower()}/lesson_{n:03d}.md").read_text(encoding="utf-8")
        for term in terms:
            if term.casefold() not in text.casefold():fatal.append(f"SKILL-SPECIFIC MISSING {key} {term}")
        if key in [(6,"PJ",27),(6,"PJ",28)] and "pertukaran baton" in text:
            fatal.append(f"WRONG SPORT BATON {key}")
    repeated=[{"subject":s,"field":f,"count":len(rows),"lesson_examples":rows[:6]}
              for (s,f,v),rows in dup.items() if len(rows)>1 and v]
    repeated.sort(key=lambda x:-x["count"])
    report["counts"]={"RPT_PDP":len(seen),"RPH_numbered_found":len(report["individual"])-1,
      "blocked_RPT":1,"PJ_numbered":176,"PK_numbered":163,
      "source_page_unverified":sum(1 for r in manifest["records"] if r["subject"]=="PJ" and "BELUM" in str(r.get("bt","")).upper()),
      "repeated_activity_templates":len(repeated),"repeated_templates_examples":repeated[:12],
      "fatal_count":len(fatal),"manual_content_review_required":338}
    report["fatal"]=fatal
    report["status"]="FAIL_STATIC" if fatal else "PASS_STATIC_ONLY_NOT_READY"
    return report

if __name__ == "__main__":
    result=run()
    print(json.dumps(result,ensure_ascii=False,indent=2))
    sys.exit(1 if result["fatal"] else 0)
