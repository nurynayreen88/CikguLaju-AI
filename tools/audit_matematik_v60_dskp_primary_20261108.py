"""Reconcile Telegram Matematik v25.99 and v60 with reference DSKP SP codes.

Inputs:
- Actual checksum-verified Matematik v25.99 canonical Telegram sequence
- All 585 checksum-verified v60 RPH Markdown
- Explicit SP inventory transcribed from primary Drive DSKP PDFs Tahun 2–6,
  pinned to PDF sha256. No PDF content is invented/retrieved in CI.

An absent code means 'not found in the supplied reference PDF', NOT that every
curriculum edition is invalid. Always HOLD release pending academic review.
Never rewrite SK/SP, select candidates, or change any production database.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from tools.audit_matematik_v60_v2599_native_source_20261108 import audit_snapshot
from rph_standalone.matematik.v60_source_loader import get_lesson
from web.matematik_v60_native_rows import parse_lesson

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = ROOT / "audits/matematik_v60_dskp_primary_sp_inventory_20261108.json"
SP_CODE = re.compile(r"(?<![0-9.])([0-9]{1,2}[.][0-9]{1,2}[.][0-9]{1,2})(?![0-9.])")
EXPECTED_DSKP_COUNTS = {2: 70, 3: 102, 4: 85, 5: 72, 6: 38}
EXPECTED_DSKP_HASH = {
    2: "70fc940fe036db4ce40482aceaf7843ae3f3fd33988eaf3842aba1bd90b985cb",
    3: "3707c7e995a36caf4aa3cd8af1960be3c6e985f9886a468d71f536cd9878ea60",
    4: "8a8b066f863d1b635ddeaf5ad57241dafca4e0434fe9058317879aa67821563f",
    5: "603a8aaeb124a7b864d8473fc3f11f09339d9b609c3e4c45daff5e03eb8adda4",
    6: "e48576169c12cc9666675770432a425e573686a331fba6bcd7f01e33787476a9",
}


def audit_dskp_primary():
    data = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    if (data.get("schema") != "cikgulaju.math.primary_dskp_sp_inventory.v1"
            or data.get("academic_signoff") is not False):
        raise ValueError("Unapproved or unidentified DSKP source inventory")
    canonical = audit_snapshot()
    years = {}
    affected = []
    for year in range(2, 7):
        doc = data["documents"][str(year)]
        official = doc["sp_codes"]
        if (len(official) != EXPECTED_DSKP_COUNTS[year]
                or len(official) != len(set(official))
                or doc["sha256"] != EXPECTED_DSKP_HASH[year]
                or not all(SP_CODE.fullmatch(x) for x in official)):
            raise ValueError(f"DSKP Year {year} source inventory changed; reverify primary PDF")
        # Year 2 PDF has a typography issue: '4. 1.1' means '4.1.1'.
        if year == 2 and "4.1.1" not in official:
            raise ValueError("Verified Year2 DSKP normalization absent")
        codes = set(official)
        rows = canonical["candidate_crosswalk"]["by_year"][str(year)]["candidates"]
        absent_unique = set()
        native_codes = set()
        affected_count = 0
        for row in rows:
            row_codes = set()
            for pair in row["sksp"]:
                row_codes.update(SP_CODE.findall(pair["sp"]))
            if not row_codes:
                raise ValueError("Native Telegram PdP without a parseable SP code")
            native_codes.update(row_codes)
            absent = sorted(row_codes - codes)
            if absent:
                affected_count += 1
                absent_unique.update(absent)
                affected.append({
                    "year": year,
                    "pdp_code": row["pdp_code"],
                    "pdp_title": row["native_title"],
                    "unit": row["native_unit"],
                    "native_sksp": row["sksp"],
                    "missing_from_reference_dskp": absent,
                    "review_status": "HOLD — confirm official DSKP/RPT and lesson activities",
                    "approved": False,
                })
        v60_codes = set()
        for number in range(1, 118):
            source = parse_lesson(get_lesson(year, number), year, number)
            v60_codes.add(source["_sp_code"])
        missing_v60 = sorted(v60_codes - codes)
        years[str(year)] = {
            "reference_dskp_drive_file_id": doc["drive_file_id"],
            "reference_pdf_sha256": doc["sha256"],
            "dskp_distinct_sp_codes": len(codes),
            "native_pdp_count": len(rows),
            "native_distinct_sp_codes": len(native_codes),
            "native_absent_distinct_sp_codes": len(absent_unique),
            "native_absent_codes": sorted(absent_unique),
            "native_pdp_requiring_review": affected_count,
            "v60_distinct_sp_codes": len(v60_codes),
            "v60_absent_codes": missing_v60,
            "academic_signoff": False,
        }
    # Semantic conflicts are a different axis from SP-code presence.
    # Never claim that a code existing in a PDF verifies its teaching scope.
    ledger_path = ROOT / "audits/matematik_y6_pdp004_006_semantic_conflict_20261108.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    if (ledger.get("schema") != "cikgulaju.math.y6.native_semantic_hold.v1"
            or ledger.get("approved_count") != 0 or ledger.get("final_ready") is not False
            or ledger.get("production_modified") is not False
            or len(ledger.get("cases", [])) != 2):
        raise ValueError("Unexpected Mathematics semantic-review ledger")
    by_pdp = {
        item["pdp_code"]: item
        for item in canonical["candidate_crosswalk"]["by_year"]["6"]["candidates"]
    }
    extra_semantic = []
    for case in ledger["cases"]:
        key = case["native_pdp_code"]
        native = by_pdp.get(key)
        if (native is None or native["native_title"] != case["native_title"]
                or native["source_sequence_numbers"] != [str(case["native_lesson_number"])]
                or native["sksp"] != [{"sk": case["native_sk"], "sp": case["native_sp"]}]
                or case["native_sp"] not in data["documents"]["6"]["sp_codes"]
                or case.get("ready") is not False):
            raise ValueError(f"Maths semantic evidence conflicts with actual source {key}")
        # These are precisely codes that *pass* naive presence checking.
        if any(p["pdp_code"] == key for p in affected):
            raise ValueError("Semantic case unexpectedly counted as missing code")
        if case.get("candidate_dskp_sp") and (
                case["candidate_dskp_sp"] not in data["documents"]["6"]["sp_codes"]):
            raise ValueError("Suggested semantic SP not in reference DSKP")
        extra_semantic.append({
            "year": 6,
            "pdp_code": key,
            "native_title": native["native_title"],
            "native_sp": case["native_sp"],
            "reason": case["evidence"],
            "candidate_sp": case.get("candidate_dskp_sp"),
            "status": "REQUIRES_ACADEMIC_REVIEW",
            "approved": False,
        })
    return {
        "schema": "cikgulaju.math.v60_dskp_code_presence_audit.v1",
        "run_status": "CODE_AUDIT_ONLY",
        "source_archive": canonical["audited_source"],
        "note": "Code present/absent only. A source mismatch does not authorize remapping or declare a curriculum edition invalid. Only academic sign-off can approve.",
        "years": years,
        "affected_native_pdp_total": len(affected),
        "distinct_absent_code_year_pairs": sum(
            row["native_absent_distinct_sp_codes"] for row in years.values()),
        "affected_pdp": affected,
        "code_present_but_semantically_conflicting_known_cases": extra_semantic,
        "known_semantic_conflict_count": len(extra_semantic),
        "known_distinct_pdp_requiring_review_minimum": len(affected) + len(extra_semantic),
        "coverage_warning": "This is a minimum of 98 absent-code PdP and 2 independently verified meaning conflicts, not a complete semantic audit of all 528 PdP.",
        "release_decision": "HOLD",
        "academic_signoff": False,
        "runtime_e2e_passed": False,
        "production_modified": False,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", help="Write fresh report path, refuse overwrite")
    p.add_argument("--require-zero-conflicts", action="store_true",
                   help="Strict source harmonization gate; exits nonzero while conflicts remain")
    args = p.parse_args()
    report = audit_dskp_primary()
    body = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        target = Path(args.output)
        with target.open("x", encoding="utf-8") as file:
            file.write(body + "\n")
    print("Academic source check: distinct absent codes=",
          report["distinct_absent_code_year_pairs"],
          "affected native PdP=", report["affected_native_pdp_total"])
    for y, info in report["years"].items():
        print("Year", y, "reference code count", info["dskp_distinct_sp_codes"],
              "native absent", info["native_absent_distinct_sp_codes"],
              "affected PdP", info["native_pdp_requiring_review"],
              "v60 absent", len(info["v60_absent_codes"]))
    print("Known semantic conflicts with existing SP codes:",
          report["known_semantic_conflict_count"],
          "minimum distinct native PdP review:", report["known_distinct_pdp_requiring_review_minimum"])
    print("RELEASE HOLD: code presence is NOT semantic approval or Web/Telegram E2E")
    if args.require_zero_conflicts and (
            report["affected_native_pdp_total"] > 0
            or report["known_semantic_conflict_count"] > 0
            or any(info["v60_absent_codes"] for info in report["years"].values())):
        raise SystemExit("RELEASE HOLD: unresolved primary DSKP code conflicts")


if __name__ == "__main__":
    main()
