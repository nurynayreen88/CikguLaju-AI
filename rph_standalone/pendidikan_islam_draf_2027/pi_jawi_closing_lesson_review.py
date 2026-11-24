"""690-row per-Lesson Jawi closing review ledger, preserving original SK/SP.

Every candidate remains UNAPPROVED. Domain and source SP are copied from the
staging source (not claimed to be official DSKP verified). Six fully withheld
records are deliberately excluded, three incomplete critical sources are
labelled to prohibit teacher previews. Nothing is written to teacher RPHs.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

from pi_quality_audit import ROOT, COUNT, audit
from pi_closing_jawi_candidates_complete import generate as candidate_proposals

CSV_FIELDS = (
    "id", "year", "lesson", "domain", "source_rumi_closing", "candidate_jawi_closing",
    "source_original_sha256", "candidate_group_id", "shared_group_count",
    "source_sk_not_dskp_approved", "source_sp_not_dskp_approved",
    "critical_source_hold", "pbd_pending_expert", "old_textbook_page_pending",
    "editor_review_priority", "jawi_reviewer", "content_reviewer", "source_reviewer",
    "jawi_spelling_verified", "content_matches_sp_verified",
    "original_dskp_source_verified", "word_pdf_native_verified",
    "can_publish", "release"
)


def build(root=ROOT):
    root = Path(root)
    qa = audit(root)
    flags_by_id = {x["id"]: x for x in qa["records"]}
    candidates = candidate_proposals(root)
    assert candidates["candidate_groups"] == 78
    assert candidates["candidate_covered_lesson_occurrences"] == 690
    by_lesson = {}
    for group in candidates["records"]:
        for lesson_id in group["lesson_ids"].split("|"):
            if lesson_id in by_lesson:
                raise ValueError("Duplicate lesson in Jawi group: " + lesson_id)
            by_lesson[lesson_id] = group
    assert len(by_lesson) == 690
    rows = []
    for year, expected in COUNT.items():
        data = json.loads((root / f"year{year}.json").read_text(encoding="utf-8"))
        assert data["year"] == year and data["ready"] is False and len(data["records"]) == expected
        for record in data["records"]:
            if record["withheld"]:
                assert "fields" not in record
                assert record["id"] not in by_lesson
                continue
            lesson_id = record["id"]
            group = by_lesson[lesson_id]
            text = record["fields"]["penutup"]
            source_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            if text != group["original_closing_rumi"] or source_hash != group["original_text_sha256"]:
                raise ValueError("Changed source Rumi without rechecking Jawi: " + lesson_id)
            f = flags_by_id[lesson_id]["flags"]
            critical = "SUMBER_KRITIKAL_BELUM_LENGKAP" in f
            priority = (
                "P0_SOURCE_HOLD" if critical
                else "P1_PBD_AND_PAGE" if (
                    "PBD_SP_SASARAN_BELUM_DISAH_PAKAR" in f and
                    "RUJUKAN_HALAMAN_BELUM_DISAHKAN" in f
                )
                else "P2_PBD_OR_PAGE" if (
                    "PBD_SP_SASARAN_BELUM_DISAH_PAKAR" in f or
                    "RUJUKAN_HALAMAN_BELUM_DISAHKAN" in f
                )
                else "P3_JAWI_CONTENT_EDITOR"
            )
            rows.append({
                "id": lesson_id,
                "year": year,
                "lesson": record["lesson"],
                "domain": flags_by_id[lesson_id]["domain"],
                "source_rumi_closing": text,
                "candidate_jawi_closing": group["candidate_jawi_text"],
                "source_original_sha256": source_hash,
                "candidate_group_id": group["group_id"],
                "shared_group_count": group["lesson_count"],
                "source_sk_not_dskp_approved": record["fields"]["sk"],
                "source_sp_not_dskp_approved": record["fields"]["sp"],
                "critical_source_hold": critical,
                "pbd_pending_expert": "PBD_SP_SASARAN_BELUM_DISAH_PAKAR" in f,
                "old_textbook_page_pending": "RUJUKAN_HALAMAN_BELUM_DISAHKAN" in f,
                "editor_review_priority": priority,
                "jawi_reviewer": None,
                "content_reviewer": None,
                "source_reviewer": None,
                "jawi_spelling_verified": False,
                "content_matches_sp_verified": False,
                "original_dskp_source_verified": False,
                "word_pdf_native_verified": False,
                "can_publish": False,
                "release": "NO_GO",
            })
    assert len(rows) == 690 and len({x["id"] for x in rows}) == 690
    assert sum(x["critical_source_hold"] for x in rows) == 3
    assert sum(x["pbd_pending_expert"] for x in rows) == 43
    assert sum(x["old_textbook_page_pending"] for x in rows) == 77
    assert all(not x["can_publish"] and x["release"] == "NO_GO" for x in rows)
    counts = Counter(x["editor_review_priority"] for x in rows)
    return {
        "scope": "Pendidikan Islam Tahun 2–6, Jawi Penutup review only",
        "all_catalog_records": 696,
        "fully_held_without_source": 6,
        "candidate_lessons": 690,
        "candidate_unique_groups": 78,
        "ready_lesson_count": 0,
        "jawi_approved": 0,
        "academic_quality_percent": None,
        "can_publish": False,
        "release": "NO_GO",
        "by_priority": dict(sorted(counts.items())),
        "rows": rows,
    }


def write(json_path, csv_path, root=ROOT):
    result = build(root)
    Path(json_path).write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    with Path(csv_path).open("w", encoding="utf-8-sig", newline="") as target:
        w = csv.DictWriter(target, fieldnames=CSV_FIELDS)
        w.writeheader()
        w.writerows(result["rows"])
    print(json.dumps({k: v for k, v in result.items() if k != "rows"},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--json", required=True)
    p.add_argument("--csv", required=True)
    args=p.parse_args()
    write(args.json, args.csv)
