#!/usr/bin/env python3
"""Read-only curriculum crosswalk for PJPK 2027 staging, no READY promotions.

Verify all 339 RPT rows against numbered RPH source documents. The exception
Year 6 PJ PdP 033 is deliberately blocked due to conflicting source SP.
"""
from __future__ import annotations
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "rpt_2027/pjpk/pjpk_2027_rpt_manifest.json"
HEAD = re.compile(r"^\*\*([^*\n]+?):\*\*\s*(.*?)\s*$", re.M)
S = re.compile(r"(?<!\d)\d+\.\d+(?![\d.])")
P = re.compile(r"(?<!\d)\d+\.\d+\.\d+(?![\d.])")
EXPECTED = {2: (37,35), 3:(38,32), 4:(34,32), 5:(33,32), 6:(34,32)}
BLOCKED = (6,"PJ",33)


def inspect(root=ROOT):
    manifest = json.loads((root / "rpt_2027/pjpk/pjpk_2027_rpt_manifest.json").read_text(encoding="utf-8"))
    records = manifest["records"]
    issues=[]
    dup=collections.Counter()
    count=collections.Counter()
    overlaps=collections.defaultdict(list)
    if len(records) != 339 or len(manifest["weeks"]) != 38 or manifest["ready"] is not False:
        issues.append("Manifest count/week/readiness mismatch")
    for w in manifest["weeks"]:
        if not (w.get("groupA") and w.get("groupB") and 1<=int(w.get("week",0))<=38):
            issues.append(f"Invalid weekly groups: {w}")
    for rec in records:
        year,kind,num = rec["year"],rec["subject"],rec["pdp"]
        key=(year,kind,num)
        dup[key]+=1
        count[(year,kind)]+=1
        if rec["ready"] is not False:
            issues.append(f"Unexpected READY: {key}")
        if any(x.rsplit(".",1)[0] not in rec["sk"] for x in rec["sp"]):
            if key != BLOCKED:
                issues.append(f"SP parent SK mismatch: {key}")
        if key == BLOCKED:
            if rec["status"]!="BLOK_KONFLIK_SK_SP" or "5.2.2" not in rec["sp"]:
                issues.append("Y6 PJ033 must remain source-conflict BLOCKED")
            continue
        if rec["status"]!="DRAF_CADANGAN":
            issues.append(f"Unsafe status: {key} = {rec['status']}")
        path=root / f"rph_standalone/pjpk/year{year}_{kind.lower()}/lesson_{num:03d}.md"
        if not path.is_file():
            issues.append(f"Missing source: {path}")
            continue
        t=path.read_text(encoding="utf-8")
        labels={m[1].strip().lower():m[2].strip() for m in HEAD.finditer(t)}
        if not labels.get("status","").upper().startswith("DRAF"):
            issues.append(f"RPH is not explicitly DRAFT: {key}")
        title=labels.get("tajuk") or labels.get("unit/tajuk")
        if title != rec["title"]:
            issues.append(f"Title differs RPT/RPH: {key}: {title} != {rec['title']}")
        if S.findall(labels.get("sk",""))!=rec["sk"] or P.findall(labels.get("sp",""))!=rec["sp"]:
            issues.append(f"SK/SP mismatch: {key}")
        if not (labels.get("objektif") or labels.get("objektif pembelajaran")):
            issues.append(f"Missing objectives: {key}")
        activities=[(k,v) for k,v in labels.items() if re.match(r"aktiviti [12]\b",k)]
        if len(activities)!=2 or any(len(v)<45 for k,v in activities):
            issues.append(f"Insufficient activities: {key}")
        if not (labels.get("pengukuhan/pbd") or labels.get("pentaksiran/pbd") or
                labels.get("pengukuhan dan penilaian (pbd)") or labels.get("pentaksiran")):
            issues.append(f"Missing assessment: {key}")
        if not labels.get("penutup"):
            issues.append(f"Missing closure: {key}")
        if kind=="PK":
            for section,body in activities:
                normalized=re.sub(r"\s+"," ",body.casefold()).strip()
                overlaps[(year,rec["sk"][0],normalized)].append((num,section))
        if kind=="PJ" and num==22 and year==3:
            if not all(x in t for x in ("hiperventilasi","pengawasan","BELUM DITAKSIR","tanpa pengawasan")):
                issues.append("Aquatic Y3 PJ022 safety/PBD safeguards missing")
        if kind=="PK" and year==2 and 9<=num<=12:
            if "bimbang dan cemburu" not in title.casefold() or "dan marah" in t.casefold():
                issues.append(f"Wrong emotional SK3.1 topic Y2 PdP {num}")
        if kind=="PK" and year==4 and 13<=num<=15:
            if "gejala sosial" not in title.casefold() or "kad tugas rumah" in t.casefold():
                issues.append(f"Wrong social-issues SK4.1 topic Y4 PdP {num}")
    for y,(pj,pk) in EXPECTED.items():
        if count[(y,"PJ")]!=pj or count[(y,"PK")]!=pk:
            issues.append(f"Wrong PdP count Year{y}: PJ{count[(y,'PJ')]} PK{count[(y,'PK')]}")
    if max(dup.values(),default=0)>1:
        issues.append("Duplicate RPT PdP identities")
    duplicate_activity_groups={f"Y{y} SK{sk}":v for (y,sk,activity),v in overlaps.items() if len(v)>1 and len(activity)>70}
    return {
        "status":"PASS_STATIC" if not issues else "FAIL",
        "rpt_records":len(records),
        "rph_numbered_checked":len(records)-1,
        "year_counts":{str(y):{"PJ":count[(y,"PJ")],"PK":count[(y,"PK")]} for y in EXPECTED},
        "known_blocked":[BLOCKED],
        "duplicate_activity_groups":len(duplicate_activity_groups),
        "repeated_activity_evidence":list(duplicate_activity_groups.items())[:30],
        "issues":issues,
        "note":"Static inspection is not independent textbook visual validation, teacher signoff or real Telegram delivery."
    }


if __name__=="__main__":
    result=inspect()
    print(json.dumps(result,ensure_ascii=False,indent=2))
    sys.exit(0 if result["status"]=="PASS_STATIC" else 1)
