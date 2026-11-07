"""Non-destructive EDITOR preview for Pendidikan Islam Year 2-6 RPH.

The original RPH fields, including unresolved textbook page claims, are never
edited. This projection stores the full source and all 523 secondary material
lines under editor provenance, NOT in the teacher-materials preview field.

This is NOT a runtime component, a verified RPH, or authorization to publish.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from pi_quality_audit import COUNT, HELD, REQUIRED, ROOT

# A strict whitelist of *existing* audit/source-review prefixes found after
# the primary material line. Fail closed if source formats change.
EDITORIAL_PREFIXES = (
    "Rujukan bacaan/tasmi':",
    "Mushaf al-Quran:",
    "Mushaf al-Quran (tasmi'/khatam)",
    "Unit ",
    "Buku Teks PI Tahun 2:",
    "PEMBETULAN DIAUDIT:",
    "Pemetaan buku teks",
    "Rekod padanan SP buku teks lama",
    "SEMAKAN KURIKULUM:",
    "SEMAKAN DSKP DIPERLUKAN:",
)


def preview_catalog(root=ROOT):
    rows = []
    exceptions = []
    for year, expected in COUNT.items():
        payload=json.loads((Path(root)/f"year{year}.json").read_text(encoding="utf-8"))
        assert payload["year"]==year and payload["ready"] is False
        assert len(payload["records"])==expected
        for record in payload["records"]:
            if (year, record["lesson"]) in HELD:
                assert record["withheld"] and "fields" not in record
                continue
            assert not record["withheld"] and record["verified_ready"] is False
            src=record["fields"]
            assert all(src.get(k) for k in REQUIRED)
            parts=[p.strip() for p in src["bahan"].splitlines() if p.strip()]
            assert parts and parts[0]
            extra=parts[1:]
            unknown=[p for p in extra if not p.startswith(EDITORIAL_PREFIXES)]
            if unknown:
                exceptions.append({"id":record["id"],"unrecognized":unknown})
                continue

            # Do not edit SP, SK, objectives, pedagogy, PBD or source JSON.
            shown={k:src[k] for k in REQUIRED}
            shown["bahan"]=parts[0]
            source_sha=hashlib.sha256(
                src["bahan"].encode("utf-8")
            ).hexdigest()
            rows.append({
                "id": record["id"],
                "year": year,
                "source_state": record["state"],
                "source_material_sha256": source_sha,
                "display_fields": shown,
                "editor_only_material_notes": extra,
                "hidden_note_count": len(extra),
                "quality_certified": False,
                "preview_only": True,
                "ready": False,
                "can_publish": False,
                "book_activity_page_verified": False,
            })

    assert not exceptions, f"Unrecognized extra material text: {exceptions[:5]}"
    assert len(rows)==690 and len({r["id"] for r in rows})==690
    cnt=Counter(r["year"] for r in rows)
    assert cnt=={2:111,3:147,4:151,5:143,6:138}, cnt
    num=sum(r["hidden_note_count"] for r in rows)
    assert num==523, num
    assert all(r["display_fields"]["bahan"].strip() for r in rows)
    assert all(r["quality_certified"] is False and r["ready"] is False and
               r["can_publish"] is False for r in rows)
    return {
        "subject": "Pendidikan Islam",
        "projection": "ISOLATED_EDITOR_PREVIEW_ONLY",
        "all_records": 696,
        "active_drafts": 690,
        "held_excluded": 6,
        "source_bahan_secondary_lines_preserved": num,
        "hidden_editor_notes_total": num,
        "by_year": dict(sorted(cnt.items())),
        "unrecognized_material_line_count": len(exceptions),
        "academic_quality_percent": None,
        "release": "NO_GO",
        "rows": rows,
    }


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    args=ap.parse_args()
    r=preview_catalog()
    Path(args.output).write_text(
        json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
    )
    print(json.dumps({k:v for k,v in r.items() if k!="rows"},
                     ensure_ascii=False,indent=2))
