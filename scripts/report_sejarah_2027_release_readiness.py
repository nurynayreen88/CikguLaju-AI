#!/usr/bin/env python3
"""Non-destructive per-PdP release readiness report for Sejarah Years 4–6.

A green staging CI run is not a pedagogical release. The report distinguishes
the 108 verified document builds from actual textbook, teacher and runtime
signoffs. Run with --require-final-ready for the *release* gate only.
No production endpoint, database or user record is touched.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from web.sejarah_2027_staging_source import SejarahNotReady, lesson, source_fingerprint

MANIFEST = ROOT / "audits/sejarah_y4_y6_release_approval_manifest_20261106.json"
CHECKS = (
    "technical_preview",
    "textbook_visual",
    "teacher_signoff",
    "school_profile",
    "native_parity",
    "word_pdf_layout",
    "evidence_url",
    "source_integrity",
    "rph_status",
    "markdown_status",
    "rpt_status",
)

def report():
    ledger = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if ledger.get("subject") != "Sejarah" or ledger.get("count") != 108:
        raise AssertionError("Wrong release manifest")
    entries = ledger.get("lessons", [])
    if len(entries) != 108:
        raise AssertionError("Incomplete release manifest")

    records = []
    for year in (4, 5, 6):
        src = ROOT / f"rph_standalone/sejarah/y{year}_2027_rph_DRAF.json"
        lessons = json.loads(src.read_text(encoding="utf-8"))["lessons"]
        if len(lessons) != 36:
            raise AssertionError(f"Incomplete Year {year} lesson set")
        plan = ROOT / f"rpt_2027/sejarah/RPT_SEJARAH_TAHUN_{year}_2027_A_B_DRAF.csv"
        with plan.open(encoding="utf-8", newline="") as fh:
            rpt_rows = list(csv.DictReader(fh))
        if len(rpt_rows) != 36:
            raise AssertionError(f"Incomplete Year {year} RPT")
        for pdp, item in enumerate(lessons, 1):
            ident = f"SEJ-T{year}-PDP-{pdp:03d}"
            entry = entries[(year - 4) * 36 + pdp - 1]
            if item["id"] != ident or entry.get("id") != ident or rpt_rows[pdp - 1]["ID"] != ident:
                raise AssertionError(f"Lesson identity mismatch: {ident}")
            rph = item["rph"]
            sign = rph.get("release_signoff") or {}
            md = ROOT / f"rph_standalone/sejarah/tahun_{year}/RPH_{ident}.md"
            text = md.read_text(encoding="utf-8")
            digest = source_fingerprint(year, pdp)
            if not isinstance(digest, str) or len(digest) != 64:
                raise AssertionError(f"Missing source fingerprint: {ident}")
            checks = {
                "technical_preview": entry.get("word_pdf_preview_passed") is True and entry.get("rpt_rph_crosswalk_passed") is True,
                "textbook_visual": entry.get("exact_textbook_exercise_page_verified") is True
                    and rph.get("textbook_page_verified") is True
                    and rph.get("textbook_reference", {}).get("exact_activity_page_confirmed") is True,
                "teacher_signoff": entry.get("teacher_individual_signoff") is True
                    and rph.get("teacher_approval") is True
                    and bool(str(entry.get("teacher_approved_by") or "").strip())
                    and bool(str(sign.get("approved_by") or "").strip()),
                "school_profile": entry.get("school_profile_logo_verified") is True,
                "native_parity": entry.get("telegram_web_native_parity_verified") is True
                    and sign.get("web_telegram_parity_verified") is True,
                "word_pdf_layout": sign.get("word_pdf_layout_verified") is True,
                "evidence_url": bool(str(entry.get("textbook_evidence_url") or "").strip()),
                "source_integrity": entry.get("approved_source_fingerprint") == digest
                    and sign.get("approved_source_fingerprint") == digest,
                "rph_status": rph.get("status") == "FINAL_READY",
                "markdown_status": any(line.strip() == "**Status:** FINAL_READY" for line in text.splitlines()),
                "rpt_status": rpt_rows[pdp - 1].get("Status") == "READY",
            }
            complete = all(checks.values())
            marked = entry.get("release_ready") is True
            if marked and not complete:
                raise AssertionError(f"Unsafe ready flag without full evidence: {ident}")
            try:
                selected = lesson(year, pdp)
            except SejarahNotReady:
                accessible = False
            else:
                accessible = True
                if selected.get("id") != ident:
                    raise AssertionError(f"Wrong released source: {ident}")
            if accessible != (marked and complete):
                raise AssertionError(f"API access disagrees with independent release ledger: {ident}")
            records.append({
                "year": year, "pdp": pdp, "id": ident,
                "ready": complete and marked and accessible,
                "blockers": [name for name in CHECKS if not checks[name]],
                "checks": checks,
            })
    return records

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-final-ready", action="store_true")
    args = parser.parse_args()
    rows = report()
    by_year = {y: sum(int(r["ready"]) for r in rows if r["year"] == y) for y in (4, 5, 6)}
    gates = Counter(k for r in rows for k in r["blockers"])
    total = sum(int(r["ready"]) for r in rows)
    print("Sejarah 2027 release readiness (not just CI format QA)")
    for year, count in by_year.items():
        print(f"  Tahun {year}: {count}/36 verified FINAL_READY")
    print(f"  Overall: {total}/108 FINAL_READY")
    for gate, count in gates.most_common():
        print(f"  Unmet {gate}: {count}/108")
    output = ROOT / "output" / "sejarah_release_readiness_qa"
    output.mkdir(parents=True, exist_ok=True)
    (output / "report.json").write_text(json.dumps({
        "total": 108, "ready": total, "year_ready": by_year,
        "unmet": dict(gates), "records": rows,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (output / "review_matrix.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Year", "PdP", "ID", "READY", *CHECKS, "Unmet release gates"])
        for row in rows:
            w.writerow([row["year"], row["pdp"], row["id"], int(row["ready"]),
                        *(int(row["checks"][k]) for k in CHECKS),
                        "; ".join(row["blockers"])])
    if args.require_final_ready and total != 108:
        print("RELEASE BLOCKED: all 108 lessons require individual evidence and signoff.")
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
