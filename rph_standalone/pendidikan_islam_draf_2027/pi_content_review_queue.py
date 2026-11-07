"""Prioritized per-Lesson Pendidikan Islam review ledger (STAGING ONLY).

Uses existing draft source identifiers and flags. This does NOT assess or
certify the academic quality of any RPH and never edits teacher-facing content.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import json
from pathlib import Path

from pi_quality_audit import ROOT, COUNT, HELD, audit

PRIORITIES = ("P0_HELD", "P1_CRITICAL_SOURCE", "P2_PBD_OR_PAGE",
              "P3_ENRICHMENT_REVIEW", "P4_FULL_CONTENT_REVIEW")
CSV_FIELDS = (
    "id", "year", "lesson", "domain", "priority", "sp_as_source",
    "reason_codes", "editor_next_step", "content_expert_approved",
    "book_page_verified_in_this_audit", "book_activity_verified_in_this_audit",
    "can_publish", "release"
)


def build_queue(root=ROOT):
    qa = audit(root)
    rows_by_id = {r["id"]: r for r in qa["records"]}
    queue = []
    for year, expected in COUNT.items():
        source = json.loads((Path(root) / f"year{year}.json").read_text(encoding="utf-8"))
        assert len(source["records"]) == expected
        for record in source["records"]:
            row = rows_by_id[record["id"]]
            flags = row["flags"]
            held = (year, record["lesson"]) in HELD
            if held:
                assert record["withheld"] and "fields" not in record
                priority = "P0_HELD"
                action = "Jangan jana atau terbit RPH; perlu lengkapkan dan sahkan sumber asal."
                sp = None
            elif "SUMBER_KRITIKAL_BELUM_LENGKAP" in flags:
                priority = "P1_CRITICAL_SOURCE"
                action = "Dapatkan matan/julat ayat asal yang lengkap; semak pakar sebelum isi aktiviti."
                sp = record["fields"]["sp"]
            elif ("PBD_TIDAK_KHUSUS_KEPADA_SP" in flags or
                  "PBD_SP_SASARAN_BELUM_DISAH_PAKAR" in flags or
                  "RUJUKAN_HALAMAN_BELUM_DISAHKAN" in flags):
                priority = "P2_PBD_OR_PAGE"
                tasks = []
                if "PBD_TIDAK_KHUSUS_KEPADA_SP" in flags:
                    tasks.append("Semak PBD individu terhadap kata kerja dan hasil SP sebenar")
                if "PBD_SP_SASARAN_BELUM_DISAH_PAKAR" in flags:
                    tasks.append("Semak ayat PBD draf khusus: bukti aktiviti/SP, ejaan Jawi dan rubrik guru")
                if "RUJUKAN_HALAMAN_BELUM_DISAHKAN" in flags:
                    tasks.append("Sahkan halaman Buku Teks pada naskhah asal")
                if "HALAMAN_BUKU_T2_MELEBIHI_MUKA_TERAKHIR" in flags:
                    tasks.append("Julat lama 133-140 melepasi halaman bercetak terakhir 138; semak cadangan 133-138 dengan SP")
                action = "; ".join(tasks) + "."
                sp = record["fields"]["sp"]
            elif "PENAMBAHAN_PDP_BELUM_SAH_PAKAR" in flags:
                priority = "P3_ENRICHMENT_REVIEW"
                action = "Semak ketepatan pengayaan, Jawi, objektif dan PBD terhadap DSKP/buku/mushaf."
                sp = record["fields"]["sp"]
            else:
                priority = "P4_FULL_CONTENT_REVIEW"
                action = "Audit SK/SP, objektif, aktiviti, PBD, Jawi serta Word/PDF A4."
                sp = record["fields"]["sp"]
            queue.append({
                "id": record["id"],
                "year": year,
                "lesson": record["lesson"],
                "domain": row["domain"],
                "priority": priority,
                "sp_as_source": sp,
                "reason_codes": "|".join(flags),
                "editor_next_step": action,
                "content_expert_approved": False,
                "book_page_verified_in_this_audit": False,
                "book_activity_verified_in_this_audit": False,
                "can_publish": False,
                "release": "NO_GO",
            })
    assert len(queue) == 696 and len({x["id"] for x in queue}) == 696
    assert all(x["priority"] in PRIORITIES and not x["can_publish"] for x in queue)
    counts = Counter(x["priority"] for x in queue)
    return {
        "scope": "Pendidikan Islam Tahun 2-6 sahaja; Tahun 1 belum dalam katalog ini",
        "status": "STAGING_EDITOR_REVIEW_ONLY",
        "quality_score_percent": None,
        "quality_80_certified": False,
        "generic_pbd_records": qa["generic_pbd_count"],
        "pbd_refinements_pending_expert_review": qa["refined_pbd_review_count"],
        "unverified_old_page_note_records": qa["flags"].get("RUJUKAN_HALAMAN_BELUM_DISAHKAN", 0),
        "textbook_end_page_overruns": qa["textbook_page_range_overrun_count"],
        "by_priority": {p: counts.get(p, 0) for p in PRIORITIES},
        "total": len(queue),
        "can_publish": False,
        "release": "NO_GO",
        "rows": queue,
    }


def write_csv(path, queue):
    with Path(path).open("w", encoding="utf-8-sig", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(queue["rows"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", required=True)
    parser.add_argument("--csv", required=True)
    args = parser.parse_args()
    result = build_queue()
    Path(args.json).write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_csv(args.csv, result)
    print(json.dumps({k: v for k, v in result.items() if k != "rows"},
                     ensure_ascii=False, indent=2))
