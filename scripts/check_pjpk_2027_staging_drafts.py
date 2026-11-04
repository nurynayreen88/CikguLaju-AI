#!/usr/bin/env python3
"""Fail-closed read-only validator for 400 staged PJPK RPH; never changes production."""
from __future__ import annotations
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

MANIFEST = Path("audits/pjpk_2027_staging_manifest_20261104.json")
EXPECTED = {
 "year2_pj":41, "year2_pk":53, "year3_pj":38, "year3_pk":41,
 "year4_pj":34, "year4_pk":41, "year5_pj":33, "year5_pk":44,
 "year6_pj":34, "year6_pk":41,
}
FLAGS = ("rpt_2027_exact_slot_verified","textbook_page_verified",
 "pedagogical_qa_verified","word_a4_verified","telegram_runtime_verified",
 "web_runtime_verified","production_ready")
PATH = re.compile(r"^rph_standalone/pjpk/year([2-6])_(pj|pk)/([a-zA-Z0-9_]+)\.md$")


def check(root: Path) -> dict:
 errors=[]
 try: obj=json.loads((root/MANIFEST).read_text(encoding="utf-8"))
 except (ValueError,OSError) as e: return {"result":"FAIL","issues":[str(e)]}
 entries=obj.get("records")
 if obj.get("schema_version") != 2 or not isinstance(entries,list):
  return {"result":"FAIL","issues":["Expected manifest schema version 2"]}
 seen=set(); counts=Counter()
 for e in entries:
  path=e.get("path",""); m=PATH.fullmatch(path)
  if not m: errors.append(f"Bad path: {path}"); continue
  if path in seen: errors.append(f"Duplicate: {path}"); continue
  seen.add(path); year=int(m[1]); kind=m[2]; counts[f"year{year}_{kind}"]+=1
  if e.get("year")!=year or e.get("component")!=kind.upper(): errors.append(f"Scope mismatch: {path}")
  if e.get("status")!="DRAFT_NOT_APPROVED": errors.append(f"Unsafe status: {path}")
  if e.get("dskp_code_presence_checked") is not True: errors.append(f"DSKP code unchecked: {path}")
  for key in FLAGS:
   if e.get(key) is not False: errors.append(f"Unsafe gate {key}: {path}")
  f=root/path
  if not f.is_file() or f.is_symlink(): errors.append(f"Missing or symlink: {path}"); continue
  txt=f.read_text(encoding="utf-8")
  if len(txt)<600 or not txt.startswith("# RPH Pendidikan"): errors.append(f"Truncated: {path}")
  if "DRAF" not in txt[:700]: errors.append(f"No DRAFT marking: {path}")
  if not re.search(r"\*\*SK(?:[^*]*)\*\*",txt[:1300]): errors.append(f"Missing SK: {path}")
  if not re.search(r"\*\*SP(?:[^*]*)\*\*",txt[:1600]): errors.append(f"Missing SP: {path}")
  if not re.search(r"\*\*(?:Objektif|Objektif pembelajaran)[^*]*\*\*",txt): errors.append(f"Missing objective: {path}")
  if not re.search(r"\*\*Aktiviti 1[^*]*\*\*",txt) or not re.search(r"\*\*Aktiviti 2[^*]*\*\*",txt): errors.append(f"Missing activities: {path}")
  if not re.search(r"\*\*(?:Pentaksiran|Pengukuhan)[^*]*\*\*",txt): errors.append(f"Missing PBD: {path}")
  if "**Penutup" not in txt: errors.append(f"Missing closure: {path}")
 if len(entries)!=400 or len(seen)!=400: errors.append(f"Wrong manifest count {len(entries)} unique {len(seen)}")
 if counts!=Counter(EXPECTED) or obj.get("counts")!=EXPECTED: errors.append(f"Counts mismatch: {dict(counts)}")
 actual={p.relative_to(root).as_posix() for p in (root/"rph_standalone/pjpk").glob("year*_*/*.md")}
 if actual!=seen: errors.append(f"Inventory drift: {len(actual-seen)} extra, {len(seen-actual)} missing")
 for a,b,years in [
   ("rpt_staging/pjpk/pendidikan_kesihatan_2027_year2_year3.csv",67,{2:35,3:32}),
   ("rpt_staging/pjpk/pendidikan_kesihatan_2027_year4_year6.csv",96,{4:32,5:32,6:32})
 ]:
  p=root/a
  if not p.is_file(): errors.append(f"Missing RPT: {a}"); continue
  with p.open(newline="",encoding="utf-8") as f: rr=list(csv.DictReader(f))
  if len(rr)!=b: errors.append(f"Bad RPT size: {a} {len(rr)}")
  for year,n in years.items():
   ids=[r["pdp"] for r in rr if r["year"]==str(year)]
   if ids!=[str(i).zfill(3) for i in range(1,n+1)]: errors.append(f"Non-contiguous RPT: Year {year}")
   if any(not (root/f"rph_standalone/pjpk/year{year}_pk/lesson_{x}.md").is_file() for x in ids):
    errors.append(f"RPH missing for PK Year {year}")
   for r in rr:
    if r["year"]!=str(year): continue
    if r["status"]!="DRAFT_UNAPPROVED" or r["duration_minutes"]!="30": errors.append(f"Unsafe RPT row: {year} {r['pdp']}")
    if any(not s.startswith(r["sk"]+".") for s in r["sp_codes"].split(";")):
     errors.append(f"Unlinked SK/SP in PK: {year} {r['pdp']}")
 critical=root/"rph_standalone/pjpk/year6_pj/lesson_033.md"
 if not critical.is_file() or "DRAF TERHALANG" not in critical.read_text(encoding="utf-8") or "KONFLIK DSKP/RPT" not in critical.read_text(encoding="utf-8"):
  errors.append("Y6 PJ PdP033 conflict must remain blocked")
 return {"result":"FAIL" if errors else "PASS_STATIC_ONLY","records":len(entries),
         "counts":dict(counts),"issues":errors,
         "note":"Structural checks are not teacher approval, A4 render, Telegram, or Web runtime tests."}


if __name__=="__main__":
 result=check(Path(sys.argv[1] if len(sys.argv)>1 else ".").resolve())
 print(json.dumps(result,ensure_ascii=False,indent=2))
 sys.exit(0 if result["result"]=="PASS_STATIC_ONLY" else 1)
