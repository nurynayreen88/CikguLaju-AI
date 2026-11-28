"""Audit internal Year 5-6 RBT textbook SP-page references, no promotion to READY.

Requires no network/book PDF. Checks that 64 RPH lessons, 64 RPT rows and
release manifest all reference the same editorial textbook page ranges.
This CANNOT independently verify actual publisher pages or textbook activities.
"""
from __future__ import annotations

import json
from pathlib import Path

from rpt_2027.rbt.pdf_runtime import source_rows

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "audits/rbt_y5_y6_textbook_page_evidence_20261106.json"
MANIFEST = ROOT / "audits/rbt_t4_t6_manual_release_approval_manifest_20261106.json"
OUTPUT = ROOT / "staging/rpt_2027_seragam_2026/audit_rbt_y5_y6_64_pdp_page_consistency.json"

def run_audit():
    ledger = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if ledger.get("status") != "SUMBER_TEKS_DIPADANKAN_BELUM_SAH_VISUAL" or ledger.get("approval_count") != 0:
        raise ValueError("RBT Y5–6 textbook source evidence status changed")
    if (manifest.get("status") != "STAGING_DRAF_FAIL_CLOSED" or
        manifest.get("item_count") != 96 or
        manifest.get("approvals_granted") != 0 or
        manifest.get("release_ready_count") != 0):
        raise ValueError("RBT source release manifest changed")
    evidence = {r["id"]: r for r in manifest["individual_review"]}
    if len(evidence) != 96:
        raise ValueError("Missing or duplicate RBT release manifest entries")
    results = []
    for year, expected_codes in ((5, 34), (6, 23)):
        source_index = ledger[f"year{year}"]["printed_page_index"]
        if len(source_index) != expected_codes:
            raise ValueError(f"RBT Y{year}: source SP index incomplete")
        doc = json.loads((ROOT / f"rph_standalone/rbt/tahun_{year}/RPH_RBT_T{year}_2027_DRAF.json")
                         .read_text(encoding="utf-8"))
        rows = source_rows(year)
        lessons = doc["pelajaran"]
        if len(rows) != 32 or len(lessons) != 32 or doc.get("status") != "DRAF_STAGING":
            raise ValueError(f"RBT Y{year}: missing/mismatched RPT/RPH lessons")
        for n, (row, lesson) in enumerate(zip(rows, lessons), 1):
            identity = f"RBT-T{year}-PDP-{n:03d}"
            m = evidence.get(identity)
            if not m or m["tahun"] != year or m["pdp"] != n:
                raise ValueError("RBT manual review manifest not aligned")
            if (row["ID"] != identity or lesson["id"] != identity or
                int(row["PdP"]) != n or
                lesson["sp_codes"] != row["SP"].split(" / ") or
                lesson["sk"] != row["SK"].split(" / ") or
                lesson["unit_label"] != row["Unit"] or
                m["sp"] != lesson["sp_codes"] or
                m["sk"] != lesson["sk"]):
                raise ValueError(f"RBT Y{year} PdP{n:03d}: identity/SK/SP mismatch")
            original = lesson["rujukan_buku_teks"]
            if (original.get("status") != "BELUM_SAH_HALAMAN" or
                original.get("muka_surat") is not None or
                original.get("aktiviti_buku_teks") is not None or
                original.get("halaman_adalah_calon_sahaja") is not True or
                original.get("aktiviti_visual_disahkan") is not False or
                lesson["review"]["release_ready"] is not False or
                lesson["review"]["halaman_buku_disahkan"] is not False or
                m.get("release_ready") is not False or
                m.get("aktiviti_dalam_buku_diluluskan") is not False or
                m.get("semakan_individu_guru") is not False):
                raise ValueError(f"RBT Y{year} PdP{n:03d}: forbidden approval promotion")
            expected = [
                {"sp": code, "muka_surat_bercetak_calon": source_index[code]}
                for code in lesson["sp_codes"]
            ]
            if original.get("calon_muka_surat_mengikut_sp") != expected:
                raise ValueError(f"RBT Y{year} PdP{n:03d}: RPH page range differs from source")
            boundaries = sorted({int(page) for item in expected
                                 for page in item["muka_surat_bercetak_calon"]})
            got = original.get("calon_muka_surat_teks_digital")
            if sorted(set(got or [])) != boundaries:
                raise ValueError(f"RBT Y{year} PdP{n:03d}: RPH page-boundary list differs")
            if sorted(set(m.get("buku_teks_hal_bercetak_calon") or [])) != boundaries:
                raise ValueError(f"RBT Y{year} PdP{n:03d}: manual review page list differs")
            ranges = "; ".join(
                f"{code} ({'hlm. ' if year==6 else ''}{source_index[code][0]}–{source_index[code][1]})"
                for code in lesson["sp_codes"]
            )
            suffix = "BELUM SAH VISUAL" if year == 5 else "CALON BUKAN VISUAL"
            if row.get("Rujukan Buku Teks m/s") != f"{ranges} — {suffix}":
                raise ValueError(f"RBT Y{year} PdP{n:03d}: CSV page display differs")
            if row["Kumpulan A tarikh"] or row["Kumpulan B tarikh"] or row["Status"] != "DRAF":
                raise ValueError(f"RBT Y{year} PdP{n:03d}: unfounded calendar/release value")
            results.append({
                "year": year, "pdp": n, "id": identity,
                "sp_codes": list(lesson["sp_codes"]),
                "calon_halaman_bercetak_mengikut_sp": expected,
                "status": "RPH_RPT_MANIFEST_INTERNAL_CONSISTENCY_PASS",
                "source_book_page_verification": "PENDING_INDEPENDENT",
                "activities_visual_verified": False,
                "teacher_approved": False
            })
    if len(results) != 64:
        raise ValueError("RBT page audit incomplete")
    return {
        "audit_date": "2026-11-07",
        "status": "STAGING_INTERNAL_CONSISTENCY_ONLY",
        "source": str(EVIDENCE.relative_to(ROOT)),
        "book_source_urls": ledger["urls"],
        "pdps_verified_internal_only": len(results),
        "years": {"5": 32, "6": 32},
        "unique_sp_by_year": {"5": 34, "6": 23},
        "independent_book_page_checks_completed": 0,
        "teacher_approvals": 0,
        "release_ready_count": 0,
        "records": results,
    }


def main():
    audit = run_audit()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("RBT Y5-Y6: 64/64 RPH–RPT–manifest SP/page-range mappings PASS (internal only).")
    print("Independent book-page verification: 0; release status: BLOCKED.")


if __name__ == "__main__":
    main()
