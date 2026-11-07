"""Strict staging check of Quran activity double-period copyedits.

This edits only a duplicated full stop after 'برتجويد' and preserves the
prior activity verbatim per Lesson. Not an academic or mushaf review.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pi_quality_audit import COUNT, HELD, ROOT

REVISION = "pi-tajwid-trailing-double-period-20261108"
BEFORE = "برتجويد.."
AFTER = "برتجويد."
EXPECTED = {2: 5, 3: 8, 4: 12, 5: 12, 6: 12}
# These ellipses are Jawi affix notation, not sentence punctuation.
AFFIX_EXAMPLE_LESSONS = ("T3-L084", "T3-L088", "T3-L092", "T3-L096",
                         "T3-L100", "T3-L104", "T3-L108", "T3-L115")


def audit(root=ROOT):
    root = Path(root)
    by_year = {}
    verified = []
    year3 = {}
    for year, total in COUNT.items():
        payload = json.loads((root / f"year{year}.json").read_text(encoding="utf-8"))
        assert len(payload["records"]) == total and payload["ready"] is False
        ids = []
        for record in payload["records"]:
            if year == 3:
                year3[record["id"]] = record
            if (year, record["lesson"]) in HELD:
                assert record["withheld"] and "staging_copyedit" not in record
                continue
            assert not record["withheld"] and record["verified_ready"] is False
            edit = record.get("staging_copyedit")
            if not edit:
                assert BEFORE not in record["fields"]["aktiviti_utama"], record["id"]
                continue
            assert edit["revision"] == REVISION
            assert edit["publication"] == "HOLD"
            assert edit["expert_content_approved"] is False
            assert edit["jawi_orthography_approved"] is False
            assert edit["native_word_pdf_verified"] is False
            assert edit["source_sk_sp_unchanged"] is True
            assert edit["activity_semantics_unchanged"] is True
            original = edit["original_activity"]
            assert original.count(BEFORE) == 1, record["id"]
            assert record["fields"]["aktiviti_utama"] == original.replace(BEFORE, AFTER), record["id"]
            assert BEFORE not in record["fields"]["aktiviti_utama"]
            ids.append(record["id"])
            verified.append({"id": record["id"], "year": year,
                             "exact_punctuation_correction_only": True,
                             "original_activity_saved": True,
                             "content_and_jawi_expert_approved": False,
                             "release": "NO_GO"})
        assert len(ids) == EXPECTED[year], (year, ids)
        by_year[str(year)] = ids
    for lesson in AFFIX_EXAMPLE_LESSONS:
        r = year3[lesson]
        assert "..." in r["fields"]["objektif"], lesson
        assert "..." in r["fields"]["set_induksi"], lesson
        assert "staging_copyedit" not in r
    assert len(verified) == 49
    return {
        "scope": "Pendidikan Islam Tahun 2-6, Quran RPH editor drafts only",
        "exact_punctuation_repairs": len(verified),
        "by_year": {year: len(rows) for year, rows in by_year.items()},
        "affix_examples_preserved": len(AFFIX_EXAMPLE_LESSONS),
        "source_sk_sp_fields_modified": 0,
        "official_quran_verses_modified": 0,
        "verified_ready": 0,
        "expert_approvals": 0,
        "academic_quality_percent": None,
        "originals_preserved_in_metadata": True,
        "publication": "HOLD",
        "release": "NO_GO",
        "rows": verified,
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    result = audit()
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                                 encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, ensure_ascii=False))
