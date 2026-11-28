"""Read-only integration preflight for Science 5P Web selections.

The native catalogue is authoritative. No route, quota charge, feature
activation, or public download. Academic approval remains a separate gate.
"""
import argparse
import json
import re
from pathlib import Path

from tools.audit_science_native_5p_documents_20261128 import inventory, support_inventory, COUNTS
from tools.export_science_native_5p_mapping_input import collect
from web.native_telegram_sequence_rph_client import verified_native_sequence_available

def map_catalogue(year, catalogue, drafts):
    if type(year) is not int or year not in COUNTS:
        raise ValueError("Unsupported Science 5P year")
    prefix = {5:"v", 6:"w"}[year]
    if (catalogue.get("year") != year
        or catalogue.get("source") != "telegram-native-pdp-sequence"
        or catalogue.get("catalogue_prefix") != prefix
        or catalogue.get("rpt_count_match") is not True
        or catalogue.get("native_selection_count") != COUNTS[year]
        or catalogue.get("unique_lesson_ids") != COUNTS[year]):
        raise ValueError("Wrong native catalogue version or count")
    rows = catalogue["records"]
    if len(rows) != COUNTS[year] or len(drafts) != COUNTS[year]:
        raise ValueError("Incomplete Science source inventory")
    if [r["lesson_id"] for r in rows] != [d["lesson_id"] for d in drafts]:
        raise ValueError("Native lesson identity/order mismatch")
    unit_to_token = {}
    token_to_unit = {}
    mappings = {}
    for r, d in zip(rows, drafts, strict=True):
        token = r["unit"]
        unit = d["unit"]
        if (r.get("year") != year or r.get("subject") != "SCIENCE"
            or r.get("curriculum") != "KSSR" or r.get("ready") is not False
            or not isinstance(token,str) or not re.fullmatch(prefix+r"[a-f0-9]{24}",token)):
            raise ValueError("Invalid native selection")
        if token_to_unit.setdefault(token,unit) != unit or unit_to_token.setdefault(unit,token) != token:
            raise ValueError("Native unit grouping mismatch")
        cid = d["lesson_id"]
        if cid in mappings or d["ready"] is not False:
            raise ValueError("Duplicate or unexpectedly released draft")
        mappings[cid] = {"year":year,"subject":"SCIENCE","unit":token,
            "lesson":cid,"source_unit":unit,"source_title":d["title"],
            "source_minutes":d["minutes"],"source_pages":d["textbook_pages"],
            "native_label":r["lesson_label"],"native_unit_label":r["unit_label"],
            "ready":False}
    if len(token_to_unit) != catalogue["unit_count"]:
        raise ValueError("Native unit count mismatch")
    return mappings

def verify_selection(mappings, year, unit, lesson):
    if not isinstance(lesson,str) or lesson not in mappings:
        raise ValueError("Unmapped Science lesson")
    row = mappings[lesson]
    if (row["year"] != year or row["unit"] != unit or row["ready"] is not False):
        raise ValueError("Wrong Science lesson/year/unit")
    return row

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--year",type=int,choices=COUNTS,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--check-availability",action="store_true",
        help="Optional 205 read-only checks on the authorized native backend; no download")
    a = p.parse_args()
    try:
        drafts = inventory(a.year)
        support_inventory(a.year,drafts)
        catalogue = collect(a.year)
        mappings = map_catalogue(a.year,catalogue,drafts)
        checked = 0
        if a.check_availability:
            for row in mappings.values():
                if not verified_native_sequence_available(row["year"],row["subject"],row["unit"],row["lesson"]):
                    raise ValueError("Native source unavailable")
                checked += 1
        report = {"status":"READ_ONLY_NATIVE_SELECTION_PREFLIGHT",
                  "year":a.year,"mapped":len(mappings),"availability_checked":checked,
                  "academic_approved":False,"release":False,"records":list(mappings.values())}
        with a.out.open("x",encoding="utf-8") as f:
            json.dump(report,f,ensure_ascii=False,indent=2)
        print("Mapped:",len(mappings),"availability checked:",checked)
    except Exception as exc:
        p.exit(1,"Preflight failed: "+type(exc).__name__+"\n")

if __name__ == "__main__":
    main()
