"""Reversible, lesson-linked editor improvements for 14 heavy tasmi' PdP.

Source SP contains 61-106 Quran ayat in a single PdP. Replace two GENERIC
teaching fields only in a restricted editor preview with feasible individual
talaqqi/tasmi' assessment of teacher-selected passages. Never change Quran
ranges, the Year2–6 JSON catalogs, RPT, official DSKP, or live runtime.
A selected subset is NOT equivalent to mastering all ayat in source SP.
Jawi language, timing, learner differentiation and academic signoff remain HOLD.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from pi_quality_audit import ROOT, COUNT, HELD
from pi_tasmi_continuity_quality_guard import audit as tasmi_source_audit
from pi_quran_114_surah_range_audit import parse as source_verse_ranges

EXPECTED = {
    "T5-L014", "T5-L018", "T5-L106", "T5-L109",
    "T6-L054", "T6-L058", "T6-L062", "T6-L066", "T6-L070",
    "T6-L109", "T6-L113", "T6-L125", "T6-L129", "T6-L133",
}

ACTIVITY = (
    "1. ݢورو منتڤكن سورة دان جولتن اية اونتوق ستياڤ موريد برداسركن SP دان مصحف، "
    "لالو مريكود ڤيليهن سبلوم ڤدڤ دمولاکن.\n"
    "2. ݢورو ممبيمبيڠ باچاءن ڤتيقن اية سچارا تلقي دان مشافهة؛ موريد مڠيكوت "
    "باچاءن دان ممڤرباءيكي سبوتن.\n"
    "3. موريد ممڤردڠركن باچاءن تسميع سچارا برگيلير؛ راكن ممبنتو مڽمق "
    "سمنتارا ݢورو ممبتولكن مخارج دان حكوم تجويد.\n"
    "4. ݢورو مريكود جولتن اية يڠ تله دباچ دان كسالهن موريد دالم سناراي سمق، "
    "كمودين منتڤكن بيمبيڠن سوسولن اونتوق باهاݢين يڠ بلوم دكواءساءي."
)

PBD = (
    "ڤبد تسميع اينديويدو: ݢورو مڽمق باچاءن موريد برداسركن سورة دان جولتن "
    "اية يڠ تله دريکود سبلوم ڤدڤ. سناراي سمق مريكود كتڤتن مخارج، حكوم "
    "تجويد، كلنچرن، كسالهن باچاءن دان تيندقن ڤموليهن. جولتن اية سبنر "
    "واجب ديسهكن ݢورو؛ ڤنچاڤاين ڤتيقن ڤيليهن بوكن ڤڠساسهن "
    "كسلوروهن اية دالم SP."
)

def generate(root=ROOT):
    root = Path(root)
    audit = tasmi_source_audit(root)
    heavy = {entry["id"]: entry for entry in audit["high_volume_review_queue"]}
    assert set(heavy) == EXPECTED, ("Heavy source set changed", sorted(set(heavy)^EXPECTED))
    assert audit["proposed_verse_assignments"] == 0
    assert audit["teacher_ready"] == 0 and audit["release"] == "NO_GO"
    rows=[]
    for year, expected in COUNT.items():
        payload=json.loads((root/f"year{year}.json").read_text(encoding="utf-8"))
        assert payload["year"] == year and payload["ready"] is False
        assert len(payload["records"]) == expected
        for row in payload["records"]:
            if row["id"] not in heavy:
                continue
            assert not row["withheld"] and (year,row["lesson"]) not in HELD
            assert row["verified_ready"] is False
            f=row["fields"]
            assert "تسميع" in f["sk"] or "ختم القرءان" in f["sk"]
            assert all(f[k].strip() for k in ("sp","objektif","aktiviti_utama","pentaksiran"))
            assert f["aktiviti_utama"] != ACTIVITY and f["pentaksiran"] != PBD
            spans = source_verse_ranges(f["sp"])
            assert spans and sum(x["end"]-x["start"]+1 for x in spans) == heavy[row["id"]]["source_range_total_ayah"]
            source_scope = "، ".join(
                f"سورة {span['surah']} اية {span['start']}-{span['end']}"
                for span in spans
            )
            # The *existing SP ranges* are named for each individual Lesson.
            # Guru determines the exact student subset; the model assigns none.
            proposed_activity=ACTIVITY.replace(
                "برداسركن SP دان مصحف",
                f"دالم جولتن {source_scope} برداسركن SP دان مصحف"
            )
            assert source_scope in proposed_activity and proposed_activity != ACTIVITY
            rows.append({
                "id":row["id"],"year":year,"lesson":row["lesson"],
                "source_range_ayat_count":heavy[row["id"]]["source_range_total_ayah"],
                "source_surah_count":len(spans),
                "source_surah_range_label":source_scope,
                "source_surah_ranges":[{"surah":x["surah"],"start":x["start"],"end":x["end"]} for x in spans],
                "unchanged_source_sp":f["sp"],
                "unchanged_source_objective":f["objektif"],
                "original_activity":f["aktiviti_utama"],
                "original_pbd":f["pentaksiran"],
                "original_activity_sha256":hashlib.sha256(f["aktiviti_utama"].encode("utf-8")).hexdigest(),
                "original_pbd_sha256":hashlib.sha256(f["pentaksiran"].encode("utf-8")).hexdigest(),
                "proposed_activity_jawi":proposed_activity,
                "proposed_pbd_jawi":PBD,
                "teacher_selected_exact_ayah":None,
                "full_sp_completion_certified":False,
                "source_rpt_modified":False,
                "source_catalog_modified":False,
                "expert_quran_approved":False,
                "expert_jawi_approved":False,
                "teacher_timing_approved":False,
                "editor_preview_only":True,
                "can_publish":False,
                "release":"NO_GO",
            })
    assert len(rows)==14 and len({x["id"] for x in rows})==14
    assert Counter(x["year"] for x in rows)=={5:4,6:10}
    assert min(x["source_range_ayat_count"] for x in rows)>60
    assert max(x["source_range_ayat_count"] for x in rows)==106
    assert len({x["source_surah_range_label"] for x in rows})==14
    assert all(x["unchanged_source_sp"].strip() and
               not x["full_sp_completion_certified"] and
               x["teacher_selected_exact_ayah"] is None and
               not x["can_publish"] for x in rows)
    return {
        "scope":"14 high-volume Quran tasmi Year5/6 editor previews only",
        "candidate_rph_activity_and_pbd_overlays":len(rows),
        "year5":4,"year6":10,
        "source_specific_surah_range_labels":len({x["source_surah_range_label"] for x in rows}),
        "source_ayah_min":min(x["source_range_ayat_count"] for x in rows),
        "source_ayah_max":max(x["source_range_ayat_count"] for x in rows),
        "original_catalog_files_overwritten":0,
        "official_ayah_boundaries_reassigned":0,
        "teacher_exact_subranges_assigned":0,
        "claim_to_have_completed_full_sp":False,
        "jawi_or_content_approvals":0,
        "teacher_ready":0,
        "release":"NO_GO",
        "rows":rows,
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True)
    args=p.parse_args()
    result=generate()
    Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="rows"},ensure_ascii=False,indent=2))
